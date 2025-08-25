import logging
import pymongo
import bson
from django.conf import settings
from bson.objectid import ObjectId
from pymongo.errors import InvalidId


logger = logging.getLogger("django")


class MongoDB:
    def __init__(self):
        self._client = pymongo.MongoClient(settings.MONGODB["host"],
                                           settings.MONGODB["port"])
        self._db = self._client.bible

    def troparion_add(self, doc):
        self._db.troparion.insert_one(doc)

    def get_troparions(self, search_str):
        search_str = search_str.replace(".", " ")
        rgs = []
        for rg in search_str.split(" "):
            if len(rg) < 3:
                continue
            _ptr = bson.regex.Regex(rg[:-1], "i")
            rgs.append(_ptr)
        for doc in self._db.troparion.find({"title": {
                                                "$in": rgs,
                                           }}):
            yield doc

    def get_tropar_by_id(self, pk):
        try:
            return self._db.troparion.find_one({"_id": ObjectId(pk)})
        except InvalidId:
            raise ValueError


MongoDBClient = MongoDB()

