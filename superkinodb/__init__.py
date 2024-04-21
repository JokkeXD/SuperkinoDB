import os
import json
from flask import Flask, Response
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from superkinodb.consts import *

db = SQLAlchemy()
#cache = Cache() TODO Using Cache?

# Code taken from "Flask API Project Layout" tutorial on Lovelace
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "dev.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

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
    app.cli.add_command(db_models.init_db_command) 
    app.cli.add_command(db_models.populate_db)
    app.url_map.converters["movie"] = MovieConverter
    app.url_map.converters["review"] = ReviewConverter
    app.register_blueprint(api.api_bp)

    db.init_app(app)

    @app.route('/', methods=["GET"])
    def entry_point():
        return Response(
            status=200,
            response=json.dumps(
                {"@namespaces": {
                    "superkinodb": {
                        "name": LINK_RELATIONS
                    }
                },
                "@controls": {
                    "superkinodb:movies": {
                        "href": "/api/movies/"
                    }
                }
                })
            )
    

    return app
