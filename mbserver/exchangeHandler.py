
# This is the exchange handler code
# This will be a function


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




