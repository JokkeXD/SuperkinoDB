from superkinodb.resources.actor import ActorItem, ActorCollection
from flask import Blueprint
from flask_restful import Api

# Import resource files to add to API

api_bp = Blueprint("api", __name__)
api = Api(api_bp)

api.add_resource(ActorCollection, '/actors/')
api.add_resource(ActorItem, '/actors/<actor:actor>/')
