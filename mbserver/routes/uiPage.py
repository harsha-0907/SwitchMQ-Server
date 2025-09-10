
# This handles all the actions for Admin Page
# TO-DO : Shift the page handling from Files to tinydb
import json
from typing import Annotated
from fastapi import APIRouter, Depends, Cookie, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from utils.responsePages import *
from utils.routeUtils import fetchFile
from utils.jwtUtils import decodeJWT
from utils.utilsHelper import stopExchange

def isAuthorizedForUI(switchMqAuthorization: str = Cookie(...)):
    """ Checks if the user has access to UI"""
    userData = decodeJWT(switchMqAuthorization)
    if isinstance(userData, dict):
        if userData.get("access", {}).get("ui", False):
            return userData
    
    raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

def isAdmin(switchMqAuthorization: str = Cookie(...)):
    """ Checks if the user has admin privilige"""
    userData = decodeJWT(switchMqAuthorization)
    print(userData)
    if isinstance(userData, dict):
        if userData.get("access", {}).get("admin", False):
            return userData
    
    raise HTTPException(
            status_code=403,
            detail="Un-Authorized Actions",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
CREDENTIALS_FILE = "credentials.json"
router = APIRouter(prefix="/ui", dependencies=[Depends(isAuthorizedForUI)])

# Admin-Permissions
@router.delete("/user")
def deleteUser(username: str, _=Depends(isAdmin)):
    print("User is getting deleted")
    return JSONResponse(
        content={
            "message": f"{username} Deleted Successfully"
        }, status_code=200
    )

    with open(CREDENTIALS_FILE, 'r') as file:
        userData = json.load(file)

    if username in userData:
        del(userData[username])
        with open(CREDENTIALS_FILE, 'w') as file:
            json.dump(userData, file, indent=4)

    return JSONResponse(
        content={
            "message": f"{username} Deleted Successfully"
        }, status_code=200
    )
 
@router.put("/user")
def addUser(newUserData: dict, _=Depends(isAdmin)):
    # TO-DO : Complete the part to add the user into the dictionary and save the file
    try:
        with open(CREDENTIALS_FILE, 'r') as file:
            userData = json.load(file)

    except FileNotFoundError as _fe:
        print("Credentials file not found")
        return INTERNAL_SERVER_ERROR_500_RESP
    
    username = newUserData.get("username", None)
    
    if username == "admin":
        return JSONResponse(
            content={
                "message": "Cannot modify the admin"
            }, status_code=403
        )
    
    try:
        if username in userData:
            # Update the User
            return JSONResponse(
                content={
                    "message": "User already exists!"
                },status_code=200
            )

        else:
            newUserData["access"]["ui"] = True
            newUserData["access"]["admin"] = False
            userData[username] = newUserData

            with open(CREDENTIALS_FILE, 'w') as file:
                json.dump(userData, file, indent=4)

            return JSONResponse(
                content={"message": f"User '{username}' added successfully."},
                status_code=201
            )
    
    except Exception as _e:
        return JSONResponse(status_code=600,
            content={"message": str(_e)}
        )

@router.delete("/exchange")
async def deleteExchange(exchangeName: str, request: Request, _=Depends(isAdmin)):
    print("Deleting Exchange", exchangeName)
    print(request.app.state.exchanges)
    await stopExchange(exchangeName, request.app.state.exchanges)

    return JSONResponse(content={
        "message": "Exchange is being stopped"
    }, status_code=200)

# Non-Admin Priviliges
@router.get("/")
def sendUIPage():
    """ Sends the Admin UI Page"""
    uiPage = ""
    with open("src/adminUI.html", 'r') as file:
        uiPage = file.read()
    return HTMLResponse(content=uiPage, status_code=200)

@router.get("/user")
async def fetchUserDetails():
    try:
        fileContent = json.loads(fetchFile("credentials.json"))
        users = []

        for _userData in fileContent.values():
            _userData["password"] = "xxxxxx"
            users.append(_userData)
        
        return JSONResponse(content={
            "users": users
        }, status_code=200)
    
    except Exception as _e:
        print(_e)
        return JSONResponse(content={
            "users": []
        }, status_code=200)

@router.get("/exchange")
async def fetchExchangeDetails(request: Request):
    try:
        redisClient = request.app.state.redisClient
        keys = redisClient.keys()
        exchanges = []
        for key in keys:
            exchangeData = redisClient.hgetall(key)
            exchanges.append(exchangeData)
        
        return JSONResponse(
            content={
                "exchanges": exchanges
            }, status_code=200
        )
    
    except Exception as _e:
        print(_e)
        return JSONResponse(
            content={
                "exchanges": []
            }
        )





