from typing import List

from fastapi import Depends, HTTPException, status, APIRouter, Security, BackgroundTasks, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel, RequestEmail
from src. repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_email
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

router = APIRouter(prefix="/auth", tags=['auth'])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    The signup function creates a new user in the database.
    It takes a UserModel object as input, and returns the newly created user.
    If an account with that email already exists, it raises an HTTP 409 error.

    :param body: UserModel: Receive the request body and deserialize it into a usermodel object
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the server
    :param db: Session: Get a database session
    :return: A user object, which is serialized to a json response
    :doc-author: Trelent
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url)
    return new_user


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    The login function is used to authenticate a user.
        It takes the email and password of the user, verifies them against
        those stored in the database, and returns an access token if they match.

    :param body: OAuth2PasswordRequestForm: Validate the request body
    :param db: Session: Get a database session
    :return: A dictionary with the access_token, refresh_token and token type
    :doc-author: Trelent
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmad")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
    The refresh_token function is used to refresh the access token.
        The function takes in a refresh token and returns an access token, a new refresh token, and the type of authentication being used.

    :param credentials: HTTPAuthorizationCredentials: Get the token from the request header
    :param db: Session: Get the database session
    :return: A dictionary with three keys: access_token, refresh_token, and token_type
    :doc-author: Trelent
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.
        It takes in the token that was sent to the user's email and uses it to get their email address.
        Then, it gets the user from the database using their email address and checks if they are already confirmed.
        If they are, then an error message is returned saying that their account has already been confirmed.  Otherwise, 
        we update them in our database as being confirmed.

    :param token: str: Get the token from the url
    :param db: Session: Pass the database session to the function
    :return: A message that the email is already confirmed or a message that the email has been confirmed
    :doc-author: Trelent
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    The request_email function is used to send an email to the user with a link
    to confirm their account. The function takes in the body of the request, which
    is a RequestEmail object containing an email address. It then checks if there is
    a user associated with that email address and if so, sends them an email.

    :param body: RequestEmail: Validate the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the application
    :param db: Session: Get the database session
    :return: A message to the user
    :doc-author: Trelent
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user:
        if user.confirmed:
            return {"message": "Your email is already confirmed"}
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}
