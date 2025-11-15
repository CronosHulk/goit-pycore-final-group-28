from collections import UserDict
from datetime import datetime, timedelta
import json
import functools
import re # для первірки формату імейлу

from config import DATA_FILE
from notes import Note, NoteBook


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not (
            isinstance(value, str) and value.isdigit() and len(value) == 10
        ):
            raise ValueError(
                "Phone number must be a 10-digit string of numbers."
            )
        super().__init__(value)

#додано класс email
class Email(Field):
    def __init__(self, value):
        pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern,value):
            raise ValueError("Invalid email format")
        super().__init__(value)

#додано класс Address
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
    def __init__(self, name, email=None, address=None):
        self.name = Name(name)
        self.phones = []
        self.birthday = None
        self.email = email
        self.address = address

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def add_birthday(self, birthday):
        if isinstance(birthday, str):
            self.birthday = Birthday(birthday)
        elif isinstance(birthday, Birthday):
            self.birthday = birthday

    #метод для додавання імейлу
    def add_email(self,email): 
        if isinstance(email,str):
            self.email= Email (email)
        elif isinstance (email,Email):
            self.email=email
    
    #метод для додавання адресси
    def add_address (self, address):
        if isinstance(address,str):
            self.address=address
        elif isinstance(address,Address):
            self.address=address


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
            raise ValueError(
                f"Phone number {old_phone_number} not found."
            )

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None
    
    def set_email(self, email_str):
        if email_str and isinstance(email_str, str) and "@" in email_str:
            self.email = email_str
        else:
            raise ValueError("Invalid email provided.")

    def set_address(self, address_str):
        if address_str and isinstance(address_str, str):
            self.address = address_str
        else:
            raise ValueError("Invalid address provided.")

    def edit_email(self, new_email):
        self.set_email(new_email)

    def edit_address(self, new_address):
        self.set_address(new_address)

    def __str__(self):
        phones = f"phones: {'; '.join(p.value for p in self.phones)}"
        birthday_info = ""
        if self.birthday:
            birthday_str = self.birthday.value.strftime('%d.%m.%Y')
            birthday_info = f", birthday: {birthday_str}"
        email_info = f", email: {self.email.value}" if self.email else "" #додала email 
        address_info = f", address: {self.address.value}" if self.address else "" #додала адресу
        return f"Contact name: {self.name.value}, {phones}{birthday_info}, {email_info}, {address_info}"

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
        record = cls(data["name"], email=data.get("email"), address=data.get("address"))
        for phone_number in data.get("phones", []):
            record.add_phone(phone_number)
        if data.get("birthday"):
            record.add_birthday(Birthday.from_dict(data["birthday"]))
        if data.get("email"): #додала імейл в класс
            record.add_email(Email(data["email"])) 
        if data.get("address"): #додала адрессу в класс
            record.add_address(Address(data["address"]))
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

    def to_dict(self):
        return {name: record.to_dict() for name, record in self.data.items()}

    @classmethod
    def from_dict(cls, data):
        book = cls()
        for name, record_dict in data.items():
            record = Record.from_dict(record_dict)
            book.add_record(record)
        return book
    
    def search(self, query):
        q = str(query).lower()
        results = []
        for rec in self.data.values():
            if q in rec.name.value.lower():
                results.append(rec)
                continue
            if rec.email and q in rec.email.lower():
                results.append(rec)
                continue
            if rec.address and q in rec.address.lower():
                results.append(rec)
                continue
            for p in rec.phones:
                if q in p.value:
                    results.append(rec)
                    break
        return results



def input_error(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact or Note not found."
        except AttributeError:
            return "Contact not found."
        except IndexError:
            return "Invalid number of arguments."
    return inner


def parse_input(user_input):
    parts = user_input.split()
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args


@input_error
def add_contact(args, book: AddressBook):
    if not args:
        raise IndexError("Provide at least a name.")
    name = args[0]
    phone = None
    email = None
    address = None
    rest = args[1:]
    addr_parts = []
    for token in rest:
        if not phone and token.isdigit() and len(token) == 10:
            phone = token
            continue
        if not email and "@" in token and "." in token:
            email = token
            continue
        addr_parts.append(token)
    if addr_parts:
        address = " ".join(addr_parts) if addr_parts else None
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    if email:
        record.set_email(email)
    if address:
        record.set_address(address)
    return message


@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise IndexError("Not enough arguments for change.")
    name = args[0]
    field = args[1].lower()
    rec = book.find(name)
    if field == "phone":
        if len(args) < 4:
            raise IndexError("Phone change requires old and new numbers.")
        old_phone = args[2]
        new_phone = args[3]
        rec.edit_phone(old_phone, new_phone)
        return "Phone updated."
    elif field == "email":
        new_email = args[2]
        rec.edit_email(new_email)
        return "Email updated."
    elif field == "address":
        new_address = " ".join(args[2:])
        rec.edit_address(new_address)
        return "Address updated."
    else:
        raise ValueError("Unknown field. Use 'phone', 'email' or 'address'.")


@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    return '; '.join(p.value for p in record.phones)


def show_all(_, book: AddressBook):
    if not book.data:
        return "No contacts found."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record.birthday:
        return record.birthday.value.strftime('%d.%m.%Y')
    return "Birthday not set for this contact."


@input_error
def birthdays(args, book: AddressBook):
    days = 7
    if args:
        days_str = args[0]
        try:
            days = int(days_str)
        except ValueError:
            raise ValueError("Days must be a positive integer.")
        if days <= 0:
            raise ValueError("Days must be a positive integer.")

    upcoming = book.get_upcoming_birthdays(days=days)

    if not upcoming:
        return f"No upcoming birthdays in the next {days} days."

    result_lines = [f"Upcoming birthdays in the next {days} days:"]
    for birthday_info in upcoming:
        congrats_date = birthday_info["congratulation_date"]
        result_lines.append(
            f"Congratulate {birthday_info['name']} on {congrats_date}"
        )
    return "\n".join(result_lines)

@input_error
def add_email(args, book: AddressBook):        
    name, email, *_ = args
    rec = book.find(name)
    rec.set_email(email)
    return "Email set."

@input_error
def add_address(args, book: AddressBook):
    if len(args) < 2:
        raise IndexError("Provide name and address.")
    name = args[0]
    address = " ".join(args[1:])
    rec = book.find(name)
    rec.set_address(address)
    return "Address set."

@input_error
def delete_contact(args, book: AddressBook):
    name, *_ = args
    book.delete(name)
    return "Contact deleted."

@input_error
def find_contact(args, book: AddressBook):
    if not args:
        raise IndexError("Provide search query.")
    query = " ".join(args)
    results = book.search(query)
    if not results:
        return "No contacts found."
    return "\n".join(str(r) for r in results)


@input_error
def add_note(args, notebook: NoteBook):
    text = ' '.join(args)
    if not text:
        raise IndexError("Please provide text for the note.")
    note = Note(text)
    return notebook.add_note(note)


def show_notes(_, notebook: NoteBook):
    if not notebook.data:
        return "No notes found."
    return "\n".join(str(note) for note in notebook.data.values())


@input_error
def find_notes(args, notebook: NoteBook):
    search_text = ' '.join(args)
    if not search_text:
        raise IndexError("Please provide search text.")
    found_notes = notebook.find_notes(search_text)
    if not found_notes:
        return "No notes found matching your query."
    return "\n".join(str(note) for note in found_notes)


@input_error
def edit_note(args, notebook: NoteBook):
    if len(args) < 2:
        raise IndexError("Please provide note ID and new text.")
    note_id_str, *new_text_parts = args
    try:
        note_id = int(note_id_str)
    except ValueError:
        return "Note ID must be a number."
    new_text = ' '.join(new_text_parts)
    if not new_text:
        raise IndexError("Please provide new text for the note.")
    return notebook.edit_note(note_id, new_text)


@input_error
def delete_note(args, notebook: NoteBook):
    if not args:
        raise IndexError("Please provide a note ID.")
    note_id_str, *_ = args
    try:
        note_id = int(note_id_str)
    except ValueError:
        return "Note ID must be a number."
    return notebook.delete_note(note_id)

def save_data(book, notebook):
    data = {
        "contacts": book.to_dict(),
        "notes": notebook.to_dict(),
    }

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # если файла нет или он битый — создаём пустые структуры
        return AddressBook(), NoteBook()

    book_data = data.get("contacts", {})
    notes_data = data.get("notes", {})

    book = AddressBook.from_dict(book_data)
    notebook = NoteBook.from_dict(notes_data)

    return book, notebook

def main():
    book, notebook = load_data()

    command_map = {
        "hello": lambda *_: "How can I help you?",
        "add": add_contact,
        "change": change_contact,
        "phone": show_phone,
        "all": lambda args, book: show_all(args, book),
        "add-birthday": add_birthday,
        "show-birthday": show_birthday,
        "birthdays": lambda args, book: birthdays(args, book),
        "add-note": lambda args, book: add_note(args, notebook),
        "show-notes": lambda args, book: show_notes(args, notebook),
        "find-notes": lambda args, book: find_notes(args, notebook),
        "edit-note": lambda args, book: edit_note(args, notebook),
        "delete-note": lambda args, book: delete_note(args, notebook),
        "help": lambda args, book: help_command(),
        "add-email": lambda args, book: add_email(args, book),
        "add-address": lambda args, book: add_address(args, book),
        "delete-contact": lambda args, book: delete_contact(args, book),
        "find-contact": lambda args, book: find_contact(args, book),
    }

    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        if not user_input:
            continue
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book, notebook)
            break
        elif command in command_map:
            print(command_map[command](args, book))
        else:
            print("Invalid command.")

def help_command(*args):
    return (
        "Доступні команди:\n"
        "\n"
        "Контакти:\n"
        "  add <ім'я> [телефон] [email] [address] - Додати контакт або доповнити\n"
        "  change <ім'я> phone <старий> <новий>   - Змінити телефон\n"
        "  delete-contact <ім'я>                  - Видалити контакт\n"
        "  find-contact <запит>                   - Пошук по імені/тел/емейл/адресі\n"
        "  phone <ім'я>                           - Показати телефони контакту\n"
        "  all                                    - Показати всі контакти\n"
        "\n"
        "email:\n"
         "  add-email <ім'я> <email>               - Додати email\n"
         "  change <ім'я> email <new_email>        - Змінити email\n"

         "\n"
        "Адреси:\n"
        "  add-address <ім'я> <address>           - Додати адресу\n"
        "  change <ім'я> address <new address>    - Змінити адресу\n"

        "\n"
        "Дні народження:\n"
        "  add-birthday <ім'я> <дата>             - Додати день народження\n"
        "  show-birthday <ім'я>                   - Показати день народження\n"
        "  birthdays [днів]                       - Показати дні народження в найближчі N днів\n"
        "\n"
        "Нотатки:\n"
        "  add-note <текст>                       - Додати нотатку\n"
        "  show-notes                              - Показати всі нотатки\n"
        "  find-notes <запит>                      - Пошук нотаток\n"
        "  edit-note <ID> <новий текст>           - Редагувати нотатку\n"
        "  delete-note <ID>                        - Видалити нотатку\n"
        "\n"
        "Системні:\n"
        "  help                                   - Показати це меню\n"
        "  exit / close                           - Вийти з програми\n"
    )


if __name__ == "__main__":
    main()
