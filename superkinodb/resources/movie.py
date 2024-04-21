import json
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from superkinodb import db
from superkinodb.db_models import * 
from superkinodb.consts import *
from superkinodb.utils import SuperkinodbBuilder, error_response, add_person, cleanup_personnel
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound

class MovieConverter(BaseConverter):
    def to_python(self, movie):
        db_item = Movie.query.filter_by(name=movie.name).first()
        if db_item is None:
            raise NotFound
        return db_item

    def to_url(self, movie):
        return movie.name

class MovieCollection(Resource):
    def get(self):
        movies = Movie.query.order_by(Movie.name)

        body = SuperkinodbBuilder()
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control("self", url_for("api.moviecollection"))
        body.add_control_all_actors()
        body.add_control_all_directors()
        body.add_control_all_writers()

        body["movies"] = []

        for movie in movies: 
            body["movies"].append(movie.serialize(short_form=True))

    def post(self):
        if not request.json():
            return error_response(
                415,
                "Unsupported media type",
                "Requests must be in JSON format"
            )
        
        try:
            validate(request.json, Movie.get_schema())
        except ValidationError as e:
            return error_response(
                400,
                "Invalid JSON schema",
                str(e) 
            )

        movie = Movie(
            name=request.json["name"],
            release=request.json["release"],
            genre=request.json["genre"],
            actors=request.json["actors"],
            directors=request.json["directors"],
            writers=request.json["writers"]
        )
        
        try:
            db.session.add(movie)
        except IntegrityError as e:
            return error_response(
                409,
                "Movie {} already exists".format(request.json["name"]),
                "Movies must be named uniquely"
            )

        if request.json["actors"]:
            for item in request.json["actors"]:
                actor = Actor.query.filter_by(name=item) 
                if actor is None:
                    actor = add_person(Actor, item, movie.name)
                movie.actors.append(actor)

        if request.json["directors"]:
            for item in request.json["directors"]:
                director = Director.query.filter_by(name=item) 
                if director is None:
                    director = add_person(Director, item, movie.name)
                movie.directors.append(director)

        if request.json["writers"]:
            for item in request.json["writers"]:
                writer = Writer.query.filter_by(name=item) 
                if writer is None:
                    writer = add_person(Writer, item, movie.name)
                movie.writers.append(writer)

        try:
            db.session.commit()
        except IntegrityError as e:
            return error_response(
                409,
                "Database conflict",
                str(e)
            )
        return Response(status=201)

    def delete(self):
        pass


class MovieItem(Resource):
    def get(self, movie):
        body = movie.serialize()
        body.add_control_all_movies()
        body.add_control_edit_movie(movie)
        body.add_control_delete_movie(movie)
        body.add_control_movie_reviews(movie)
        return Response(json.dumps(body), 200, mimetype="application/vnd.mason+json")

    def put(self, movie):
        if not request.json():
            return error_response(
                415,
                "Unsupported media type",
                "Requests must be in JSON format"
            )

        try:
            validate(request.json, movie.get_schema())
        except ValidationError as e:
            return error_response(
                400,
                "Invalid JSON schema",
                str(e)
            )
        
        movie.name = request.json["name"]
        movie.release = request.json["release"]
        movie.genre = request.json["genre"]
        movie.actors = request.json["actors"]
        movie.directors = request.json["directors"]
        movie.writers = request.json["writers"]

        cleanup_personnel(Actor)
        cleanup_personnel(Director)
        cleanup_personnel(Writer)

        try:
            db.session.commit()
        except IntegrityError as e: return error_response(
                409,
                "Database operation failed",
                str(e)
            )
        
        return Response(status=204)

    def delete(self, movie):
        db.session.delete(movie)
        cleanup_personnel(Actor)
        cleanup_personnel(Director)
        cleanup_personnel(Writer)

        try:
            db.session.commit()
        except IntegrityError as e:
            return error_response(
                409,
                "Database operation error",
                str(e)
            )

