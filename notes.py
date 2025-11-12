from datetime import datetime
from collections import UserDict
import json


class Note:
    def __init__(self, text, tags=None):
        words = text.split()
        self.tags = [word for word in words if word.startswith('#')]
        self.text = ' '.join([word for word in words if not word.startswith('#')])
        self.id = None
        self.created = datetime.now()

    def _extract_tags(self, text):
        return [word.strip() for word in text.split() if word.startswith('#')]

    def __str__(self):
        tags_str = ', '.join(self.tags) if self.tags else "No tags"
        return (f"ID: {self.id}\n"
                f"Date: {self.created.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Tags: {tags_str}\n"
                f"Text: {self.text}\n")

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "created": self.created.strftime('%Y-%m-%d %H:%M:%S'),
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data):
        note = cls(data["text"])
        note.id = data["id"]
        note.created = datetime.strptime(data["created"], '%Y-%m-%d %H:%M:%S')
        note.tags = data["tags"]
        return note


class NoteBook(UserDict):
    def __init__(self):
        super().__init__()
        self.next_id = 1

    def add_note(self, note: Note):
        note.id = self.next_id
        self.data[self.next_id] = note
        self.next_id += 1
        return f"Note with ID {note.id} added."

    def find_notes(self, search_text):
        found_notes = []
        search_text = search_text.lower()
        for note in self.data.values():
            if search_text in note.text.lower() \
               or any(search_text in tag.lower() for tag in note.tags):
                found_notes.append(note)
        return found_notes

    def edit_note(self, note_id, new_text):
        if note_id in self.data:
            self.data[note_id].text = new_text
            self.data[note_id].tags = self.data[note_id]._extract_tags(new_text)
            return f"Note with ID {note_id} updated."
        raise KeyError(f"Note with ID {note_id} not found.")

    def delete_note(self, note_id):
        if note_id in self.data:
            del self.data[note_id]
            return f"Note with ID {note_id} deleted."
        raise KeyError(f"Note with ID {note_id} not found.")

    def to_dict(self):
        return {
            "next_id": self.next_id,
            "notes": {str(k): v.to_dict() for k, v in self.data.items()}
        }

    @classmethod
    def from_dict(cls, data):
        notebook = cls()
        notebook.next_id = data.get("next_id", 1)
        notes_data = data.get("notes", {})
        for note_id_str, note_dict in notes_data.items():
            note = Note.from_dict(note_dict)
            notebook.data[int(note_id_str)] = note
        return notebook