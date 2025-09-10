
# Handles the entire login flow
import json
from typing import Annotated
from utils.jwtUtils import encodeJWT
from fastapi import APIRouter, Body
from fastapi.responses import HTMLResponse, JSONResponse
from utils.responsePages import *
from utils.routeUtils import fetchFile

router = APIRouter(prefix="/auth")

@router.get("/login")
async def sendLoginPage():
    resp = None
    try:
        loginPage = fetchFile(filePath="src/loginPage.html")
        resp = HTMLResponse(content=loginPage, status_code=200)

    except FileNotFoundError as _e:
        resp = INTERNAL_SERVER_ERROR_500_RESP
    
    return resp
    
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

