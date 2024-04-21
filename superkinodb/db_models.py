from enum import unique
import click
from datetime import date
from flask import url_for, request
from flask.cli import with_appcontext
from superkinodb import db
from superkinodb.utils import SuperkinodbBuilder
from superkinodb.consts import *

movie_actors = db.Table('movie_actors',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id')),
    db.Column('actor_id', db.Integer, db.ForeignKey('actor.id')))

movie_directors = db.Table('movie_directors',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id')),
    db.Column('director_id', db.Integer, db.ForeignKey('director.id')))

movie_writers = db.Table('movie_writers',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id')),
    db.Column('writer_id', db.Integer, db.ForeignKey('writer.id')))

# Database model classes defined here.
class Director(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)

    movies=db.relationship(
        "Movies",
        secondary='movie_directors',
        back_populates="directors"
    )

    def serialize(self):
        data = SuperkinodbBuilder(
            id=self.id,
            name=self.name,
            movies=self.movies
        )
        return data


class Writer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)

    movies=db.relationship(
        "Movie",
        secondary='movie_writers',
        back_populates="writers"
    )

    def serialize(self):
        data = SuperkinodbBuilder(
            id=self.id,
            name=self.name,
            movies=self.movies
        )
        return data


class Actor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)

    movies = db.relationship(
        "Movie",
        secondary='movie_actors',
        back_populates="actors"
    )

    def serialize(self):
        data = SuperkinodbBuilder(
            id=self.id,
            name=self.name,
            movies=self.movies
        )
        return data
    
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    release = db.Column(db.Date, nullable=True)
    genre = db.Column(db.String, nullable=False)

    directors = db.relationship(
        "Director",
        secondary='movie_directors',
        back_populates="directed",
        backref="movies",
        cascade="all, delete"
    )

    writers = db.relationship(
        "Writer",
        secondary='movie_writers',
        back_populates="wrote",
        backref="movies",
        cascade="all, delete"
    )

    actors = db.relationship(
        "Actor",
        secondary='movie_actors',
        back_populates="starred_in",
        backref="movies",
        cascade="all, delete"
    )

    reviews = db.relationship(
        "Review",
        back_populates="movie"
    )
 
    def serialize(self, short_form=False):
        body = SuperkinodbBuilder()
        body.add_control("self", url_for("api.movieitem", movie=self.name))
        body["name"] = self.name

        if short_form is True:
            return body
        
        body["release"] = self.release
        body["genre"] = self.genre
        body["actors"] = self.actors
        body["directors"] = self.directors
        body["writers"] = self.writers
        body.add_namespace("superkinodb", LINK_RELATIONS)

        return body
   
    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["name"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Movie's name",
            "type": "string"
        }
        props["release"] = {
            "description": "Release date",
            "type": "date"
        }
        props["genre"] = {
            "description": "Genre(s)",
            "type": "string"
        }
        props["actors"] = {
            "description": "Actors in the movie, limit to main roles",
            "type": "array",
            "items": {
                "type": "string"
            }
        }
        props["directors"] = {
            "description": "Directors of the movie",
            "type": "array",
            "items": {
                "type": "string"
            }
        }
        props["writers"] = {
            "description": "Writers of the movie",
            "type": "array",
            "items": {
                "type": "string"
            }
        }
        return schema

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer = db.Column(db.String, nullable=False)
    review_text = db.Column(db.String, nullable=True)
    score = db.Column(db.Integer, nullable=False)

    movie_name = db.Column(db.ForeignKey("movie.name", ondelete="CASCADE"), nullable=False)
    movie = db.relationship("Movie", back_populates="reviews")

    def serialize(self, short_form=False):
        body = SuperkinodbBuilder()
        body.add_control("self", url_for("api.reviewitem", movie=self.movie, review=self.reviewer))
        body["reviewer"] = self.reviewer
        body["score"] = self.score

        if short_form is True:
            return body
        
        body["review_text"] = self.review_text
        body["movie"] = self.movie
        body.add_namespace("superkinodb", LINK_RELATIONS)

        return body

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["reviewer", "score"]
        }
        props = schema["properties"] = {}
        props["reviewer"] = {
            "description": "Reviewer's name or identifier",
            "type": "string"
        }
        props["review_text"] = {
            "description": "Freely written review text",
            "type": "string"
        }
        props["score"] = {
            "description": "Score 0.0 - 10.0",
            "type": "number"
        }
        return schema

@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()

@click.command("testgen")
@with_appcontext
def populate_db():
    for i in range(4):
        movie = Movie(
            name="test-movie{}".format(i),
            release=date.today(),
            genre="Drama"
        )
        db.session.add(movie)

        actor = Actor(
            name="actor{}".format(i)
        )
        db.session.add(actor)

        director = Director(
            name="director{}".format(i)
        )
        db.session.add(director)

        writer = Writer(
            name="writer{}".format(i)
        )
        db.session.add(writer)

    db.session.commit()
