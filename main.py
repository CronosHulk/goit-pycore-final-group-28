# -*- coding: utf-8 -*-
import json
import functools
import sys

from config import DATA_FILE
from notes import Note, NoteBook
from models import AddressBook, Record


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
        "Email:\n"
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


def main():
    # Встановлюємо UTF-8 кодування для введення/виведення
    if sys.platform.startswith('win'):
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')

    book, notebook = load_data()

    greet = "Welcome to the assistant bot! Enter help to see commands"
    command_map = {
        "hello": lambda *_: greet,
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


if __name__ == "__main__":
    main()
