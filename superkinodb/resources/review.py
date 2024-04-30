import json
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from superkinodb import db
from superkinodb.db_models import Review, Movie
from superkinodb.consts import *
from superkinodb.utils import SuperkinodbBuilder, error_response
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound

class ReviewConverter(BaseConverter):
    def to_python(self, reviewer):
        db_item = Review.query.filter_by(reviewer=reviewer).first()
        if db_item is None:
            raise NotFound
        return db_item

    def to_url(self, review):
        return review.reviewer

class ReviewCollection(Resource):
    def get(self, movie):
        reviews = Review.query.filter_by(movie=movie)
        movie_item = Movie.query.filter_by(name=movie.name).first()

        body = SuperkinodbBuilder()
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control("self", url_for("api.reviewcollection", movie=movie))
        body.add_control("movie", url_for("api.movieitem", movie=movie))
        body.add_control_add_review(movie_item=movie)

        body["reviews"] = []

        for review_item in reviews:
            item = SuperkinodbBuilder()
            item.add_control("self", url_for("api.reviewitem", movie=movie_item, review=review_item))
            item["data"] = review_item.serialize(short_form=True)
            body["reviews"].append(item)

        return Response(json.dumps(body), 200, mimetype="application/vnd.mason+json")

    def post(self, movie):
        if not request.json:
            return error_response(
                415,
                "Unsupported media type",
                "Requests must be in JSON format"
            )

        try:
            validate(request.json, Review.get_schema())
        except ValidationError as e:
            return error_response(
                400,
                "Invalid JSON schema",
                str(e) 
            )

        review = Review(
            reviewer=request.json["reviewer"],
            score=request.json["score"],
            review_text=request.json.get("review_text"),
            movie_name=movie.name
        )

        review_by_reviewer_exists = Review.query.filter_by(
                reviewer=review.reviewer,
                movie_name=movie.name).first()

        if review_by_reviewer_exists:
            return error_response(
                409,
                "Entry by this reviewer already exists",
                "Reviewer must be unique within a review collection"
            )

        try:
            db.session.add(review)
        except IntegrityError as e:
            return error_response(
                409,
                "Database operation failed",
                str(e)
            )

        db.session.commit()

        return Response(
                status=201,
                headers={"Location": url_for("api.reviewitem", movie=movie, review=review)}
            )
    
    def delete(self):
        resp = error_response(
                405,
                "Method not allowed",
                "Request not supported for this resource"
            )
        resp.headers["Allow"] = "GET, POST"
        return resp

class ReviewItem(Resource):
    def get(self, review, movie):

        body = SuperkinodbBuilder()
        body["data"] = review.serialize()
        body.add_control("self", url_for("api.reviewitem", movie=movie, review=review))
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control("reviewcollection", url_for("api.reviewcollection", movie=movie))
        body.add_control_edit_review(movie_item=movie, review_item=review)
        body.add_control_delete_review(movie_item=movie, review_item=review)

        return Response(json.dumps(body), 200, mimetype="application/vnd.mason+json")

    def post(self):
        resp = error_response(
                405,
                "Method not allowed",
                "Request not supported for this resource"
            )
        resp.headers["Allow"] = "GET, PUT, DELETE"
        return resp
    
    def put(self, review, movie):
        if not request.json:
            return error_response(
                415,
                "Unsupported media type",
                "Requests must be in JSON format"
            )

        try:
            validate(request.json, Review.get_schema())
        except ValidationError as e:
            return error_response(
                400,
                "Invalid JSON schema",
                str(e)
            )

        review.reviewer = request.json["reviewer"]
        review.review_text = request.json["review_text"] 
        review.score = request.json["score"] 
       
        try:
            db.session.commit()
        except IntegrityError as e: return error_response(
                409,
                "Database operation failed",
                str(e)
            )
        
        return Response(status=204)

    def delete(self, review, movie):
        db.session.delete(review)
        db.session.commit()

