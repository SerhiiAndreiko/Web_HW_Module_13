import pickle

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer  # Bearer token
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from src.database.db import get_db
from src.repository import users as repository_users
import redis as redis
from src.conf.config import settings


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    def verify_password(self, plain_password, hashed_password):
        """
        The verify_password function is used to verify a plain-text password against a hashed password.
        The function returns True if the passwords match, and False otherwise.

        :param self: Make the method a bound method, which means that it can be called on instances of the class
        :param plain_password: Compare the password that is entered by the user
        :param hashed_password: Compare the hashed password in the database with a new plain text password
        :return: A boolean value
        :doc-author: Trelent
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        The get_password_hash function takes a password and returns the hash of that password.
        The hash is generated using the CryptContext object, which is created in main.py.

        :param self: Represent the instance of the class
        :param password: str: Get the password from the user
        :return: A hash of the password
        :doc-author: Trelent
        """
        return self.pwd_context.hash(password)

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        The create_access_token function creates a new access token.


        :param self: Access the class attributes
        :param data: dict: Pass the data to be encoded
        :param expires_delta: Optional[float]: Set the expiration time of the access token
        :return: A jwt access token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        The create_refresh_token function creates a refresh token for the user.
            The function takes in two parameters: data and expires_delta.
            Data is a dictionary that contains information about the user, such as their username and password.
            Expires_delta is an optional parameter that determines how long the refresh token will be valid for.

        :param self: Represent the instance of the class
        :param data: dict: Pass in the user's data
        :param expires_delta: Optional[float]: Set the expiration time for the refresh token
        :return: A refresh token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token
    # limit: int = Query(10, le=500), offset: int = 0, db: Session = Depends(get_db),
    #                    _: User = Depends(auth_service.get_current_user)):

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        The get_current_user function is a dependency that will be used in the
            protected endpoints. It takes a token as an argument and returns the user
            if it's valid, or raises an HTTPException with status code 401 (Unauthorized)
            if not.

        :param self: Access the class attributes
        :param token: str: Get the token from the request header
        :param db: Session: Pass the database session to the function
        :return: A user object
        :doc-author: Trelent
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY,
                                 algorithms=[self.ALGORITHM])
            if payload.get("scope") == "access_token":
                email = payload.get("sub")
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        # user = await repository_users.get_user_by_email(email, db)
        user = self.r.get(f"user:{email}")
        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.r.set(f"user:{email}", pickle.dumps(user))
            self.r.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)
        if user is None:
            raise credentials_exception
        return user

    async def decode_refresh_token(self, refresh_token: str):
        """
        The decode_refresh_token function is used to decode the refresh token.
            The function takes in a refresh_token as an argument and returns the email of the user if successful.
            If not, it raises an HTTPException with status code 401 (Unauthorized) and detail 'Invalid scope for token' or 'Could not validate credentials'. 

        :param self: Represent the instance of a class
        :param refresh_token: str: Pass in the refresh token that was sent to the client
        :return: An email address
        :doc-author: Trelent
        """
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate credentials')

    def create_email_token(self, data: dict):
        """
        The create_email_token function creates a token that is used to verify the user's email address.
        The token contains the following information:
            - iat (issued at): The time when the token was created.
            - exp (expiration): The time when this token will expire and no longer be valid. This is set to 7 days from creation date by default, but can be changed in settings.py if desired. 
            - scope: A string indicating what this particular JWT can do or access.

        :param self: Make the function a method of the class
        :param data: dict: Pass in the data that will be encoded into the token
        :return: A token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "email_token"})
        token = jwt.encode(to_encode, self.SECRET_KEY,
                           algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        """
        The get_email_from_token function takes a token as an argument and returns the email address associated with that token.
        The function first tries to decode the token using jwt.decode(). If it is successful, then it checks if the scope of 
        the payload is 'email_token'. If so, then it returns the sub (subject) field from the payload which contains 
        the email address.

        :param self: Represent the instance of the class
        :param token: str: Pass in the token that is sent to the user's email
        :return: The email of the user that is in the payload
        :doc-author: Trelent
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY,
                                 algorithms=[self.ALGORITHM])
            if payload['scope'] == 'email_token':
                email = payload['sub']
                return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")


auth_service = Auth()
