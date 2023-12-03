from typing import List
from datetime import date, timedelta
from fastapi_limiter.depends import RateLimiter
from fastapi import Depends, HTTPException, status, Path, APIRouter
from sqlalchemy.orm import Session
from src.database.models import User, Role
from src.database.db import get_db
from src.repository import contacts as repository_contacts
from src.schemas import ContactResponse, ContactBase
from src.services.auth import auth_service
from src.services.roles import RoleAccess
router = APIRouter(prefix="/contacts", tags=["contacts"])

allowed_operation_get = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_create = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_update = RoleAccess([Role.admin, Role.moderator])
allowed_operation_remove = RoleAccess([Role.admin])


@router.get("/", response_model=List[ContactResponse], dependencies=[Depends(allowed_operation_get), Depends(RateLimiter(times=2, seconds=5))], name="Return contacts")
async def get_contacts(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    The get_contacts function returns a list of contacts.


    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the current user
    :return: A list of contacts from the database
    :doc-author: Trelent
    """
    contacts = await repository_contacts.get_contacts(db)
    return contacts


@router.get("/search_by_id/{id}", response_model=ContactResponse, dependencies=[Depends(allowed_operation_get)])
async def get_contact(id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    The get_contact function returns a contact by id.

    :param id: int: Specify the id of the contact to be retrieved
    :param db: Session: Pass the database session to the repository layer
    :param current_user: User: Get the current user
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.get_contact_by_id(id, db)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.get(
    "/search_by_last_name/{last_name}",
    response_model=List[ContactResponse], dependencies=[
        Depends(allowed_operation_get)],
    name="Search contacts by last name",
)
async def search_contacts_by_last_name(last_name: str, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    The search_contacts_by_last_name function searches for a contact by last name.
        Args:
            last_name (str): The last name of the contact to search for.

    :param last_name: str: Specify the last name of the contact to be searched for
    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the user id of the current logged in user
    :return: A single contact
    :doc-author: Trelent
    """
    contact = await repository_contacts.search_contacts_by_last_name(last_name, db)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.get(
    "/search_by_first_name/{first_name}",
    response_model=List[ContactResponse], dependencies=[
        Depends(allowed_operation_get)],
    name="Search contacts by first name",
)
async def search_contacts_by_first_name(first_name: str, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    The search_contacts_by_first_name function searches for a contact by first name.
        Args:
            first_name (str): The first name of the contact to search for.

    :param first_name: str: Get the first name of a contact from the url
    :param db: Session: Pass the database session to the repository layer
    :param current_user: User: Get the current user from the auth_service
    :return: A list of contacts with the given first name
    :doc-author: Trelent
    """
    contact = await repository_contacts.search_contacts_by_first_name(first_name, db)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.get(
    "/search_by_email/{email}",
    response_model=List[ContactResponse], dependencies=[
        Depends(allowed_operation_get)],
    name="Search contacts by email",
)
async def search_contacts_by_email(email: str, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    The search_contacts_by_email function searches for a contact by email.
        If the contact is not found, it raises an HTTPException with status code 404 and detail &quot;Not Found&quot;.
        Otherwise, it returns the contact.

    :param email: str: Specify the email of the contact to be searched
    :param db: Session: Pass the database session to the repository layer
    :param current_user: User: Get the current logged in user
    :return: A contact object, which is a dictionary
    :doc-author: Trelent
    """
    contact = await repository_contacts.search_contact_by_email(email, db)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,  dependencies=[Depends(allowed_operation_create)])
async def create_contacts(body: ContactBase, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    The create_contacts function creates a new contact in the database.

    :param body: ContactBase: Get the data from the request body
    :param db: Session: Pass the database connection to the repository layer
    :param current_user: User: Get the current user from the database
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.get_contact_by_email(body.email, db)
    if contact:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is exists!"
        )

    contact = await repository_contacts.create(body, db)
    return contact


@router.put("/{id}", response_model=ContactResponse,  dependencies=[Depends(allowed_operation_update)], description='Only moderators and admin')
async def update_contact(body: ContactBase, id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    The update_contact function updates a contact in the database.

    :param body: ContactBase: Pass the contact data to be updated
    :param id: int: Specify the id of the contact to be deleted
    :param db: Session: Access the database
    :param current_user: User: Get the current user from the auth_service
    :return: A contactbase object
    :doc-author: Trelent
    """
    contact = await repository_contacts.update(id, body, db)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    return contact


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT,  dependencies=[Depends(allowed_operation_remove)], description='Only admin')
async def remove_contact(id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    The remove_contact function removes a contact from the database.
        It takes an id as input and returns the removed contact.

    :param id: int: Specify the id of the contact to be removed
    :param db: Session: Pass the database session to the repository
    :param current_user: User: Get the user that is currently logged in
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.remove(id, db)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.get(
    "/birthdays", response_model=List[ContactResponse], name="Upcoming Birthdays",  dependencies=[Depends(allowed_operation_get)]
)
async def get_birthdays(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    The get_birthdays function returns a list of contacts with birthdays in the next 7 days.

    :param db: Session: Pass the database connection to the repository layer
    :param current_user: User: Get the current user from the auth_service
    :return: A list of birthdays for the next 7 days
    :doc-author: Trelent
    """
    today = date.today()
    end_date = today + timedelta(days=7)
    birthdays = await repository_contacts.get_birthdays(today, end_date, db)
    if birthdays is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return birthdays
