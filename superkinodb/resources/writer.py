from flask import url_for
from flask_restful import Resource
from superkinodb.db_models import Writer
from superkinodb.consts import *
from superkinodb.utils import SuperkinodbBuilder 

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
            body["writers"].append(writer.serialize(short_form=True))

    def post(self):
        pass

    def delete(self):
        pass

