from collections import UserDict
from datetime import datetime, timedelta
import pickle
import functools


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


def input_error(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except AttributeError:
            return "Contact not found."
        except IndexError:
            return "Give me name and phone please."
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

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def main():
    book = load_data()

    command_map = {
        "hello": lambda *_: "How can I help you?",
        "add": add_contact,
        "change": change_contact,
        "phone": show_phone,
        "all": lambda args, book: show_all(args, book),
        "add-birthday": add_birthday,
        "show-birthday": show_birthday,
        "birthdays": lambda args, book: birthdays(args, book),
    }

    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        if not user_input:
            continue
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)
            
            break
        elif command in command_map:
            print(command_map[command](args, book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
