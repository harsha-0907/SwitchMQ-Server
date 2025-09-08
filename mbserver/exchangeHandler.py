
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
        print("Removing Message")
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











