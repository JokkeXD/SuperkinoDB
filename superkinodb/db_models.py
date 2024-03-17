import click
from flask.cli import with_appcontext
from superkinodb import db

@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()

# Database model classes defined here.
class Actor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    born_on = db.Column(db.Date, nullable=True)
    score = db.Column(db.Float, nullable=True)

    starred_in = db.relationship(
        "Actor",
        back_populates="actors"
    )


class Director(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    born_on = db.Column(db.Date, nullable=True)

    movies=db.relationship(
        "Movie",
        back_populates="directors",
        order_by="score"
    )

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    release = db.Column(db.Date, nullable=True)
    genre = db.Column(db.String, nullable=False)
    director_id = db.Column(db.ForeignKey("director.id", ondelete="CASCADE"), nullable = True)
    imdb_rating = db.Column(db.Float, nullable=True)
    
    directors = db.relationship(
        "Director",
        back_populates="directed_by"
    )

    actors = db.relationship(
        "Actor",
        back_populates="starred_in",
        order_by=(Actor.score)
    )
