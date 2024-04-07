import json
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from superkinodb import db
from superkinodb.db_models import Actor
from superkinodb.consts import *
from superkinodb.utils import SuperkinodbBuilder, error_response

class ActorCollection(Resource): #TODO: Continue from this, once DB model has all necessary components
    def get(self):
        actors = Actor.query.order_by(Actor.name)

        body = SuperkinodbBuilder()
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control("self", url_for("api.actorcollection"))
        body.add_control_all_movies()

        body["actors"] = []

        for actor in actors:
            body["actors"].append(actor.serialize(short_form=True))

    def post(self):
        pass

    def delete(self):
        pass

class ActorItem(Resource):

    def get(self, actor):
        body = SuperkinodbBuilder(
            id = actor.id,
            name = actor.name,
            born_on = actor.born_on,
            starred_in = actor.starred_in
        )
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control("self", url_for("api.actoritem", actor=actor.id))
        body.add_control("actor_collection", url_for("api.actorcollection"))

        return Response(json.dumps(body), 200, mimetype="application/vnd.mason+json")

    def put(self, actor):
        if not request.json():
            return error_response(
                415,
                "Unsupported media type",
                "Requests must be in JSON format"
            )

        try:
            validate(request.json, Actor.get_schema())
        except ValidationError as e:
            return error_response(
                400,
                "Invalid JSON schema",
                str(e)
            )
        
        actor.name = request.json["name"]
        actor.born_on = request.json["born_on"]

        try:
            db.session.commit()
        except IntegrityError as e:
            return error_response(
                409,
                "Database operation failed",
                str(e)
            )
        
        return Response(status=204)

    def delete(self, actor):
        db.session.delete(actor)
        db.session.commit()
