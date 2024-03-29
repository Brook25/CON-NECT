#!/usr/bin/env python3
import mongoengine
from .equipments import Equipment
from .materials import Material


class MLocation(mongoengine.EmbeddedDocument):
    """matetial location document schema"""
    name = mongoengine.StringField(required=True)
    city = mongoengine.StringField(required=True)
    sub_city = mongoengine.StringField(required=True)
    items = mongoengine.EmbeddedDocumentListField(Material)
    meta = {'allow_inheritance': True }

    @classmethod
    def append(cls, dct):
        """class method to embed new location along with
           equipment or material embedded documents
           to an existing user document.
        """
        coll = Equipment if dct['coll'][0] == "E" else Material
        items = [coll(**(it)) for it in dct['append']]
        dct['items'] = items
        loc = cls(**dct['filter'])
        dct['user'].locations.append(loc)
        dct['user'].save()
        return items


class ELocation(MLocation):
    items = mongoengine.EmbeddedDocumentListField(Equipment)
