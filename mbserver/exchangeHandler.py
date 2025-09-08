
# This is the exchange handler code
# This will be a function


class Message:
    def __init__(self, messageId: str = "", head=False):
        self.messageId = 0 if head else messageId
        self.next = None
