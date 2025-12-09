import shelve
from .base import BaseRatings


class Ratings(BaseRatings):
    def __init__(self, file_path="ratings"):
        self.file_path = file_path

    def get(self, item_id):
        with shelve.open(self.file_path) as db:
            return db.get(item_id, 0)

    def inc(self, item_id,
            amount=1,):
        with shelve.open(self.file_path, writeback=True) as db:
            db[item_id] = db.get(item_id, 0) + amount

    def dec(self, item_id,
            amount=1,):
        with shelve.open(self.file_path, writeback=True) as db:
            db[item_id] = db.get(item_id, 0) - amount
