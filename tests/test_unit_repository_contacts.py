from datetime import date, timedelta
import sys
import os
import unittest
from unittest.mock import MagicMock
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import select, text, extract, desc

# hw_path: str = str(Path(__file__).resolve().parent.parent.joinpath("hw14"))
# sys.path.append(hw_path)
# # print(f"{hw_path=}", sys.path)
# os.environ["PYTHONPATH"] += os.pathsep + hw_path
# # print(f'{os.environ["PYTHONPATH"]=}')

from src.database.models import Contact, User
from src.schemas import ContactBase
# from hw14.src.database.models import User, Contact
# from hw14.src.shemas import ContactModel, ContactFavoriteModel
# from import UserModel, UserResponse, UserDetailResponse, NewUserResponse

from src.repository.contacts import (
    get_contacts,
    get_contact_by_id,
    get_contact_by_email,
    create,
    update,
    remove,
    get_birthdays,
    search_contact_by_email,
    search_contacts_by_first_name,
    search_contacts_by_last_name
)


class TestContactsRepository (unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, email="some@email.ua")

    async def test_get_contacts(self):
        contacts = [Contact(), Contact()]
        self.session.query().all.return_value = contacts
        result = await get_contacts(self.session)
        self.assertEqual(result, contacts)

    async def test_get_contact_found_by_id(self):
        contact = Contact(id=1, first_name='John', last_name='Doe', email='john@example.com')
        query_mock = MagicMock()
        query_mock.filter_by().first.return_value = contact
        self.session.query.return_value = query_mock

        result = await get_contact_by_id(id=1, db=self.session)
        self.assertEqual(result, contact)


    async def test_get_contact_found_by_email(self):
        expected_contact = Contact(first_name='John', last_name='Doe', email='john@example.com')
        query_mock = MagicMock()
        query_mock.filter_by().first.return_value = expected_contact
        self.session.query.return_value = query_mock

        result = await get_contact_by_email(email="as@ee.ua", db=self.session)
        self.assertEqual(result, expected_contact)

    async def test_get_contact_not_found_by_id(self):
        contact = Contact(id=1, first_name='John', last_name='Doe', email='john@example.com')
        query_mock = MagicMock()
        query_mock.filter_by.return_value.first.return_value = contact
        self.session.query().filter_by().first.return_value = None
        result = await get_contact_by_id(id=1, db=self.session)
        self.assertIsNone(result)

    async def test_get_contact_not_found_by_email(self):
        expected_contact = Contact(first_name='John', last_name='Doe', email='john@example.com')
        query_mock = MagicMock()
        query_mock.filter_by().first.return_value = expected_contact
        self.session.query().filter_by().first.return_value = None
        result = await get_contact_by_email(email="as@ee.ua", db=self.session)  # type: ignore
        self.assertIsNone(result)

    async def test_create_contact(self):
        body = ContactBase(
            id= "1",
            first_name="test1",
            last_name="test2",
            email="aa@uu.uu",
            phone_number="+380 (44) 1234567",
            birth_date="2023-11-11",
            additional_data = "test",
            created_at = "2023-11-21 16:53:03.053",
            updated_at = "2023-11-21 16:53:03.053"
        )
        result = await create(body=body, db=self.session)  # type: ignore
        self.assertEqual(result.id, body.id)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone_number, body.phone_number)
        self.assertEqual(result.birth_date, body.birth_date)
        self.assertEqual(result.additional_data, body.additional_data)
        # self.assertTrue(hasattr(result, "id"))
        # self.assertEqual(result.user_id, self.user.id)

    async def test_remove_contact_found(self):
        contact = Contact()
        self.session.query().filter_by().first.return_value = contact
        result = await remove(id=1, db=self.session)  # type: ignore
        self.assertEqual(result, contact)

    async def test_remove_contact_not_found(self):
        self.session.query().filter_by().first.return_value = None
        result = await remove(id=1, db=self.session) # type: ignore
        self.assertIsNone(result)

    async def test_update_contact_found(self):
        contact = Contact()
        body=ContactBase(
            id="1",
            first_name="test1",
            last_name="test2",
            email="aa@uu.uu",
            phone_number="+380 (44) 1234567",
            birth_date="2023-11-11",
            additional_data="test",
            created_at="2023-11-21 16:53:03.053",
            updated_at="2023-11-21 16:53:03.053"
          )

        self.session.query().filter_by().first.return_value = contact
        self.session.commit.return_value = None
        result = await update(id= body.id, body=body, db=self.session)  # type: ignore
        self.assertEqual(result, contact)

    async def test_update_contact_not_found(self):
        body = ContactBase(
            id="1",
            first_name="test1",
            last_name="test2",
            email="aa@uu.uu",
            phone_number="+380 (44) 1234567",
            birth_date="2023-11-11",
            additional_data="test",
            created_at="2023-11-21 16:53:03.053",
            updated_at="2023-11-21 16:53:03.053"
        )
        self.session.query().filter_by().first.return_value = None
        self.session.commit.return_value = None
        result = await update(id=1, body=body, db=self.session)  # type: ignore
        self.assertIsNone(result)

    async def test_get_contact_search_birthday(self):
        date_now = date.today()
        start_date = date_now
        end_date = date_now + timedelta(days=7)
        contacts = [Contact(), Contact(), Contact(), Contact()]

        query_mock = MagicMock()
        query_mock.filter().all.return_value = contacts
        self.session.query.return_value = query_mock

        result = await get_birthdays(start_date, end_date, db=self.session)
        self.assertEqual(result, contacts)

    async def test_search_contacts_by_first_name(self):
        first_name = 'Vasyl'
        contacts = [Contact(), Contact(), Contact(), Contact()]
        query_mock = MagicMock()
        query_mock.filter_by(first_name=first_name).all.return_value = contacts
        self.session.query.return_value = query_mock

        result = await search_contacts_by_first_name(first_name=first_name, db=self.session)
        self.assertEqual(result, contacts)


    async def test_search_contacts_by_last_name(self):
        last_name = 'Vasyl'
        contacts = [Contact(), Contact(), Contact(), Contact()]
        query_mock = MagicMock()
        query_mock.filter_by(last_name=last_name).all.return_value = contacts
        self.session.query.return_value = query_mock

        result = await search_contacts_by_last_name(last_name=last_name, db=self.session)
        self.assertEqual(result, contacts)

    async def test__search_contact_by_email(self):
        email = 'john@example.com'
        contacts = [Contact(), Contact(), Contact(), Contact()]
        # contact = Contact(email=email)
        query_mock = MagicMock()
        query_mock.filter_by(email=email).all.return_value = contacts
        self.session.query.return_value = query_mock

        result = await search_contact_by_email(email=email, db=self.session)
        self.assertEqual(result, contacts)





if __name__ == "__main__":
    unittest.main()
