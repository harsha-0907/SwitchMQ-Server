
# This handles all the actions for Admin Page
# TO-DO : Shift the page handling from Files to tinydb
import json
from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from utils.responsePages import *
from utils.jwtUtils import decodeJWT

CREDENTIALS_FILE = "credentials.json"
router = APIRouter(prefix="/admin")

def isAuthorizedForUI(authorization: str = Header(...)):
    """ Lets only admin access UI"""
    userData = decodeJWT(authorization)
    if isinstance(userData, dict):
        if userData.get("access", {}).get("ui", False):
            return userData
    
    raise HTTPException(
            status_code=401,
            detail="Invalid token",  # Still required
            headers={"WWW-Authenticate": "Bearer"},
            response=UN_AUTH_401_RESP
        )

# TO-DO Cache the page
@router.get("/")
def sendUIPage(userData = Depends(isAuthorizedForUI)):
    """ Sends the Admin UI Page"""
    uiPage = ""
    with open("src/adminUI.html", 'r') as file:
        uiPage = file.read()
    return HTMLResponse(content=uiPage, status_code=200)

@router.delete("/user")
def deleteUser(username: str, _=Depends(isAuthorizedForUI)):
    with open(CREDENTIALS_FILE, 'r') as file:
        userData = json.load(file)
    
    if username != "admin" and username in userData:
        del(userData[username])
        with open(CREDENTIALS_FILE, 'w') as file:
            json.dump(userData, file, indent=4)
        return JSONResponse(
            content={
                "message": f"{username} Deleted Successfully"
            }, status_code=200
        )
    
    else:
        return JSONResponse(
            content={
                "message": f"{username} doesn't exist"
            }, status_code=200
        )
    
@router.put("/user")
def addUser(newUserData: dict, _=Depends(isAuthorizedForUI)):
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
    
    if username in userData:
        # Update the User
        userData[username] = newUserData
        with open(CREDENTIALS_FILE, 'w') as file:
            json.dump(userData, file, indent=4)
        return JSONResponse(
            content={"message": f"{username} updated."},
            status_code=200
        )

    # Build user entry
    newUserData["access"]["ui"] = False

    userData[username] = newUserData

    with open(CREDENTIALS_FILE, 'w') as file:
        json.dump(userData, file, indent=4)

    return JSONResponse(
        content={"message": f"User '{username}' added successfully."},
        status_code=201
    )

