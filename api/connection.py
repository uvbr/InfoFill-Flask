from flask_pymongo import PyMongo
from .config import Configurations as config
from app import app
from bson import json_util
import json
from bson.objectid import ObjectId

class Insertion(object):

    def __init__(self):

        self.conn=None        
        app.config['MONGO_DBNAME'] = config.MONGO_DBNAME
        app.config['MONGO_URI'] = config.MONGO_URL
        self.conn = PyMongo(app)


    def create_collection(self, collection_name):

        self.collect =self.conn.db[collection_name]
        return self.collect

    def insert_one_record(self,collection,record):
        """
        It inserts record into the collection and returns its id
        """
        self.collect= self.create_collection(collection)
        inserted_data= self.collect.insert(record)
        data=json.loads(json_util.dumps(self.collect.find({'_id':ObjectId(inserted_data)})))[0]
        data['_id']=data['_id']['$oid']
        return data

    def insert_multiple_records(self,collection,record):
        """
        It inserts multiple records into the collection and returns its ids
        """
        self.collect= self.create_collection(collection)
        inserted= self.collect.insert_many(record)
        return inserted.inserted_ids


    def update_one_record(self,collection,query,record):
        """
        It inserts record into the collection and returns its id
        """
        self.collect= self.create_collection(collection)
        data= self.collect.update_one(query,record)
        data=json.loads(json_util.dumps(self.collect.find(query)))[0]
        data['_id']=data['_id']['$oid']

        return data

    def update_multiple_records(self,collection,query,record):
        """
        It inserts multiple records into the collection and returns its ids
        """
        self.collect= self.create_collection(collection)
        updated_data= self.collect.update_many(query,record).distinct('_id')
        data=json.loads(json_util.dumps(self.collect.find({'_id':ObjectId(updated_data)})))[0]
        return data

    def delete_one_record(self,collection,query):
        """
        It inserts multiple records into the collection and returns its ids
        """
        self.collect= self.create_collection(collection)
        deleted_data= self.collect.delete_one(query)
        return deleted_data.deleted_count


    def validate_with_query_get_ids(self, connection, query):
        """
        It gives the count of records the collection for a query
        """
        self.collect= self.create_collection(connection)
        result= self.collect.find(query).distinct('_id')
        return result

    def retrieve_record_get_all(self, connection,record=None,retricted_fields=None):
        """
        If record parameter is None, it retrieves all records in a collection in an array
        If record parameter is passed, it retrieves particular records only in an array 
        """
        self.collect= self.create_collection(connection)
        result=[]
        if not record:
            records= self.collect.find().distinct('_id')
        else:
            records= self.collect.find(record).distinct('_id')

        if not retricted_fields:
            for record in records:
                result.append(json.loads(json_util.dumps(self.collect.find({'_id':ObjectId(record)})))[0])
        else:
            for record in records:
                data=json.loads(json_util.dumps(self.collect.find({'_id':ObjectId(record)})))[0]
                for key in list(data):
                    if key in retricted_fields:
                        del data[key]
                result.append(data)

        return result

    def filter_complete_record(self, connection,records, retricted_fields=None):
        """
        If record parameter is None, it retrieves all records in a collection in an array
        If record parameter is passed, it retrieves particular records only in an array 
        """
        self.collect= self.create_collection(connection)
        result=[]
        if not retricted_fields:
            for record in records:
                result.append(json.loads(json_util.dumps(self.collect.find({'_id':ObjectId(record)})))[0])
        else:
            for record in records:
                data=json.loads(json_util.dumps(self.collect.find({'_id':ObjectId(record)})))[0]
                for key in list(data):
                    if key in retricted_fields:
                        del data[key]
                result.append(data)
        return result



    # def __del__(self):
    #     self.conn.close()

