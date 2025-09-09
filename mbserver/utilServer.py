
import os
import time
import redis
import asyncio
from multiprocessing import Process, Event
from fastapi import FastAPI
from routes import login, uiPage
from dotenv import load_dotenv
from utils.utilsHelper import start_exchange
load_dotenv()

app = FastAPI()

app.include_router(login.router, tags=["Auth"])
app.include_router(uiPage.router, tags=["Admin-UI"])

@app.on_event("startup")
async def startup_event():
    app.state.exchanges = dict()
    app.state.redisClient = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT")),
        username=os.getenv("REDIS_USERNAME"),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True
    )
    processTerminateSwitch = Event()
    args = {
        "hostName": "server01",
        "exchangeName": "default",
        "port": 46123,
        "queues": ["default"],
        "terminateSwitch": processTerminateSwitch
    }
    exchangeProcess = Process(target=start_exchange, args=(args,))
    exchangeProcess.start()
    app.state.exchanges[args["exchangeName"]] = (exchangeProcess, processTerminateSwitch)

    time.sleep(2)

@app.on_event("shutdown")
async def shutdown_event():
    exchanges = app.state.exchanges
    for exchangeName, exchangeProcess in exchanges.items():
        exchangeObject, exchangeTerminateSwitch = exchangeProcess
        exchangeTerminateSwitch.set()
        exchangeProcess.terminate()
        exchangeProcess.join()
    
    time.sleep(1)   # Buffer for complete shutdown
    print("Exchanges terminated")

@app.get("/")
async def getHomePage():
    return {
        "statusCode": 200,
        "message": "Server is alive and running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("utilServer:app", host="0.0.0.0", port=42425, reload=True)
    