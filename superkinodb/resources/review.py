import json
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from superkinodb import db
from superkinodb.db_models import Review
from superkinodb.consts import *
from superkinodb.utils import SuperkinodbBuilder, error_response
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound

class ReviewConverter(BaseConverter):
    def to_python(self, review):
        db_item = Review.query.filter_by(reviewer=review.reviewer).first()
        if db_item is None:
            raise NotFound
        return db_item

    def to_url(self, review):
        return review.reviewer

class ReviewCollection(Resource):
    def get(self, movie):
        reviews = Review.query.filter_by(movie=movie)

        body = SuperkinodbBuilder()
        body.add_namespace("superkinodb", LINK_RELATIONS)
        body.add_control("self", url_for("api.reviewcollection", movie=movie))
        body.add_control("movie", url_for("api.movieitem", movie=movie))
        body.add_control_add_review(movie_item=movie)

        body["reviews"] = []

        for item in reviews: 
            body["reviews"].append(item.serialize(short_form=True))

    def post(self, movie):
        if not request.json():
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
            review_text=request.json["review_text"],
            score=request.json["score"],
            movie_name=movie.name
        )

        try:
            db.session.add(review)
        except IntegrityError as e:
            return error_response(
                409,
                "Entry by this reviewer already exists",
                str(e)
            )

        db.session.commit()

        return Response(status=201)

    def delete(self):
        pass


class ReviewItem(Resource):
    def get(self, review, movie):
        body = review.serialize()
        body.add_control("reviewcollection", url_for("api.reviewcollection", movie=movie))
        body.add_control_edit_review(movie_item=movie, review_item=review)
        body.add_control_delete_review(movie_item=movie, review_item=review)
        return Response(json.dumps(body), 200, mimetype="application/vnd.mason+json")

    def put(self, review):
        if not request.json():
            return error_response(
                415,
                "Unsupported media type",
                "Requests must be in JSON format"
            )

        try:
            validate(request.json, review.get_schema())
        except ValidationError as e:
            return error_response(
                400,
                "Invalid JSON schema",
                str(e)
            )

        review.reviewer = request.json["reviewer"],
        review.review_text = request.json["review_text"], 
        review.score = request.json["score"] 
       
        try:
            db.session.commit()
        except IntegrityError as e: return error_response(
                409,
                "Database operation failed",
                str(e)
            )
        
        return Response(status=204)

    def delete(self, review):
        db.session.delete(review)
        db.session.commit()

