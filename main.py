import time
from ipaddress import ip_address
from typing import Callable

import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter

from src.database.db import get_db
from src.routes import contacts, auth, users
from src.conf.config import settings

app = FastAPI()


@app.on_event("startup")
async def startup():
    """
    The startup function is called when the application starts up.
    It can be used to initialize things that are needed by the app, such as
    connecting to a database or initializing an external API.

    :return: A coroutine, which is a function that returns a future
    :doc-author: Trelent
    """
    r = await redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)
    await FastAPILimiter.init(r)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://127.0.0.1:8000', 'http://localhost:8000'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ALLOWED_IPS = [ip_address('192.168.1.0'), ip_address(
    '172.16.0.0'), ip_address("127.0.0.1")]


@app.middleware("http")
async def limit_access_by_ip(request: Request, call_next: Callable):
    """
    The limit_access_by_ip function is a middleware that limits access to the API only from certain IP addresses.
    It checks if the client's IP address is in ALLOWED_IPS, and if not, it returns an error message.

    :param request: Request: Get the ip address of the client
    :param call_next: Callable: Pass the next function in the chain
    :return: A jsonresponse object if the ip address is not allowed
    :doc-author: Trelent
    """
    ip = ip_address(request.client.host)
    if ip not in ALLOWED_IPS:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Not allowed IP address"})
    response = await call_next(request)
    return response


@app.middleware('http')
async def custom_middleware(request: Request, call_next):
    """
    The custom_middleware function is a middleware function that prints the base URL of the request,
    and then adds a header to the response called &quot;performance&quot; with how long it took to process.
    :param request: Request: Get the request information
    :param call_next: Call the next middleware in the chain
    :return: A response object
    :doc-author: Trelent

    """
    print(request.base_url)
    start_time = time.time()
    response = await call_next(request)
    during = time.time() - start_time
    response.headers['performance'] = str(during)
    return response

templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse, description="Main Page")
async def root(request: Request):
    """
    The root function is the entry point of the application.
    It returns a TemplateResponse object, which renders an HTML template using Jinja2.
    The template contains a link to /docs, where you can find more information about this app.
    :param request: Request: Get the request object for the incoming http request
    :return: A template response, which is a special type of response
    :doc-author: Trelent
    """
    return templates.TemplateResponse('index.html', {"request": request, "title": "Менеджер контактів"})


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    """
    The healthchecker function is a function that checks the health of the database.
    It does this by making a request to the database and checking if it returns any results.
    If it doesn't, then we know something is wrong with our connection to the database.
    :param db: Session: Get the database session
    :return: A dict with a message
    :doc-author: Trelent
    """
    try:
        # Make request
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail="Error connecting to the database")


app.include_router(contacts.router, prefix="/api")
app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')
