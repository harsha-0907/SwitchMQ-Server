
# Server responsible for websocket & MB
import os, json, socket, asyncio
from dotenv import load_dotenv
from mbexceptions import *
from utils.jwtUtils import decodeJWT
from utils.responsePages import UN_AUTH_401_RESP
from fastapi import (FastAPI, WebSocket, Header, HTTPException, Depends, WebSocketException, status, WebSocketDisconnect)

load_dotenv()
users = dict()
connections = dict()
dbInfo = {
    "": {
        "stats": {
            "maxSize": 100000, # Mandatory
            "count": 1,    # Mandatory
            "host": "127.0.0.1",# Mandatory
            "port": 48001   # Mandatory
        },
        "": 1
    }
}
exchanges = [""]    # Update this along with dbInfo
app = FastAPI()

NUMBER_OF_MB_WORKERS = int(os.getenv("MB_WORKERS"))
MAX_MESSAGE_SIZE = int(os.getenv("MAX_MESSAGE_SIZE"))

def isAuthenticated(websocket: WebSocket):
    authorization = websocket.headers.get("authorization", None)
    if authorization is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    userData = decodeJWT(authorization)
    if not userData:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    
    return userData

def isValidMessage(message):
    """ Performs any filter actions that need to be performed"""
    if len(message) > MAX_MESSAGE_SIZE:
        return False
    
    return True

def processMessage(message):
    """ Process the message to escape any characters"""
    if message[0] == "~":
        return '~' + message

    if message == "GET":
        return '~' + message

    return message

def processExchange(host, port, message) -> str:
    """ Communicates with the exchange-via socket"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.sendall(bytes(message, "utf-8"))
        resp = sock.recv(1024).decode("utf-8")
    
    except Exception as _e:
        resp = ReturnableExceptio(_e)
    
    finally:
        return resp

async def executeCommand(rawMessage:str, userData, inputData: dict)-> str:
    """ Executes the commands & returns the response"""
    reqAction = inputData.get("action"); reqExchange = inputData.get("exchange", ""); reqQueues = inputData.get("queues", [])
    userAuthorizedExchanges = userData.get("access", {}).get("exchange", [])
    
    if reqExchange not in userAuthorizedExchanges:
        print("Un-Authorized")
        raise UnAuthorizedAccess()
    
    exchangeInfo = dbInfo.get(reqExchange, None)

    if exchangeInfo is None:
        raise ExchangeNotFoundError()
    
    exchangeStats = exchangeInfo.get("stats")
    exchangeHost, exchangePort = exchangeStats.get("host"), exchangeStats.get("port")

    if reqAction == "GET":
        resp = json.loads(await asyncio.to_thread(processExchange, exchangeHost, exchangePort, rawMessage))

        respStatusCode = resp.get("statusCode", 600)

        if respStatusCode == 200:
            count = resp.get("stats", {}).get("count", None)
            if count:
                dbInfo[reqExchange]["stats"]["count"] = count
            
            return json.dumps({
                "statusCode": 200,
                "error": False,
                "message": resp.get("message")
            })

        else:
            if respStatusCode == 604:
                raise NoMessageException()
            
            raise UnknownException(message=resp.get("message"), statusCode=respStatusCode)



@app.get("/")
async def getActiveStatus():
    return {
        "statusCode": 200,
        "message": "Server is Active"
    }

# @app.on_event("startup")
# async def setUp():
#     # TO-DO - Setup Redis Client
#     pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mbserver:app", host="0.0.0.0", port=42426, workers=NUMBER_OF_MB_WORKERS, reload=True)  # TO-DO Change this