import os

# Create data directory if it doesn't exist
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

ADDRESS_BOOK_PATH = os.path.join(DATA_DIR, "addressbook.json")
NOTE_BOOK_PATH = os.path.join(DATA_DIR, "notebook.json")