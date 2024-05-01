import os
import json
from flask import Flask, Response, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from superkinodb.consts import *

db = SQLAlchemy()
cache = Cache()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "dev.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    print(app.instance_path)

    if test_config is None: 
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    from . import db_models
    from . import api
    from superkinodb.resources.movie import MovieConverter
    from superkinodb.resources.review import ReviewConverter
    from superkinodb.utils import SuperkinodbBuilder
    app.cli.add_command(db_models.init_db_command) 
    app.cli.add_command(db_models.populate_db)
    app.url_map.converters["movie"] = MovieConverter
    app.url_map.converters["review"] = ReviewConverter
    app.register_blueprint(api.api_bp)

    db.init_app(app)

    @app.route('/api/', methods=["GET"])
    def entry_point():
        body = SuperkinodbBuilder()
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control("superkinodb:movies", url_for("api.moviecollection"))
        return Response(json.dumps(body), 200, mimetype="application/vnd.mason+json")

    @app.route(LINK_RELATIONS)
    def link_relations():
        return "Link relations for Superkinodb"

    return app

