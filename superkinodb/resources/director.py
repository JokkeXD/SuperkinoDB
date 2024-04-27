import json
from flask import Response, url_for
from flask_restful import Resource
from superkinodb.db_models import Director
from superkinodb.consts import *
from superkinodb.utils import SuperkinodbBuilder, error_response 

class DirectorCollection(Resource):
    def get(self):
        directors = Director.query.order_by(Director.name)

        body = SuperkinodbBuilder()
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control("self", url_for("api.directorcollection"))
        body.add_control_all_movies()
        body.add_control_all_actors()
        body.add_control_all_writers()

        body["directors"] = []

        for director in directors: 
            body["directors"].append(director.serialize())
        
        return Response(json.dumps(body), 200, mimetype="application/vnd.mason+json")

    def post(self):
        resp = error_response(
                405,
                "Method not allowed",
                "Request not supported for this resource"
            )
        resp.headers["Allow"] = "GET"
        return resp
   
    def put(self):
        resp = error_response(
                405,
                "Method not allowed",
                "Request not supported for this resource"
            )
        resp.headers["Allow"] = "GET"
        return resp
    
    def delete(self):
        resp = error_response(
                405,
                "Method not allowed",
                "Request not supported for this resource"
            )
        resp.headers["Allow"] = "GET"
        return resp

