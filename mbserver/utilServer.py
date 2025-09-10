
import os
import time
import redis
import asyncio
from multiprocessing import Process, Event
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from routes import login, uiPage
from dotenv import load_dotenv
from starlette.exceptions import HTTPException as StarletteHTTPException
from utils.utilsHelper import start_exchange
from utils.routeUtils import fetchFile
load_dotenv()

app = FastAPI()

app.include_router(login.router, tags=["Auth"])
app.include_router(uiPage.router, tags=["Admin-UI"])

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        # Return a custom HTML response for 404
        return HTMLResponse(
            content="""
            <html>
                <head><title>404 Not Found</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 2rem;">
                    <h1>404 - Page Not Found</h1>
                    <p>Oops! The page you are looking for does not exist.</p>
                    <a href="/">Go back home</a>
                </body>
            </html>
            """,
            status_code=404,
        )
    # For other HTTP exceptions, just return the default one
    return await app.default_exception_handler(request, exc)

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
        exchangeObject.terminate()
        exchangeObject.join()
    
    time.sleep(1)   # Buffer for complete shutdown
    print("Exchanges terminated")

@app.get("/")
async def getHomePage():
    homePage = fetchFile("src/index.html")

    return HTMLResponse(content=homePage, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("utilServer:app", host="0.0.0.0", port=42425, reload=True)
    