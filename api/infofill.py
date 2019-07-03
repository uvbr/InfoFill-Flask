from flask_restful import Resource, reqparse


import logging as logger
from .connection import Insertion as insert
from .helper import *
from flask import request, jsonify
from bson import json_util
import json
from bson.objectid import ObjectId
import random,string
import threading

def basic_auth(func):

    def wrap(cls, *args, **kwargs):
        access_token= request.headers['access_token'].strip()
        record=insert().retrieve_record_get_all('User',{'reset_code':access_token},["password","reset_code"])
        if not len(record):
            return jsonify({"message" : "Please Re-Login","status":200})

        request.auth=record[0]
        request.auth['_id']=request.auth['_id']['$oid']
        return func(cls, *args, **kwargs)

    # wrap.__doc__= func.__doc__
    # wrap.__name__= func.__name__
    return wrap

class UserView(Resource):
    parser = reqparse.RequestParser()
    def post(self):
        """
        To Check whether user is existing or not, if not
        User will be created
        URL:    /api/v1.0/user/
        body:{
                "first_name":"c",
                "last_name":"e",
                "email":"abd",
            }
        """
        UserView.parser.add_argument('email', type=str,required=True, help='This Field is mandatory')
        UserView.parser.add_argument('first_name', type=str,required=True, help='This Field is mandatory')
        UserView.parser.add_argument('last_name', type=str,required=True, help='This Field is mandatory')
        UserView.parser.add_argument('username', type=str,required=True, help='This Field is mandatory')
        UserView.parser.add_argument('is_superuser', type=str, help='This Field is mandatory')

        data = UserView.parser.parse_args()
        email= data['email']
        first_name= data['first_name']
        last_name= data['last_name']
        username= data['username']
        superuser= data['is_superuser']
        count= insert().validate_with_query_get_ids('User',{'email':email})
        if count:
            return {"message" : "User with this Email Already Exists"},400
        count= insert().validate_with_query_get_ids('User',{'username':username})
        if count:
            return {"message" : "User with this username Already Exists"},400

        secret_code= generate_secret(token_type='token_urlsafe', string_len=50)
        record= {
                'email':email,
                'username':username,
                'first_name':first_name,
                'last_name':last_name,
                'password':None,
                'role':None,
                'reset_code':secret_code.strip(),
                'is_Active':False,
                'is_Blocked':False,
                    }

        result=insert().insert_one_record('User',record)
        result.pop('password')
        if bool(superuser):
            data= insert().retrieve_record_get_all('Role',{'name':'Admin'})
            if not len(data):
                data=insert().insert_one_record('Role',{'name':'Admin'})
            else:
                data=data[0]

            result=insert().update_one_record(  'User',
                                                {'_id':ObjectId(result['_id'])},
                                                {"$set":{'role':data}}
                                                )
        url=request.base_url+'/?activate/?code='+secret_code.strip()          
        thread = threading.Thread(target=send_mail, args=(email,url,)) 
        thread.start()
        return jsonify({"message" : "User created Successfully","data":result,"status":200})

    @basic_auth
    def get(self):
        """
        To get all user details
        """
        query=dict(request.args)
        if query.keys() and 'id' in query.keys():
            result=insert().retrieve_record_get_all('User',{'_id':ObjectId(query['id'])})
            if request.auth['role']['name']==query['id']:
                result= insert().filter_complete_record('User',result)
            else:
                result= insert().filter_complete_record('User',result,['password'])

        else:
            if request.auth['role']['name']=='Admin':
                result= insert().retrieve_record_get_all('User',retricted_fields=['password'])
        return jsonify({"message" : "Retrieve User details Successfully","data":result,"status":200})
    
    @basic_auth
    def put(self):
        """
        To update user detail by id
        """
        query=dict(request.args)
        result=None
        if query.keys() and 'id' in query.keys():
            result=insert().validate_with_query_get_ids('User',{'_id':ObjectId(query['id'])})
        else:
            return jsonify({"message" : "User Not Found","data":result,"status":200})

        if result:
            data=request.get_json()
            for key in list(data):
                if not data[key]:
                    return jsonify({"message" : key+" Cannot be blank","data":result,"status":400})

            result=insert().update_one_record(  'User',
                                                {'_id':ObjectId(query['id'])},
                                                {"$set":data}
                                                )
        else:
            return jsonify({"message" : "User Not Found","data":result,"status":200})
        return jsonify({"message" : "Updated User details Successfully","data":result,"status":200})

    @basic_auth
    def delete(self):
        """
        To delete multiple users
        """
        if 'ids' in request.get_json() and len(request.get_json()['ids'])>0:
            users= request.get_json()['ids']
        else:
            return jsonify({"message" : "Provide Users To Delete","status":400})

        for user in users:
            result=insert().validate_with_query_get_ids('User',{'_id':ObjectId(user)})
            if len(result):
                result= insert().delete_one_record('User',{'_id':ObjectId(user)})
                if result<=0:
                    return jsonify({"message" : "User Deleted Failed","data":result,"status":200})
            else:
                return jsonify({"message" : "User Not Found","data":result,"status":200})
        return jsonify({"message" : "Users Deleted Successfully","data":result,"status":200})

class Authenticate(Resource):
    parser = reqparse.RequestParser()
    def post(self):
        Authenticate.parser.add_argument('username', type=str,required=True, help='This Field is mandatory')
        Authenticate.parser.add_argument('password', type=str,required=True, help='This Field is mandatory')
        data = Authenticate.parser.parse_args()
        username= data['username']
        password= data['password']
        record=insert().retrieve_record_get_all('User',{'username':username,'password':password})
        if not len(record):
            return jsonify({"message" : "Invalid Username/Password","status":200})
        if not record[0]['is_Active']:
            return jsonify({"message" : "Activate Account","status":200})
        secret_code= generate_secret(token_type='token_urlsafe', string_len=50)
        data=dict({'reset_code':secret_code})
        record=insert().update_one_record(  'User',
                                    {'_id':ObjectId(record[0]['_id']['$oid'])},
                                    {"$set":data}
                                    )
        return jsonify({"message" : "SuccessFully Logged in","data":record,"status":200})

class ActivateAccount(Resource):
    parser = reqparse.RequestParser()

    def post(self):
        ActivateAccount.parser.add_argument('username', type=str,required=True, help='This Field is mandatory')
        ActivateAccount.parser.add_argument('password', type=str,required=True, help='This Field is mandatory')
        data= request.get_json()
        query=dict(request.args)
        code=None
        if query.keys() and 'code' in query.keys():
            code =query['code']
        else:
            return jsonify({"message" : "Activation Failed","status":200})
        if code:
            result=insert().validate_with_query_get_ids('User',{'reset_code':code.strip(),'is_Active':False})
            if len(result):
                record_id=result[0]
                data=dict({'username':data['username'],'password':data['password'],'is_Active':True})
                result=insert().update_one_record(  'User',
                                                    {'_id':record_id},
                                                    {"$set":data})
                result.pop('password')
                return jsonify({"message" : "Account Activated Successfully","data":result,"status":200})
        return jsonify({"message" : "Activation Failed","status":200})

class RoleView(Resource):
    parser = reqparse.RequestParser()

    @basic_auth
    def get(self):
        result= insert().retrieve_record_get_all('Role',{'actor':request.auth})
        return jsonify({"message" : "Retrieved User details Successfully","data":result,"status":200})

    @basic_auth    
    def post(self):
        RoleView.parser.add_argument('role', type=str,required=True, help='This Field is mandatory')
        data = RoleView.parser.parse_args()
        if 'role' in data and data['role']:
            role=data['role']
        count= insert().retrieve_record_get_all('Role',{'name':role,'actor':request.auth})
        if count:
            return {"message" : "Role Already Exists"},400
        
        record= {
                'name':role,
                'actor':request.auth
                    }

        result=insert().insert_one_record('Role',record)

        return jsonify({"message" : "Role Created Successfully","data":result,"status":200})

    @basic_auth
    def put(self):
        query=dict(request.args)
        result=None
        if query.keys() and 'id' in query.keys():
            result=insert().validate_with_query_get_ids('Role',{'_id':ObjectId(query['id'])})
        else:
            return jsonify({"message" : "Role Not Found","data":result,"status":200})

        if result:
            data=request.get_json()
            if 'name' in data and data['name']:
                name= data['name']
            else:
                return jsonify({"message" : "Name Cannot be blank","data":result,"status":400})

            result=insert().update_one_record(  'Role',
                                                {'_id':ObjectId(query['id'])},
                                                {"$set":{'name':name}})

        return jsonify({"message" : "Updated Role details Successfully","data":result,"status":200})


    @basic_auth
    def delete(self):

        if 'roles' in request.get_json() and len(request.get_json()['roles'])>0:
            roles= request.get_json()['roles']
        else:
            return jsonify({"message" : "Provide Roles To Delete","status":400})

        for role in roles:
            result=insert().validate_with_query_get_ids('Role',{'_id':ObjectId(role),'actor':request.auth})
            if len(result):
                result= insert().delete_one_record('Role',{'_id':ObjectId(role),'actor':request.auth})
                if result<=0:
                    return jsonify({"message" : "Role Deleted Failed","data":result,"status":200})
            else:
                return jsonify({"message" : "Role Not Found","data":result,"status":200})
        return jsonify({"message" : "Role Deleted Successfully","data":result,"status":200})

class AttachUserRole(Resource):
    
    @basic_auth
    def put(self):
        """
        To update user detail by id
        """
        query=dict(request.args)
        result=None
        if query.keys() and 'user_id' in query.keys():
            result=insert().validate_with_query_get_ids('User',{'_id':ObjectId(query['user_id'])})
        else:
            return jsonify({"message" : "User Not Found","data":result,"status":200})

        if result:
            data=request.get_json()
            if 'role_id' in data:
                if data['role_id']:
                    role_id=data['role_id']
                else:
                    role_id=None
            else:
                return jsonify({"message" : "User Not Found","data":result,"status":200})
            
            if role_id:
                result=insert().retrieve_record_get_all('Role',{'_id':ObjectId(role_id)})
                if result:
                    role_id= {'_id':result[0]['_id']['$oid'],'name':result[0]['name']}
                else:
                    return jsonify({"message" : "User Not Found","data":result,"status":200})
                
            result=insert().update_one_record(  'User',
                                                {'_id':ObjectId(query['user_id'])},
                                                {"$set":{'role':role_id}}
                                                )
            return jsonify({"message" : "User Role Updated SuccessFully Found","data":result,"status":200})
        return jsonify({"message" : "User Not Found","data":result,"status":200})

