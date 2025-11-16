from collections import UserDict
from datetime import datetime, timedelta
import re


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not (isinstance(value, str) and value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must be a 10-digit string of numbers.")
        super().__init__(value)


class Email(Field):
    def __init__(self, value):
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern, value):
            raise ValueError("Invalid email format")
        super().__init__(value)


class Address(Field):
    def __init__(self, value):
        if not value or not isinstance(value, str):
            raise ValueError("Address must be a non-empty string")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def to_dict(self):
        return self.value.strftime("%d.%m.%Y")

    @classmethod
    def from_dict(cls, value_str):
        return cls(value_str)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None
        self.email = None  # Буде Email об'єкт або None
        self.address = None  # Буде Address об'єкт або None

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def add_birthday(self, birthday):
        if isinstance(birthday, str):
            self.birthday = Birthday(birthday)
        elif isinstance(birthday, Birthday):
            self.birthday = birthday

    def set_email(self, email_str):
        """Встановити email (створює Email об'єкт)"""
        if email_str:
            self.email = Email(email_str)

    def set_address(self, address_str):
        """Встановити адресу (створює Address об'єкт)"""
        if address_str:
            self.address = Address(address_str)

    def edit_email(self, new_email):
        """Змінити email"""
        self.set_email(new_email)

    def edit_address(self, new_address):
        """Змінити адресу"""
        self.set_address(new_address)

    def remove_phone(self, phone_number):
        phone_to_remove = self.find_phone(phone_number)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)
        else:
            raise ValueError(f"Phone number {phone_number} not found.")

    def edit_phone(self, old_phone_number, new_phone_number):
        phone_to_edit = self.find_phone(old_phone_number)
        if phone_to_edit:
            phone_to_edit.value = Phone(new_phone_number).value
        else:
            raise ValueError(f"Phone number {old_phone_number} not found.")

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def __str__(self):
        phones = f"phones: {'; '.join(p.value for p in self.phones)}" if self.phones else "phones: none"

        birthday_info = ""
        if self.birthday:
            birthday_str = self.birthday.value.strftime('%d.%m.%Y')
            birthday_info = f", birthday: {birthday_str}"

        email_info = f", email: {self.email.value}" if self.email else ""
        address_info = f", address: {self.address.value}" if self.address else ""

        return f"Contact name: {self.name.value}, {phones}{birthday_info}{email_info}{address_info}"

    def to_dict(self):
        return {
            "name": self.name.value,
            "phones": [p.value for p in self.phones],
            "birthday": self.birthday.to_dict() if self.birthday else None,
            "email": self.email.value if self.email else None,
            "address": self.address.value if self.address else None
        }

    @classmethod
    def from_dict(cls, data):
        record = cls(data["name"])

        for phone_number in data.get("phones", []):
            record.add_phone(phone_number)

        if data.get("birthday"):
            record.add_birthday(Birthday.from_dict(data["birthday"]))

        if data.get("email"):
            record.set_email(data["email"])

        if data.get("address"):
            record.set_address(data["address"])

        return record


class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self, days=7):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday:
                bday = record.birthday.value
                birthday_this_year = bday.replace(year=today.year)

                delta_days = (birthday_this_year - today).days

                if 0 <= delta_days <= days:
                    congratulation_date = birthday_this_year
                    if congratulation_date.weekday() >= 5:
                        days_to_monday = 7 - congratulation_date.weekday()
                        congratulation_date += timedelta(days=days_to_monday)

                    con_date_str = congratulation_date.strftime("%d.%m.%Y")
                    upcoming_birthdays.append(
                        {
                            "name": record.name.value,
                            "congratulation_date": con_date_str,
                        }
                    )
        return upcoming_birthdays

    def search(self, query):
        """Пошук контактів по імені, телефону, email, адресі"""
        q = str(query).lower()
        results = []

        for rec in self.data.values():
            # Пошук по імені
            if q in rec.name.value.lower():
                results.append(rec)
                continue

            # Пошук по email
            if rec.email and q in rec.email.value.lower():
                results.append(rec)
                continue

            # Пошук по адресі
            if rec.address and q in rec.address.value.lower():
                results.append(rec)
                continue

            # Пошук по телефонах
            for p in rec.phones:
                if q in p.value:
                    results.append(rec)
                    break

        return results

    def to_dict(self):
        return {name: record.to_dict() for name, record in self.data.items()}

    @classmethod
    def from_dict(cls, data):
        book = cls()
        for name, record_dict in data.items():
            record = Record.from_dict(record_dict)
            book.add_record(record)
        return book