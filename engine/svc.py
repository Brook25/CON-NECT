#!/usr/bin/env python3

import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta
from models.data.equipments import Equipment
from models.data.materials import Material
from models.data.Equipment_suppliers import EquipmentSuppliers
from models.data.material_suppliers import MaterialSuppliers
from models.data.locations import MLocation, ELocation
from models.data.users import User
from models.data.booking import Booking
from models.data.validation import ValidateItem, ValidateSupp
from models.data.places_equipments import PlacesEquipments
from mongoengine import connect
import mongoengine

classes = {'User': User, 'Equipment': Equipment, 'Material': Material, 'MaterialSuppliers': MaterialSuppliers, 'MLocation': MLocation, 'ELocation': ELocation, 'EquipmentSuppliers': EquipmentSuppliers, 'PlacesEqs': PlacesEquipments, 'ValSupp': ValidateSupp, 'ValItem': ValidateItem, 'Booking': Booking}


class DBEngine:
    __db = None

    def __init__(self):
        #self.__client = MongoClient()
        #self.__db = self.__client['my_db']
        mongoengine.connect(db='my_db', alias='cnn')
        #self.__db = mongoengine.get_db()



    def add_new(self, dct):
       classes[dct['coll']](**dct['docs']).save()

       '''if len(dct.keys()) > 1:
            print(dct)
            coll = self.__db[dct['coll']]
            doc_ids = coll.insert_many(dct['docs'])
            return doc_ids
       raise ValueError("collection name not provided or document name lacking")
       '''
    @staticmethod
    def equipment_count(*args):
        it_lst = list(set(map(lambda x: x['machine'], args[0])))
        if len(args) < 2:
            count = [0 for it in it_lst]
        else:
            count = list(map(lambda x: len(args[1].items.filter(machine=x)), it_lst))
        count_dct = dict(zip(it_lst, count))
        for it in args[0]:
           it['name'] += str(count_dct[it['machine']] + 1)
           count_dct[it['machine']] += 1

        

    def append_or_create(self, dct):
        coll = classes[dct['coll']]
        supp = coll.objects(username=dct['username']).first()
        if supp:
            dct['user'] = supp
            loc = supp.locations.filter(**(dct['filter'])).first()
            if loc:
                if dct['coll'][0] == "E":
                    self.equipment_count(dct['append'], loc)
                    Equipment.append(dct)
                    dct['item'] = 'equipment'
                else:
                    filter = [loc.items.filter(name=x['name']).first() for x in dct['append']]
                    names = [x['name'] for x in filter if x]
                    dct['append'] = [x for x in dct['append'] if x['name'] not in names]
                    Material.append(dct)
                    dct['item'] = 'material'
                dct['pending'] = True
                if dct['append']:
                    ValidateItem.append(dct)
                return [x['name'] for x in dct['append']]
            else:
                if dct['coll'][0] == "E":
                    self.equipment_count(dct['append'])
                    ELocation.append(dct)
                    dct['item'] = 'equipment'
                else:
                    MLocation.append(dct)
                    dct['item'] = 'material'
                dct['pending'] = True
                ValidateItem.append(dct)
                return [x['name'] for x in dct['append']]
        else:
            if dct['coll'][0] == "E":
                self.equipment_count(dct['append'])
                eq = [Equipment(**(eq)) for eq in dct['append']]
                loc = ELocation(name=dct['filter']['name'], city=dct['filter']['city'], sub_city=dct['filter']['sub_city'], items=eq)
                write_dct = {'username': dct['username'], 'locations': [loc], 'contact_info': dct['contact_info']}
                self.add_new({'coll': 'EquipmentSuppliers', 'docs': write_dct})
                dct['item'] = 'equipment'
            else:
                mt = [Material(**(eq)) for eq in dct['append']]
                loc = MLocation(name=dct['filter']['name'], city=dct['filter']['city'], sub_city=dct['filter']['sub_city'], items=mt)
                write_dct = {'username': dct['username'], 'locations': [loc], 'contact_info': dct['contact_info'] }
                self.add_new({'coll': 'MaterialSuppliers', 'docs': write_dct})
                dct['item'] = 'material'
            ValidateSupp(username=dct['username']).save()
            dct['pending'] = False
            ValidateItem.append(dct)
            return [x['name'] for x in dct['append']]
            
                


    def find(self, dct):
        coll = classes[dct['coll']]._get_collection()
        all_docs = []
        if len(dct) == 1:
            query = coll.find()
        if 'find' in dct:
            query = coll.find(dct['find'], dct['fields'])
        elif 'agg' in dct:
            query = coll.aggregate(dct['agg'])
        for doc in query:
            all_docs += [doc]
        return all_docs



    def delete(self, dct):
        coll = classes[dct['coll']]._get_collection()
        coll.delete_many(dct['row'])




    def update(self, dct):
        coll = classes[dct['coll']]._get_collection()
        row = dct['row']
        print(coll)
        update = dct['update1']
        if len(dct) < 4:
            coll.update_one(row, update, upsert=False)
        else:
            array_filters = dct['array_filters']
            print(row, update, array_filters)
            coll.update_one(row, update, array_filters=dct['array_filters'], upsert=False)

    
    def places_equipments(self, **kwargs):
        if not (kwargs.get('place') or kwargs.get('materials') or kwargs.get('equipments')):
            raise ValueError('No place, material or equipment key word found')
        my_db = MongoClient("localhost", 27017)['my_db']
        places_equipments = my_db['places_equipments']
        if kwargs.get('place'):
            if not kwargs.get('place').get('cities'):
                raise ValueError('cities not properly provided.')
            places = list(places_equipments.find({'cities': {"$exists": True}}))
            if not places:
                places_equipments.insert_one(kwargs.get('place'))
            else:
                for city in kwargs.get('place').get('cities'):
                    if city not in places['cities']:
                        places_equipments.update({'cities': {"$exists": True}}, {"$set": {city: kwargs['place'][city] }})
                    else:
                        for sub_city in kwargs['place']['cities'][city]:
                            places_equipments.update({'cities': {'$exists': True}}, {"$addToSet": {f'{city}.{sub_city}': kwargs['place']['cities'][city][sub_city]}})
                            
        if kwargs.get('materials'):
            places_equipments.update_one({'materials': {'$exists': True}}, {"$addToSet": {'materials': {"$each": kwargs.get('materials')} } }, upsert=True)
        else:
            places_equipments.update_one({'equipments': {'$exists': True}}, {"$addToSet": {'equipments': {"$each": kwargs.get('equipments')} } }, upsert=True)




    def feed_history(self, username):
        eq_history = self.find({'coll': 'User', 'agg': [{"$match": {"username": username}}, {"$unwind": "$equipment_bookings"}, {"$match": {"equipment_bookings.return_date": {"$gt": datetime.utcnow()} } }, {"$project": {"equipment_bookings": 1, "_id": 0} }] })
        eq_lst = []
        for dct in eq_history:
            if {'username': dct['equipment_bookings']['username'], 'location': dct['equipment_bookings']['location']} not in eq_lst:
                eq_lst += [{'username': dct['equipment_bookings']['username'], 'location': dct['equipment_bookings']['location']}]
        for item in eq_lst:
            item['name'] = []
            for eq in eq_history:
                if item['username'] == eq['equipment_bookings']['username'] and item['location'] == eq['equipment_bookings']['location']:
                    item['name'] += [eq['equipment_bookings']['name']]
        for eq in eq_lst:
            loc = eq['location'].split('/')
            self.update({'coll': 'EquipmentSuppliers','row': {'username': eq['username']}, 'update1':{"$set": {"locations.$[l].items.$[i].available": True}}, 'array_filters': [{'l.name': loc[0], 'l.sub_city': loc[1], 'l.city': loc[2]}, {'i.name': {'$in': eq['name']}}]})
        mt_history = self.find({'coll': 'User', 'agg': [{"$match": {"username": username}}, {"$unwind": "$material_bookings"}, {"$match": {"material_bookings.return_date": {"$gt": datetime.utcnow()} } }, {"$project": {"material_bookings": 1, "_id": 0} }] })
        self.update({'coll': 'User', 'row': {"username": username}, 'update1': {"$pull":  {"equipment_bookings": {"return_date": {"$gt": datetime.utcnow()} }, "material_bookings": {"return_date": {"$gt": datetime.utcnow()} } } } })
        self.update({'coll': 'EquipmentSuppliers', 'row': {"username": username}, 'update1': {"$pull": {"booked_equipments": {"return_date": {"$gt": datetime.utcnow() } } } } })
        self.update({'coll': 'MaterialSuppliers', 'row': {"username": username}, 'update1': {"$pull": {"booked_materials": {"return_date": {"$gt": datetime.utcnow() } } } } })
        print(eq_history)
        history = list(map(lambda x: x['equipment_bookings'], eq_history)) + list(map(lambda x: x['material_bookings'], mt_history))
        history = sorted(history, key=lambda x: x['date'])
        self.update({'coll': 'User', 'row': {'username': username},
            'update1': {'$push': {"history": {"$each": history} } } })


        #for doc in eq_history:
        #   print(doc)
        #mt_history = users.find({'coll': 'User', 'agg': [{"$unwind": "material_bookings"}, {"$match": {"material_bookings.date": {"$lt": new Date()} } }, {"$project": {"material_bookings": 1} }] })
        #history = [eq_history + mt_history].sort()
        # inert into history all the values
        #self.update({'coll': 'User', 'row': {"uername": username}, 'update1': {"$pull": {"equipment_bookings": {"equipmemt_bookings.returndate": {"$lt": new Date ()} } } } })
        #self.update({'coll': 'User', 'row': {"uername": username}, 'update1': {"$pull": {"equipment_bookings": {"equipmemt_bookings.returndate": {"$lt": new Date ()} } } } })









#dctj = { 'username': "James", "email": "james1234@gmail.com", "password": "james1234" }

#dctt = { 'username': "Tom", "email": "tom1234@gmail.com", "password": "tommy1234" }

#dctjn = { 'username': "John", "email": "john1234@gmail.com", "password": "john1234" }


#dct1 = {'username': 'Tom', 'locations': [{"name": "tor-hailoch", "city": "Addis", "sub_city": "Kolfe", 'items': [{"machine": "Mixer", "name": "Mixer1", "years_used": 6, "price": 500}, {"machine": "Vibrator", "name": "Vibrator1", "years_used": 4, "price": 1000}, {"machine": "Excavator", "name": "Excavator1", "years_used": 3, "price": 1500}]}]}




#db = DBEngine()


#book_date = datetime.utcnow()
#return_date =  book_date + timedelta(days=3)

#book_date = datetime.utcnow()
#return_date =  book_date + timedelta(days=5)

#print(book_date, return_date)


#print(x)


#val = EquipmentSuppliers.objects(username="John").first()
#val = val.locations.filter(name="Tor-hailoch", city="Addis").first()
#val = val.equipments.filter(machine="Mixer")
#for v in val:
#    print(v.to_mongo())



#dct = {'machine': 'Mixer', 'name': "Mixer5", 'years_used': 5, 'price': 300}
#dct1 = {'machine': 'Mixer', 'name': "Mixer6", 'years_used': 5, 'price': 300}
#db.append({'coll': 'EquipmentSuppliers', 'username': 'John', 'filter': {'name': 'Tor-hailoch', 'city': 'Addis', 'sub_city': 'Kolfe'}, 'append': [dct, dct1]})
#db.append()


#db.update({'coll': 'User', 'row': {'username': "John"}, 'update1': {"$push": {"equipment_bookings": { "$each": [{"username": "James", "date": book_date, "name": "Mixer1", "return_date": return_date }, {"username": "Jammie", "date": book_date, "name": "Mixer1", "return_date": return_date} ] } } } })

#val = db.feed_history("John")

#client = MongoClient()
#db = client['my_db']
#db.users.update_one({"history": []}, {"$push": {"history": val}})
#print("done")

#db.delete({'coll': 'User', 'row': {}})
#db.add_new({'coll': User, 'docs': dctt})
#db.add_new({'coll': User, 'docs': dctj})
#db.add_new({'coll': User, 'docs': dctjn})

#print(db.find({'coll': 'User'}))

#db.add_new({'coll': 'EquipmentSuppliers', 'docs': dct1})
#db.update({'coll': EquipmentSuppliers, 'query': {'username': 'Brook'}, 'update': {'$push': {'locations': {"name": "Kaliti", "sub_city": "Akaki", "city": "Addis", 'equipments': [{"machine": "Mixer", "name": "Mixer1", "years_used": 4, "price": 600}, {"machine": "Compactor", "name": "Compactor1", "years_used": 4, "price": 600}]} } } })
#print(db.find({'coll': 'EquipmentSuppliers'}))




#print('done')
#db.find(dct)