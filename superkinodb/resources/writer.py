import json
from flask import Response, url_for
from flask_restful import Resource
from superkinodb.db_models import Writer
from superkinodb.consts import *
from superkinodb.utils import SuperkinodbBuilder, error_response

class WriterCollection(Resource):
    def get(self):
        writers = Writer.query.order_by(Writer.name)

        body = SuperkinodbBuilder()
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control("self", url_for("api.writercollection"))
        body.add_control_all_movies()
        body.add_control_all_actors()
        body.add_control_all_directors()

        body["writers"] = []

        for writer in writers: 
            body["writers"].append(writer.serialize())

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

