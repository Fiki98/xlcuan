import json
import os

class FamilyBookmark:
    _instance_ = None
    _initialized_ = False
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance_:
            cls._instance_ = super().__new__(cls)
        return cls._instance_

    def __init__(self, filename="family-bookmarks.json"):
        if not self._initialized_:
            self.filename = filename
            self.bookmarks = self.load_bookmarks()
            self._initialized_ = True

    def load_bookmarks(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def save_bookmarks(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.bookmarks, f, indent=2)

    def add_bookmark(self, family_code: str, family_name: str):
        if any(bm['family_code'] == family_code for bm in self.bookmarks):
            return False  # Already exists
        self.bookmarks.append({"family_code": family_code, "family_name": family_name})
        self.save_bookmarks()
        return True

    def remove_bookmark(self, family_code: str):
        initial_len = len(self.bookmarks)
        self.bookmarks = [bm for bm in self.bookmarks if bm['family_code'] != family_code]
        if len(self.bookmarks) < initial_len:
            self.save_bookmarks()
            return True
        return False

    def get_bookmarks(self):
        return self.bookmarks

FamilyBookmarkInstance = FamilyBookmark()