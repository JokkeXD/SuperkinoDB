from flask import url_for
from flask_restful import Resource
from superkinodb.db_models import Actor
from superkinodb.consts import *
from superkinodb.utils import SuperkinodbBuilder 

class ActorCollection(Resource): #TODO: Continue from this, once DB model has all necessary components
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
            body["actors"].append(actor.serialize(short_form=True))

    def post(self):
        pass

    def delete(self):
        pass

