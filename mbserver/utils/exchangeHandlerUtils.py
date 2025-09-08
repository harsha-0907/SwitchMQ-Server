
from uuid import uuid4
import random
import base64


def fetchMessageId(limit=1000):
    primaryId = random.randrange(limit)
    secId = convertToBase64(uuid4().hex[:14])
    return str(primaryId)+'.'+secId

def convertToBase64(secId):  # 9 bytes = 72 bits
    raw_bytes = bytes.fromhex(secId)  # Convert hex to bytes
    return base64.urlsafe_b64encode(raw_bytes).rstrip(b"=").decode("utf-8")