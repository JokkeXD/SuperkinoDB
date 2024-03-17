import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flasgger import Swagger

db = SQLAlchemy()
cache = Cache()

# Code taken from "Flask API Project Layout" tutorial on Lovelace
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None: 
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    db.init_app(app)
    from . import db_models
    from . import api
    app.cli.add_command(db_models.init_db_command)
    app.register_blueprint(api.api_bp)
    app.config["SWAGGER"] = {
    "title": "Sensorhub API",
    "openapi": "3.0.3",
    "uiversion": 3,
    "doc_dir": "./doc",
    }
    # swagger = Swagger(app, template_file="doc/base.yml")
    return app
