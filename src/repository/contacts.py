from datetime import date, timedelta

from sqlalchemy.orm import Session
# from .src.database.models import  Contact
from src.database.models import Contact
from src.schemas import ContactBase
# from .src.schemas import ContactBase

# need to add "skip limit"


async def get_contacts(db: Session):
    """
    The get_contacts function returns a list of all contacts in the database.


    :param db: Session: Pass a database session to the function
    :return: A list of all contacts in the database
    :doc-author: Trelent
    """
    contacts = db.query(Contact).all()
    return contacts


async def get_contact_by_id(id: int, db: Session):
    """
    The get_contact_by_id function takes in an id and a database session,
        then returns the contact with that id.

    :param id: int: Specify the id of the contact that we want to retrieve
    :param db: Session: Pass the database session to the function
    :return: A contact object
    :doc-author: Trelent
    """
    contact = db.query(Contact).filter_by(id=id).first()
    return contact


async def get_contact_by_email(email: str, db: Session):
    """
    The get_contact_by_email function takes in an email address and a database session.
    It then queries the database for a contact with that email address, returning it if found.
    :param email: str: Filter the database query by email
    :param db: Session: Pass the database session to the function
    :return: A contact object
    :doc-author: Trelent
    """
    contact = db.query(Contact).filter_by(email=email).first()
    return contact


async def create(body: ContactBase, db: Session):
    """
    The create function creates a new contact in the database.
        Args:
            body (ContactBase): The information for the new contact.

    :param body: ContactBase: Get the data from the request body
    :param db: Session: Access the database
    :return: A contact object
    :doc-author: Trelent
    """
    contact = Contact(**body.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def update(id: int, body: ContactBase, db: Session):
    """
    The update function updates a contact in the database.
        Args:
            id (int): The ID of the contact to update.
            body (ContactBase): The updated information for the contact.

    :param id: int: Identify the contact to be deleted
    :param body: ContactBase: Access the json body of the request
    :param db: Session: Access the database
    :return: The updated contact
    :doc-author: Trelent
    """
    contact = await get_contact_by_id(id, db)
    if contact:
        contact.email = body.email
        contact.additional_data = body.additional_data
        contact.birth_date = body.birth_date
        db.commit()
    return contact


async def remove(id: int, db: Session):
    """
    The remove function removes a contact from the database.
    :param id: int: Specify the id of the contact to be deleted
    :param db: Session: Access the database
    :return: The contact that was deleted
    :doc-author: Trelent
    """
    contact = await get_contact_by_id(id, db)
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def get_birthdays(start_date: date, end_date: date, db: Session):
    """
    The get_birthdays function returns a list of contacts whose birthdays fall between the start_date and end_date.
    :param start_date: date: Specify the start date of the range to search for birthdays
    :param end_date: date: Specify the end date of the range
    :param db: Session: Pass the database session to the function
    :return: A list of contacts whose birthdays are between the start and end dates
    :doc-author: Trelent
    """
    birthdays = (
        db.query(Contact)
        .filter(Contact.birth_date >= start_date, Contact.birth_date <= end_date)
        .all()
    )
    return birthdays


async def search_contacts_by_last_name(last_name: str, db: Session):
    """
    The search_contacts_by_last_name function searches the database for contacts with a given last name.
    :param last_name: str: Specify the last name of the contact to search for
    :param db: Session: Pass in the database session
    :return: A list of contacts that match the last name provided
    :doc-author: Trelent
    """
    contacts = db.query(Contact).filter_by(last_name=last_name).all()
    return contacts


async def search_contacts_by_first_name(first_name: str, db: Session):
    """
    The search_contacts_by_first_name function searches the database for contacts with a given first name.
        Args:
            first_name (str): The first name of the contact to search for.
            db (Session): A session object that is used to query the database.
    :param first_name: str: Specify the first name of the contact we want to find
    :param db: Session: Pass the database session to the function
    :return: A list of contact objects
    :doc-author: Trelent
    """
    contacts = db.query(Contact).filter_by(first_name=first_name).all()
    return contacts


async def search_contact_by_email(email: str, db: Session):
    """
    The search_contact_by_email function searches the database for a contact with the given email.
    :param email: str: Pass in the email address to search for
    :param db: Session: Pass the database session to the function
    :return: A list of contacts with the specified email
    :doc-author: Trelent
    """
    contact = db.query(Contact).filter_by(email=email).all()
    return contact
