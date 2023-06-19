import mongoengine

class Material(mongoengine.EmbeddedDocument):
    name = mongoengine.StringField(required=True)
    available = mongoengine.BooleanField(default=True)
    price = mongoengine.IntField(required=True)
    reviews = mongoengine.ListField(mongoengine.DictField)
    rating = mongoengine.IntField(default=2)
    meta = {'allow_inheritance': True}

    @classmethod
    def append(cls, dct):
        materials = [cls(**(eq)) for eq in dct['append']]
        loc = dct['username'].locations.filter(**(dct['filter'])).first()
        print(loc, loc.to_mongo())
        [loc.items.append(mt) for mt in materials]
        dct['username'].save()

