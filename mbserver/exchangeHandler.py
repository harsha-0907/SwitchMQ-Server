
import os, json, socket, asyncio, random, dotenv, redis
from threading import Lock
from multiprocessing import Manager
from mbexceptions import *
from utils.exchangeHandlerUtils import fetchMessageId
from apscheduler.schedulers.background import BackgroundScheduler

dotenv.load_dotenv()

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
    
    def copy(self):
        messageIds = []; msg = self.head.next
        if msg is None:
            return messageIds
        
        while msg:
            messageIds.append(msg.messageId)
            msg = msg.next
        
        return messageIds
        

class Exchange:
    def __init__(self, hostName: str, exchangeName: str,
        port: int, terminateSwitch, queues: list = None, priority: int = 1,
        bind_local: bool = True, maxSocketConnections: int = 10,
        timeOut: int = 5, maxMessages: int = 10000, saveFrequency: int = 60,
        redisUpdateFrequency: int = 3, relativeMessageStoreDirectory: str = ".messageCache"
    ):
        self.hostName: str = hostName
        self.ipAddress: str = "127.0.0.1" if bind_local else "0.0.0.0"
        self.priority: int = priority
        self.port: int = port
        self.exchangeName: str = exchangeName
        self.__queues = dict()
        self.__terminateExchange = terminateSwitch
        self.maxSocketConnections = maxSocketConnections
        self.timeOut = timeOut
        self.redisUpdateFrequency = redisUpdateFrequency
        self.saveFrequency = saveFrequency
        if not os.path.exists(relativeMessageStoreDirectory):
            os.makedirs(relativeMessageStoreDirectory)
        
        self.relativeMessageStorePath = os.path.join(relativeMessageStoreDirectory,self.exchangeName+'.store')

        self.totalMessages = 0
        self.maxMessages = maxMessages
        self.__messages = {}  # {primaryId: {secId: (message, count)}}
        self.__locks = {}     # {primaryId: asyncio.Lock()}

        # Initializing components
        self.initializeQueuesAndExchange(queues)
        self.initializeScheduler()
        self.initializeRedisScheduler()
        self.initializePersistence()

    def persistExchange(self):
        """ Saves the messages and queue order in a json file """
        logFileObject = open(self.relativeMessageStorePath, 'w')   # Replace this with aiofiles 
        exchangeData = dict()
        exchangeData["queues"] = dict(); exchangeData["messages"] = dict()
        
        for queueName, queueObj in self.__queues.items():
            messages = queueObj.copy()
            exchangeData["queues"][queueName] = messages

        for partitionId, partitionObj in self.__messages.items():
            if len(partitionObj) == 0:
                continue
            exchangeData["messages"][partitionId] = partitionObj
        
        json.dump(exchangeData, logFileObject, indent=4)
        logFileObject.close()

    def initializePersistence(self):
        """ Initializes background scheduler to copy data every interval"""
        self.scheduler.add_job(self.persistExchange, 'interval', seconds=self.saveFrequency)

    def initializeQueuesAndExchange(self, queues):
        if queues:
            for queue in queues:
                self.addQueue(queue)

        for i in range(1000):
            self.__messages[i] = {}
            self.__locks[i] = asyncio.Lock()

    def initializeScheduler(self):
        """ Initialize background scheduler & filepath for storage"""
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def addQueue(self, queueName: str):
        if queueName in self.__queues:
            return False
        
        self.__queues[queueName] = Queue(queueName)
    
    async def deleteQueue(self ,queueName):
        # Deletes all the messages in the queue
        queue = self.__queues[queueName]
        while True:
            try:
                messageId = queue.popMessage()
                await self.fetchMessage(messageId)

            except NoMessageException as _e:
                break

        return True

    def initializeRedisScheduler(self):
        self.__redisCreds = {
            "host": os.getenv("REDIS_HOST"),
            "port": int(os.getenv("REDIS_PORT")),
            "username": os.getenv("REDIS_USERNAME"),
            "password": os.getenv("REDIS_PASSWORD")
        }
        
        self.__redisClient = redis.Redis(
            host=self.__redisCreds["host"],
            port=self.__redisCreds["port"],
            decode_responses=True,
            username=self.__redisCreds["username"],
            password=self.__redisCreds["password"]
        )
        # Adding the job to scheduler
        self.scheduler.add_job(self.updateRedis, 'interval', seconds=self.redisUpdateFrequency)
        
    def updateRedis(self):
        """ Updates the Redis with database Info"""
        # TO-DO - Add redis handling
        if not self.__redisClient.ping():
            raise ExternalSystemArchitecture("Unable to connect with Redis")

        exchangeValues = dict()
        _exchangeValues = vars(self)
        for _exchangeKey, _exchangeValue in _exchangeValues.items():
            if _exchangeKey.startswith("_"):
              continue

            exchangeValues[_exchangeKey] = str(_exchangeValue)
        
        queues = ','.join(list(self.__queues.keys()))
        exchangeValues["queues"] = queues
        print("Updating Redis DB")
        self.__redisClient.hset(self.hostName+'.'+self.exchangeName, mapping=exchangeValues)

    async def saveMessage(self, message: str, messageId: str, numberOfCopies):
        primaryId, secId = messageId.split("."); primaryId = int(primaryId)
        async with self.__locks[primaryId]:
            self.__messages[primaryId][secId] = (message, numberOfCopies)
    
    async def fetchMessage(self, messageId: str):
        primaryId, secId = messageId.split("."); primaryId = int(primaryId)
        async with self.__locks[primaryId]:
            message = self.__messages.get(primaryId, {}).get(secId, None)
            messageBody, messageCount = message

            if messageCount == 1:
                del(self.__messages[primaryId][secId])
                self.totalMessages -= 1
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
            while not self.__terminateExchange.is_set():
                # print(self.__terminateExchange)
                await asyncio.sleep(0.01) # 0.01 sec is found to be optimal

        print("Exchange Stopped")

    async def processMessage(self, message: str):
        message = json.loads(message)
        action = message.get("action", None)
        queueNames = message.get("queues")
        messageBody = message.get("message", "")

        if action == "GET":
            queueName = queueNames[0]
            # TO-DO - Fetch the message and return it
            messageId = self.__queues[queueName].popMessage()
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
            await self.saveMessage(message=messageBody, messageId=messageId, numberOfCopies=len(queueNames))
            self.totalMessages += 1

            for queueName in queueNames:
                try:
                    resp = self.__queues[queueName].addMessage(messageId)
                
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

        elif action == "UPDATE-ADD":
            queueName = queueNames[0]
            self.addQueue(queueName)
                
            return json.dumps({
                "statusCode": 200,
                "error": False,
                "message": "Queue Added",
                "stats": {
                    "count": self.totalMessages
                }
            })
        
        elif action == "UPDATE-REMOVE":
            queueName = queueNames[0]
            await self.deleteQueue(queueName)
            print(self.__queues)
            return json.dumps({
                "statusCode": 200,
                "error": False,
                "message": "Queue Removed",
                "stats": {
                    "count": self.totalMessages
                }
            })
            
        else:
            raise UnknownException("Action: Unauthorized Action")

