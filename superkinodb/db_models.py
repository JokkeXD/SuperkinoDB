import click
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
    name = db.Column(db.String, nullable=False)
    born_on = db.Column(db.Date, nullable=True)

    directed=db.relationship(
        "Movie",
        secondary='movie_directors',
        back_populates="directors"
    )

class Writer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    born_on = db.Column(db.Date, nullable=True)

    wrote=db.relationship(
        "Movie",
        secondary='movie_writers',
        back_populates="writers"
    )

class Actor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    born_on = db.Column(db.Date, nullable=True)

    starred_in = db.relationship(
        "Movie",
        secondary='movie_actors',
        back_populates="actors"
    )

    def serialize(self, short_form=False):
        data = SuperkinodbBuilder(
            id=self.id,
            name=self.name,
            born_on=self.born_on,
            starred_in=self.starred_in
        )
        data.add_control("profile", PROFILES)

        if short_form is True:
            data.add_control("self", url_for("api.actoritem", actor=self.id))
            return data
        
        data.add_control("superkinodb", LINK_RELATIONS)
        data.add_control("self", request.path)
        data.add_control("collection", url_for("api.actorcollection"))
        data.add_control_all_movies()
        data.add_control_edit_actor(self)
        data.add_control_delete_actor(self)        
        return data


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    release = db.Column(db.Date, nullable=True)
    genre = db.Column(db.String, nullable=False)

    directors = db.relationship(
        "Director",
        secondary='movie_directors',
        back_populates="directed"
    )

    writers = db.relationship(
        "Writer",
        secondary='movie_writers',
        back_populates="wrote"
    )

    actors = db.relationship(
        "Actor",
        secondary='movie_actors',
        back_populates="starred_in",
    )

    reviews = db.relationship(
        "Review",
        back_populates="movie",
    )

class Review(db.model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer = db.Column(db.String, nullable=False)
    review_text = db.Column(db.String, nullable=True)
    score = db.Column(db.Integer, nullable=False)

    movie_id = db.Column(db.ForeignKey("movie.id", ondelete="CASCADE"), nullable=False)
    movie = db.relationship("Movie", back_populates="reviews")


@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()
