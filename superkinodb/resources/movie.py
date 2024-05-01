import json
from datetime import datetime
from datetime import date
from jsonschema import validate, ValidationError, draft7_format_checker
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from superkinodb import db
from superkinodb.db_models import Movie, Actor, Director, Writer
from superkinodb.consts import *
from superkinodb.utils import SuperkinodbBuilder, error_response, add_person 
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound

class MovieConverter(BaseConverter):
    def to_python(self, movie):
        db_item = Movie.query.filter_by(name=movie).first()
        if db_item is None:
            raise NotFound
        return db_item

    def to_url(self, db_item):
        return db_item.name

class MovieCollection(Resource):
    def get(self):
        movies = Movie.query.order_by(Movie.name)

        body = SuperkinodbBuilder()
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control("self", url_for("api.moviecollection"))
        body.add_control_add_movie()
        body.add_control_all_actors()
        body.add_control_all_directors()
        body.add_control_all_writers()

        body["movies"] = []

        for movie in movies:
            item = SuperkinodbBuilder()
            item.add_control("self", url_for("api.movieitem", movie=movie))
            item["data"] = movie.serialize(short_form=True)
            body["movies"].append(item)
        
        return Response(json.dumps(body), 200, mimetype="application/vnd.mason+json")

    def post(self):
        if not request.json:
            return error_response(
                415,
                "Unsupported media type",
                "Requests must be in JSON format"
            )
        
        try:
            validate(request.json, Movie.get_schema(), format_checker=draft7_format_checker)
            release = request.json.get('release')
            if release:
                release_date = datetime.strptime(release, '%Y-%m-%d').date()
            else:
                release_date = date.today()
        
        except ValidationError as e:
            return error_response(
                400,
                "Invalid JSON schema",
                str(e) 
            )
        
        movie = Movie(
            name=request.json["name"],
            release=release_date,
            genre=request.json.get("genre"),
        )

        try:
            db.session.add(movie)
        except IntegrityError as e:
            return error_response(
                409,
                "Movie {} already exists".format(request.json["name"]),
                "Movies must be named uniquely"
            )

        for item in request.json.get("actors", []):
            actor = Actor.query.filter_by(name=item).first()
            if actor is None:
                actor = add_person(Actor, item)
            
            movie.actors.append(actor)

        for item in request.json.get("directors", []):
            director = Director.query.filter_by(name=item).first()
            if director is None:
                director = add_person(Director, item)
            
            movie.directors.append(director)

        for item in request.json.get("writers", []):
            writer = Writer.query.filter_by(name=item).first()
            if writer is None:
                writer = add_person(Writer, item)
            
            movie.writers.append(writer)

        try:
            db.session.commit()
        except IntegrityError as e:
            return error_response(
                409,
                "Database conflict",
                str(e)
            )
        return Response(status=201, headers={"Location": url_for("api.movieitem", movie=movie)})

    def put(self):
        resp = error_response(
                405,
                "Method not allowed",
                "Request not supported for this resource"
            )
        resp.headers["Allow"] = "GET, POST"

        return resp

    def delete(self):
        resp = error_response(
                405,
                "Method not allowed",
                "Request not supported for this resource"
            )
        resp.headers["Allow"] = "GET, POST"
        return resp

class MovieItem(Resource):
    def get(self, movie):
        body = SuperkinodbBuilder()
        body["data"] = movie.serialize()
        body.add_control("self", url_for("api.movieitem", movie=movie))
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control_all_movies()
        body.add_control_edit_movie(movie)
        body.add_control_delete_movie(movie)
        body.add_control_movie_reviews(movie)
        return Response(json.dumps(body), 200, mimetype="application/vnd.mason+json")

    def post(self, movie):
        resp = error_response(
                405,
                "Method not allowed",
                "Request not supported for this resource"
            )
        resp.headers["Allow"] = "GET, PUT, DELETE"
        return resp
    
    def put(self, movie):
        if not request.json:
            return error_response(
                415,
                "Unsupported media type",
                "Requests must be in JSON format"
            )
        
        try:
            validate(request.json, Movie.get_schema(), format_checker=draft7_format_checker)
            release = request.json.get('release')
            
            if release:
                release_date = datetime.strptime(release, '%Y-%m-%d').date()
            else:
                release_date = date.today()

        except ValidationError as e:
            return error_response(
                400,
                "Invalid JSON schema",
                str(e) 
            )

        movie.name = request.json["name"]
        movie.release = release_date
        movie.genre = request.json.get("genre", "")

        try:
            actors = []
            for item in request.json.get("actors", []):
                actor = Actor.query.filter_by(name=item).first()
                if actor is None:
                    actor = add_person(Actor, item)
                actors.append(actor)
            
            movie.actors = actors

            directors = []
            for item in request.json.get("directors", []):
                director = Director.query.filter_by(name=item).first()
                if director is None:
                    director = add_person(Director, item)
                directors.append(director)

            movie.directors = directors
            
            writers = []
            for item in request.json.get("writers", []):
                writer = Writer.query.filter_by(name=item).first()
                if writer is None:
                    writer = add_person(Writer, item)
                writers.append(writer)
            
            movie.writers = writers

            db.session.commit()
        except IntegrityError as e: return error_response(
                409,
                "Database operation failed",
                str(e)
            )
        
        return Response(status=204)

    def delete(self, movie):
        db.session.delete(movie)
        try:
            db.session.commit()
        except IntegrityError as e:
            return error_response(
                409,
                "Database operation error",
                str(e)
            )
        return Response(status=204)
