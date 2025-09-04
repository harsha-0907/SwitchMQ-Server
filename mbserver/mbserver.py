
# Server responsible for websocket & MB
import os, json, socket
from dotenv import load_dotenv
from mbexceptions import *
from utils.jwtUtils import decodeJWT
from utils.responsePages import UN_AUTH_401_RESP
from fastapi import (FastAPI, WebSocket, Header, HTTPException, Depends, WebSocketException, status, WebSocketDisconnect)

load_dotenv()
users = dict()
connections = dict()
dbStats = {
    "": {
        "stats": {
            "maxSize": 100000, # Mandatory
            "size": 1,    # Mandatory
            "host": "127.0.0.1",# Mandatory
            "port": 12345   # Mandatory
        },
        "": 1
    }
}
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

def processMessage(message):
    """ Process the message to escape any characters"""
    if message[0] == "~":
        return '~' + message

    if message == "GET":
        return '~' + message

    return message

def fetchDBStats():
    """ Fetches the stats of the exchanges & queue"""
    # Run once every DB_POLL_INTERVAL seconds
    pass

async def processExchange(host, port, message)-> str:
    """ This function sends the data to the exchange"""
    # TO-DO : Comment or remove the testing part
    return json.dumps(
        {
            "statusCode": 200,
            "stats": {
                "count": 100,
                "message": "This is a test message" # Optional in case of exception
            }
        }
    )
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.sendall(bytes(message, "UTF-8"))
    resp = sock.recv(1024).decode("utf-8")
    return resp

async def executeCommand(inputData, userData)-> str | bool:
    """ Executes the commands sent"""
    action = inputData.get("action"); exchange = inputData.get("exchange", ""); queue = inputData.get("queue", "")
    userExchanges = userData.get("access", {}).get("exchange", [])

    if exchange not in dbStats:
        print("exhange not present")
        raise ExchangeNotFoundError()
    
    if userExchanges != "*" and exchange not in userExchanges:
        print("User not authorized")
        raise UnAuthorizedAccess()
    
    connectionStats = dbStats[exchange]["stats"]
    host = connectionStats["host"]; port = connectionStats["port"]

    if action == "POST":
        message = inputData.get("message", "")
        message = processMessage(message) # Escaping Characters
        
        if len(message) > MAX_MESSAGE_SIZE:
            raise MessageSizeExceededError()
        
        elif connectionStats.get("size", 0) >= connectionStats.get("maxSize", 0) - NUMBER_OF_MB_WORKERS:
            raise ExchangeOverflowError()
        
        else:
            stats = dbStats[exchange]["stats"]
            resp = await processExchange(host, port, message)
            resp = json.loads(resp)
            print(resp)

            responseStatusCode = resp["statusCode"]
            if responseStatusCode == 200:
                exchangeCount = resp.get("stats", {}).get("size", None)
                if exchangeCount:
                    dbStats[exchange]["stats"]["size"] = exchangeCount

                return True

            else:
                if responseStatusCode == 500:
                    raise ExchangeOverflowError("MemoryError: Insufficient FreeSpace")
                
                elif responseStatusCode == 501:
                    raise ExchangeOverflowError()
                
                
                message = resp["stats"].get("messsage", "Unknown Exception")
                raise UnknownException(message)
            
    elif action == "GET":
        message = "GET"
        resp = await processExchange(host, port, message)
        resp = json.loads(resp)
        responseStatusCode = resp["statusCode"]
        responseStats = resp.get("stats", {})

        if responseStatusCode == 200:
            exchangeCount = responseStats.get("size", None)
            if exchangeCount:
                dbStats[exchange]["stats"]["size"] = exchangeCount

            message = responseStats.get("message", "")
            return message
        
        else:
            if responseStatusCode == 502:
                raise NoMessageException()
            
            raise UnknownException(responseStats.get("message"))

    else:
        raise UnknownException(message=f"Invalid Action: This {action} is invalid")

@app.websocket("/mb")
async def handleWebsocket(websocket: WebSocket, userData: dict = Depends(isAuthenticated)):
    await websocket.accept()
    connections[websocket] = userData
    users[userData["username"]] = userData
    print("list of connections:", connections)

    try:
        while True:
            data = await websocket.receive_text()
            
            if data == "Ping":  # Ping-Response
                await websocket.send_text("Reply")
                continue

            try:
                data = json.loads((data))
                resp = await executeCommand(data, userData)
                print(resp)
                await websocket.send_text(f"Echo: Hello")
            
            except json.JSONDecodeError as _jde:
                print("Message is not in the correct format")
                # TO-DO - Return the error message
                await websocket.send_text(f"Nope")

    except WebSocketDisconnect as we:
        print("Diconnected Successfully")

    except WebSocketException as _we:
        print("Socket closed")

    

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