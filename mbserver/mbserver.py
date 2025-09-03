
# Server responsible for websocket & MB
from utils.jwtUtils import decodeJWT
from utils.responsePages import UN_AUTH_401_RESP
from fastapi import (FastAPI, WebSocket, Header, HTTPException, Depends, WebSocketException, status)

app = FastAPI()
globalConnections = dict()

def isAuthenticated(websocket: WebSocket):
    authorization = websocket.headers.get("authorization", None)
    if authorization is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    userData = decodeJWT(authorization)
    if not userData:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    
    return userData

@app.websocket("/mb")
async def handleWebsocket(websocket: WebSocket, userData: dict = Depends(isAuthenticated)):
    global globalConnections
    await websocket.accept()
    globalConnections[websocket] = userData

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")

    except WebSocketException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

    except Exception as e:
        await websocket.close()
        print("Error:", e)
