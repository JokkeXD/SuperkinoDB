from superkinodb.resources.movie import MovieItem, MovieCollection
from superkinodb.resources.actor import ActorCollection
from superkinodb.resources.director import DirectorCollection
from superkinodb.resources.writer import WriterCollection
from superkinodb.resources.review import ReviewItem, ReviewCollection
from flask import Blueprint
from flask_restful import Api

# Import resource files to add to API

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api.add_resource(ActorCollection, '/actors/')
api.add_resource(DirectorCollection, '/directors/')
api.add_resource(WriterCollection, '/writers/')
api.add_resource(MovieCollection, '/movies/')
api.add_resource(MovieItem, '/movies/<movie:movie>/')
api.add_resource(ReviewCollection, '/movies/<movie:movie>/reviews/')
api.add_resource(ReviewItem, '/movies/<movie:movie>/reviews/<review:review>/')

