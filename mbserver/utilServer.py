
from fastapi import FastAPI
from routes import login, uiPage

app = FastAPI()

app.include_router(login.router, tags=["Auth"])
app.include_router(uiPage.router, tags=["Admin-UI"])

@app.get("/")
async def getHomePage():
    return {
        "statusCode": 200,
        "message": "Server is alive and running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("utilServer:app", host="0.0.0.0", port=42425, reload=True)