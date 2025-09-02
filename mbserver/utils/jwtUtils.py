
import os
import jwt
import time
from dotenv import load_dotenv
load_dotenv()

SECRET_JWT_TOKEN = os.getenv("JWT_ACCESS_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
def fetchTime():
    return int(time.time())

def encodeJWT(decodedData: dict) -> str:
    nowTime = int(time.time())
    payload = {
        "data": decodedData,
        "timeStamp": fetchTime()
    }
    encodedJwt = jwt.encode(payload, SECRET_JWT_TOKEN, algorithm=ALGORITHM)
    return encodedJwt

def decodeJWT(encodedToken: str) -> dict | None:
    try:
        decodedData = jwt.decode(encodedToken, SECRET_JWT_TOKEN, algorithms=[ALGORITHM])
        return decodedData["data"]

    except jwt.InvalidTokenError:
        print("Invalid JWT Token")
        return None
        
    except KeyError as ke:
        print("Invalid Structure")
        return None
    
