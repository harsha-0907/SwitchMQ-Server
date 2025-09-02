from fastapi.responses import HTMLResponse

UN_AUTH_401_RESP = HTMLResponse(
    content="""
    <html>
        <head><title>401 Unauthorized</title></head>
        <body style="font-family: Arial; text-align: center; padding-top: 50px;">
            <h1>401 - Unauthorized</h1>
            <p>You are not authorized to access this resource.</p>
        </body>
    </html>
    """,
    status_code=401
)

FORBIDDEN_403_RESP = HTMLResponse(
    content="""
    <html>
        <head><title>403 Forbidden</title></head>
        <body style="font-family: Arial; text-align: center; padding-top: 50px;">
            <h1>403 - Forbidden</h1>
            <p>You do not have permission to access this resource.</p>
        </body>
    </html>
    """,
    status_code=403
)

RESOURCE_NOT_FOUND_404_RESP = HTMLResponse(
    content="""
    <html>
        <head><title>404 Not Found</title></head>
        <body style="font-family: Arial; text-align: center; padding-top: 50px;">
            <h1>404 - Not Found</h1>
            <p>The resource you are looking for could not be found.</p>
        </body>
    </html>
    """,
    status_code=404
)

UNPROCESSABLE_ENTITY_422_RESP = HTMLResponse(
    content="""
    <html>
        <head><title>422 Unprocessable Entity</title></head>
        <body style="font-family: Arial; text-align: center; padding-top: 50px;">
            <h1>422 - Unprocessable Entity</h1>
            <p>The server understands the request but cannot process it due to semantic errors.</p>
        </body>
    </html>
    """,
    status_code=422
)

INTERNAL_SERVER_ERROR_500_RESP = HTMLResponse(
    content="""
    <html>
        <head><title>500 Internal Server Error</title></head>
        <body style="font-family: Arial; text-align: center; padding-top: 50px;">
            <h1>500 - Internal Server Error</h1>
            <p>Something went wrong on the server. Please try again later.</p>
        </body>
    </html>
    """,
    status_code=500
)
