from flask import url_for
from flask_restful import Resource
from superkinodb.db_models import Director
from superkinodb.consts import *
from superkinodb.utils import SuperkinodbBuilder 

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
            body["directors"].append(director.serialize(short_form=True))

    def post(self):
        pass

    def delete(self):
        pass

