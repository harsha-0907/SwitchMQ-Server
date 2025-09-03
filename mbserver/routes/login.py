
# Handles the entire login flow
import json
from utils.jwtUtils import encodeJWT
from functools import lru_cache
from fastapi import APIRouter, Body
from fastapi.responses import HTMLResponse, JSONResponse
from utils.responsePages import *

router = APIRouter(prefix="/auth")

@lru_cache
@router.get("/login")
async def sendLoginPage():
    try:
        with open("src/loginPage.html", 'r') as file:
            return HTMLResponse(content=file.read(), status_code=200)

    except FileNotFoundError as _e:
        print("File Removed!")
        return INTERNAL_SERVER_ERROR_500_RESP
    
@router.post("/login")
async def fetchLoginCreds(username: Annotated[str, Body()], password: Annotated[str, Body()]):
    credentials = dict()
    with open("credentials.json", 'r') as file:
        credentials = json.load(file)
        userData = credentials.get(username, None)

    if userData is None or userData.get("password", None) != password:
        return UN_AUTH_401_RESP
    
    jwtToken = encodeJWT(userData)

    return JSONResponse(content={
        "auth-token": jwtToken
    }, status_code=200)

