from collections import UserDict
from datetime import datetime, timedelta
import json
import functools

from config import ADDRESS_BOOK_PATH, NOTE_BOOK_PATH
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

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def add_birthday(self, birthday):
        if isinstance(birthday, str):
            self.birthday = Birthday(birthday)
        elif isinstance(birthday, Birthday):
            self.birthday = birthday

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

    def __str__(self):
        phones = f"phones: {'; '.join(p.value for p in self.phones)}"
        birthday_info = ""
        if self.birthday:
            birthday_str = self.birthday.value.strftime('%d.%m.%Y')
            birthday_info = f", birthday: {birthday_str}"
        return f"Contact name: {self.name.value}, {phones}{birthday_info}"

    def to_dict(self):
        return {
            "name": self.name.value,
            "phones": [p.value for p in self.phones],
            "birthday": self.birthday.to_dict() if self.birthday else None
        }

    @classmethod
    def from_dict(cls, data):
        record = cls(data["name"])
        for phone_number in data["phones"]:
            record.add_phone(phone_number)
        if data["birthday"]:
            record.add_birthday(Birthday.from_dict(data["birthday"]))
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
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


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


def birthdays(_, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays in the next week."

    result = "Upcoming birthdays:\n"
    for birthday_info in upcoming:
        congrats_date = birthday_info['congratulation_date']
        result += f"Congratulate {birthday_info['name']} on {congrats_date}\n"
    return result.strip()


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
    with open(ADDRESS_BOOK_PATH, "w") as f:
        json.dump(book.to_dict(), f, indent=4)
    with open(NOTE_BOOK_PATH, "w") as f:
        json.dump(notebook.to_dict(), f, indent=4)


def load_data():
    try:
        with open(ADDRESS_BOOK_PATH, "r") as f:
            book_data = json.load(f)
            book = AddressBook.from_dict(book_data)
    except (FileNotFoundError, json.JSONDecodeError):
        book = AddressBook()

    try:
        with open(NOTE_BOOK_PATH, "r") as f:
            notebook_data = json.load(f)
            notebook = NoteBook.from_dict(notebook_data)
    except (FileNotFoundError, json.JSONDecodeError):
        notebook = NoteBook()
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
    }

    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        if not user_input:
            continue
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book, notebook)
            break
        elif command in command_map:
            print(command_map[command](args, book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
