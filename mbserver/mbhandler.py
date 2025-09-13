
# Server responsible for websocket & MB
import os, json, socket, asyncio, redis, time
from threading import Lock
from dotenv import load_dotenv
from mbexceptions import *
from apscheduler.schedulers.background import BackgroundScheduler
from utils.jwtUtils import decodeJWT
from utils.responsePages import UN_AUTH_401_RESP
from fastapi import (FastAPI, WebSocket, Header, HTTPException, Depends, WebSocketException, status, WebSocketDisconnect)

load_dotenv()
users = dict()
connections = dict()

dbInfoLock = Lock()
dbInfo = {}
app = FastAPI()

MAX_MESSAGE_SIZE = int(os.getenv("MAX_MESSAGE_SIZE"))

def updateDBInfo():
    """ Fetch data from redis db and filter data"""
    global dbInfo, dbInfoLock
    redisClient = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            username=os.getenv("REDIS_USERNAME"),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
    
    keys = redisClient.keys()
    redisData = dict()

    for key in keys:
        _exchangeData = redisClient.hgetall(key)
        key = key.split(".")[1]
        exchangeData = {
            "host": _exchangeData["ipAddress"],
            "count": int(_exchangeData["totalMessages"]),
            "port": int(_exchangeData["port"]),
            "maxSize": int(_exchangeData["maxMessages"])
        }
        queues = list(_exchangeData["queues"].split(','))
        redisData[key] = {
            "stats": exchangeData,
            "queues": queues
        }
    
    with dbInfoLock:
        for exchangeName, exchangeData in redisData.items():
            dbInfo[exchangeName] = exchangeData
    
    print("DB Info Updated")

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
    
    except ConnectionError as _e:
        resp = str(ReturnableException(ExchangeNotFoundError()))

    except Exception as _e:
        resp = str(ReturnableException(_e))
    
    finally:
        return resp

async def executeCommand(rawMessage:str, userData, inputData: dict)-> str:
    """ Executes the commands & returns the response"""
    global dbInfo, dbInfoLock
    reqAction = inputData.get("action"); reqExchange = inputData.get("exchange", ""); reqQueues = inputData.get("queues", [])
    userAuthorizedExchanges = userData.get("access", {}).get("exchange", [])
    
    if reqExchange not in userAuthorizedExchanges:
        print("Un-Authorized")
        raise UnAuthorizedAccess()
    
    with dbInfoLock:
        exchangeInfo = dbInfo.get(reqExchange, None)
    
    print(inputData)
    print(dbInfo)
    if exchangeInfo is None:
        print("Exchange not Found")
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

    elif reqAction == "POST":
        message = inputData.get("message")
        if not isValidMessage(rawMessage):
            raise MessageException("Message Size Exceeded")
        
        if exchangeStats.get("count") >= exchangeStats.get("maxSize"):
            raise ExchangeOverflowError()
        
        resp = json.loads(await asyncio.to_thread(processExchange, exchangeHost, exchangePort, rawMessage))
        respStatusCode = resp.get("statusCode", 600)

        # print(resp)
        if respStatusCode == 200:
            count = resp.get("stats" ,{}).get("count", None)
            if count:
                dbInfo[reqExchange]["stats"]["size"] = count
            
            return json.dumps({
                "statusCode": 200,
                "error": False,
                "message": "Success"
            })
        
        else:
            if respStatusCode == 602:
                raise ExchangeOverflowError()
            
            elif respStatusCode == 606:
                raise MemoryException("MemoryException: Insufficient Free Space")
            
            raise UnknownException(message=resp.get("message", "Unknown Exception"), statusCode=respStatusCode)

    elif reqAction == "UPDATE-ADD":
        print(reqAction)
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
            raise UnknownException(message=resp.get("message"), statusCode=respStatusCode)
    
    elif reqAction == "UPDATE-REMOVE":
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
            raise UnknownException(message=resp.get("message"), statusCode=respStatusCode)

    else:
        raise UnknownException(message="Action: Action not Recognized")

@app.websocket("/mb")
async def handleWebsocket(websocket: WebSocket, userData: dict = Depends(isAuthenticated)):
    """ Fetches the message from client & sends it as-is to the executeCommand -> Sends reply as-is & handles exceptions"""
    await websocket.accept()
    connections[websocket] = userData
    users[userData["username"]] = userData

    try:
        while True:
            try:
                _data = await websocket.receive_text()
                
                if _data == "Ping":  # Ping-Response
                    await websocket.send_text("Suii")
                    continue

                data = json.loads((_data))
                ack = data.get("ack", False)
                if ack:
                    resp = await executeCommand(rawMessage=_data,userData=userData, inputData=data)
                    await websocket.send_text(resp)
                else:
                    asyncio.create_task(executeCommand(rawMessage=_data,userData=userData, inputData=data))

            except json.JSONDecodeError as e:
                resp = str(ReturnableException(JSONError()))
                await websocket.send_text(resp)
            
            except WebSocketDisconnect as e:
                # Break the loop
                break

            except WebSocketException as _we:
                # Break the loop
                print(f"Websocket Exception {_we}")
                break
            
            except Exception as e:
                print(e)
                resp = str(ReturnableException(e))
                await websocket.send_text(resp)

    except Exception as e:
        print(e)
    
    finally:
        # Connection terminated
        if websocket in connections:
            user = connections[websocket]
            if user["username"] in users:
                del(users[user["username"]])
            del(connections[websocket])

@app.get("/")
async def getActiveStatus():
    return {
        "statusCode": 200,
        "message": "Server is Active"
    }

@app.on_event("startup")
async def setUp():
    # Seting up the background scheduler
    bgScheduler = BackgroundScheduler()
    bgScheduler.start()
    bgScheduler.add_job(updateDBInfo, 'interval', seconds=3)
    time.sleep(2)
    print("Starting the System...")

