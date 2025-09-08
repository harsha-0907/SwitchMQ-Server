
import os, json, redis, socket, asyncio, random, dotenv
from threading import Lock
from multiprocessing import Manager
from mbexceptions import *
from utils.exchangeHandlerUtils import fetchMessageId

class Message:
    def __init__(self, messageId: str = "", head=False):
        self.messageId = 0 if head else messageId
        self.next = None

class Queue:
    def __init__(self, queueName):
        self.queueName = queueName
        self.count = 0
        self.head = Message(head=True)
        self.tail = None
    
    def addMessage(self, messageId):
        newMessage = Message(messageId)
        if self.tail is None:
            self.tail = newMessage
            self.head.next = self.tail
        
        else:
            self.tail.next = newMessage
            self.tail = newMessage 
        
    def popMessage(self):
        if self.head.next is None:
            raise NoMessageException()
        
        message = self.head.next
        self.head.next = self.head.next.next
        if self.head.next is None:
            self.tail = None

        return message.messageId


class Exchange:
    def __init__(self, hostName: str, exchangeName: str,
        port: int, queues: list = None, priority: int = 1,
        bind_local: bool = True, maxSocketConnections: int = 10,
        timeOut: int = 5, maxMessages: int = 10000
    ):
        self.hostName: str = hostName
        self.ipAddress: str = "127.0.0.1" if bind_local else "0.0.0.0"
        self.priority: int = priority
        self.port: int = port
        self.exchangeName: str = exchangeName
        self.queues = dict()
        self.terminateExchange: bool = False
        self.maxSocketConnections = maxSocketConnections
        self.timeOut = timeOut

        self.messages = {}  # {primaryId: {secId: (message, count)}}
        self.locks = {}     # {primaryId: asyncio.Lock()}

        # Initialize queues if provided
        if queues:
            for queue in queues:
                self.addQueue(queue)

        for i in range(1000):
            self.messages[i] = {}
            self.locks[i] = asyncio.Lock()

        self.totalMessages = 0
        self.maxMessages = maxMessages


        # self.handleSocket()

    def addQueue(self, queueName: str):
        if queueName in self.queues:
            # Update the status of the request in redis to False
            return False
        
        self.queues[queueName] = Queue(queueName)
    
    async def handleRedis(self):
        """ Updates the Redis with database Info"""
        # TO-DO - Add redis handling
        pass


    async def saveMessage(self, message: str, messageId: str, numberOfCopies):
        primaryId, secId = messageId.split("."); primaryId = int(primaryId)
        async with self.locks[primaryId]:
            self.messages[primaryId][secId] = (message, numberOfCopies)
    
    async def fetchMessage(self, messageId: str):
        primaryId, secId = messageId.split("."); primaryId = int(primaryId)
        async with self.locks[primaryId]:
            message = self.messages.get(primaryId, {}).get(secId, None)
            messageBody, messageCount = message

            if messageCount == 1:
                del(self.messages[primaryId][secId])
            return messageBody

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, timeOut: int = 5):
        addr = writer.get_extra_info("peername")

        try:
            # Wait for message with timeout
            data = await asyncio.wait_for(reader.read(6000), timeout=timeOut)
            if not data:
                return

            message = data.decode("utf-8")
            try:
                response = await self.processMessage(message)

            except Exception as _e:
                response = str(ReturnableException(_e))

            writer.write(response.encode())
            await writer.drain()

        except asyncio.TimeoutError:
            pass

        except Exception as e:
            print("Exception ", e)
            pass

        finally:
            writer.close()
            await writer.wait_closed()
    
    # Socket Handler
    async def handleSocket(self):
        server = await asyncio.start_server(
            self.handle_client,
            self.ipAddress,
            self.port,
            backlog=self.maxSocketConnections
        )

        print(f"Server started on {self.ipAddress}:{self.port}")

        async with server:
            while not self.terminateExchange:
                await asyncio.sleep(0.1)


    async def processMessage(self, message: str):
        message = json.loads(message)
        action = message.get("action", None)
        queueNames = message.get("queues")
        messageBody = message.get("message", "")

        if action == "GET":
            queueName = queueNames[0]
            # TO-DO - Fetch the message and return it
            messageId = self.queues[queueName].popMessage()
            messageBody = await self.fetchMessage(messageId)
            
            if messageBody is not None:
                return json.dumps({
                    "statusCode": 200,
                    "error": False,
                    "message": messageBody,
                    "stats": {
                        "count": self.totalMessages
                    }
                })

            else:
                raise NoMessageException()
        
        elif action == "POST":
            # All exceptions will be handled at the socket
            if self.totalMessages >= self.maxMessages:
                raise ExchangeOverflowError()
            
            messageId = fetchMessageId()
            await self.saveMessage(message=message, messageId=messageId, numberOfCopies=len(queueNames))
            self.totalMessages += 1

            for queueName in queueNames:
                try:
                    resp = self.queues[queueName].addMessage(messageId)
                
                except Exception as _e:
                    # Remove all those messages
                    pass

            return json.dumps({
                "statusCode": 200,
                "error": False,
                "message": "Done",
                "stats": {
                    "count": self.totalMessages
                }
            })

            raise UnknownException("Unknown Exception")

        else:
            raise UnknownException("Action: Unauthorized Action")











