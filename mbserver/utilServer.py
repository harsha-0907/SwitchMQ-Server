
import time
import asyncio
from multiprocessing import Process
from fastapi import FastAPI
from exchangeHandler import Exchange
from routes import login, uiPage

app = FastAPI()

app.include_router(login.router, tags=["Auth"])
app.include_router(uiPage.router, tags=["Admin-UI"])

exchange_process = None

def start_exchange():
    exchange = Exchange(hostName="server01", exchangeName="", port=47001, queues=[""])
    asyncio.run(exchange.handleSocket())  # Runs the async socket server

@app.on_event("startup")
async def startup_event():
    global exchange_process
    exchange_process = Process(target=start_exchange)
    exchange_process.start()
    time.sleep(2)

@app.on_event("shutdown")
async def shutdown_event():
    global exchange_process
    if exchange_process:
        exchange_process.terminate()
        exchange_process.join()
        print("Exchange process terminated")

@app.get("/")
async def getHomePage():
    return {
        "statusCode": 200,
        "message": "Server is alive and running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("utilServer:app", host="0.0.0.0", port=42425, reload=True)
    