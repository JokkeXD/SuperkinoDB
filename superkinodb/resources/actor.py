import json
from flask import Response, url_for
from flask_restful import Resource
from superkinodb.db_models import Actor
from superkinodb.consts import *
from superkinodb.utils import SuperkinodbBuilder, error_response

class ActorCollection(Resource):
    def get(self):
        actors = Actor.query.order_by(Actor.name)

        body = SuperkinodbBuilder()
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control("self", url_for("api.actorcollection"))
        body.add_control_all_movies()
        body.add_control_all_directors()
        body.add_control_all_writers()

        body["actors"] = []

        for actor in actors:
            body["actors"].append(actor.serialize())

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

