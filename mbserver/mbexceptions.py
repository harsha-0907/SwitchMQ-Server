import json

class ReturnableException:
    def __init__(self, exceptionObject):
        self.exception = exceptionObject

    def __str__(self):
        return json.dumps(
            {
                "statusCode": getattr(self.exception, 'statusCode', 500),
                "error": True,
                "message": '\n'.join(str(arg) for arg in self.exception.args)
            }
        )

class MessageException(Exception):
    def __init__(self, message="Message size exceeded limit"):
        super().__init__(message)
        self.statusCode = 601

class ExchangeOverflowError(Exception):
    def __init__(self, message="Exchange is full: cannot add more items."):
        super().__init__(message)
        self.statusCode = 602

class UnAuthorizedAccess(Exception):
    def __init__(self, message="Access Denied to the Exchange"):
        super().__init__(message)
        self.statusCode = 605

class ExchangeNotFoundError(Exception):
    def __init__(self, message="Exchange not found"):
        super().__init__(message)
        self.statusCode = 603

class UnknownException(Exception):
    def __init__(self, message="Unknown Exception", statusCode=600):
        super().__init__(message)
        self.statusCode = statusCode

class NoMessageException(Exception):
    def __init__(self, message="The Queue/Exchange is empty"):
        super().__init__(message)
        self.statusCode = 604

class MemoryException(Exception):
    def __init__(self, message="Memory limit exceeded"):
        super().__init__(message)
        self.statusCode = 606

class JSONError(Exception):
    def __init__(self, message="Error while encoding/decoding message"):
        super().__init__(message)
        self.statusCode = 607
