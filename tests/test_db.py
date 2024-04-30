import os
import pytest
import random
import string
import tempfile
from datetime import date
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError
from superkinodb import create_app, db
from superkinodb.db_models import Movie, Review, Actor, Writer, Director

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture
def app():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING":True
    }

    app = create_app(config)

    with app.app_context():
        db.create_all()

    yield app

    os.close(db_fd)
    os.unlink(db_fname)

def _create_movie(movie_name="Good Movie 1"):
    return Movie(
        name="test-{}".format(movie_name),
        release=date.today(),
        genre="comedy"
    )

def _create_review(reviewer_name="VeryCriticalGuy69"):
    return Review(
        reviewer="test-{}".format(reviewer_name),
        score=random.uniform(0.0, 10.0),
        review_text=''.join(random.choices(string.ascii_lowercase +
                                           string.digits, k=500))
    )

def _create_person(person_type, person_name="MoviePerson"):
    return person_type(
        name=person_name
    )

def test_create_items(app):
    with app.app_context():
        movie = _create_movie()
        review = _create_review()
        actor = _create_person(Actor, "test-Actor")
        director = _create_person(Director, "test-Director")
        writer = _create_person(Writer, "test-Writer")

        movie.actors.append(actor)
        movie.directors.append(director)
        movie.writers.append(writer)
        movie.reviews.append(review)
        db.session.add(movie)
        db.session.add(actor)
        db.session.add(director)
        db.session.add(writer)
        db.session.add(review)
        db.session.commit()

        assert Movie.query.count() == 1
        assert Review.query.count() == 1
        assert Actor.query.count() == 1
        assert Director.query.count() == 1
        assert Writer.query.count() == 1

        db_movie = Movie.query.first()
        db_review = Review.query.first()
        db_actor = Actor.query.first()
        db_director = Director.query.first()
        db_writer = Writer.query.first()

        assert db_review in db_movie.reviews
        assert db_actor in db_movie.actors
        assert db_director in db_movie.directors
        assert db_writer in db_movie.writers
        assert db_movie == db_review.movie
        assert db_movie in db_actor.movies
        assert db_movie in db_director.movies
        assert db_movie in db_writer.movies

def test_movie_review_one_to_many(app):
    with app.app_context():
        movie1 = _create_movie("movie1")
        movie2 = _create_movie("movie2")
        review = _create_review("reviewer1")

        movie1.reviews.append(review)
        movie2.reviews.append(review)

        db.session.add(review)
        db.session.add(movie1)
        db.session.add(movie2)

        with pytest.raises(IntegrityError):
            db.session.commit()

def test_movie_ondelete_review(app):
    with app.app_context():
        movie = _create_movie()
        review = _create_review()
        movie.reviews.append(review)
        db.session.add(movie)
        db.session.add(review)
        db.session.commit()
        db.session.delete(review)
        db.session.commit()
        assert movie.reviews is None

def test_review_ondelete_movie(app):
    with app.app_context():
        movie = _create_movie()
        review = _create_review()
        movie.reviews.append(review)
        db.session.add(movie)
        db.session.add(review)
        db.session.commit()
        db.session.delete(movie)
        db.session.commit()
        assert Movie.query.filter_by(name=movie.name) is None
        assert Review.query.filter_by(reviewer=review.reviewer) is None

def test_movie_columns(app):
    with app.app_context():
        # Movie must have a name
        movie = _create_movie()
        movie.name = None
        db.session.add(movie)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        # Movie name must be unique
        movie1 = _create_movie()
        movie2 = _create_movie()
        db.session.add(movie1)
        db.session.add(movie2)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        movie = _create_movie()
        movie.release = "2024-13-32" # Invalid date
        db.session.add(movie)
        with pytest.raises(StatementError):
            db.session.commit()

        db.session.rollback()

        movie = _create_movie()
        movie.genre = 1
        db.session.add(movie)
        with pytest.raises(StatementError):
            db.session.commit()

        db.session.rollback()

        movie = _create_movie()
        movie.release = None
        movie.genre = None
        db.session.add(movie)
        db.session.commit()

def test_review_columns(app):
    with app.app_context():
        # Reviewer can't be None
        review = _create_review()
        review.reviewer = None
        db.session.add(review)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        # Score can't be None
        review = _create_review()
        review.score = None
        db.session.add(review)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        # Score must be a number
        review = _create_review()
        review.score = "10"
        db.session.add(review)
        with pytest.raises(StatementError):
            db.session.commit()

        db.session.rollback()

        # Score max limit is 10.0
        review = _create_review()
        review.score = 10.1
        db.session.add(review)
        with pytest.raises(StatementError):
            db.session.commit()

        db.session.rollback()

        # Score min limit is 0.0
        review = _create_review()
        review.score = -0.1
        db.session.add(review)
        with pytest.raises(StatementError):
            db.session.commit()

        db.session.rollback()

        # Review text is limited to 1000 characters
        review = _create_review()
        review.review_text = ''.join(random.choices(string.ascii_lowercase +
                                           string.digits, k=1001))
        db.session.add(review)
        with pytest.raises(StatementError):
            db.session.commit()

        db.session.rollback()
        
        review = _create_review()
        review.review_text = None
        db.session.add(review)
        db.session.commit()

def test_person_columns(app):
    with app.app_context():
        # Names must exist
        actor = _create_person(Actor, "actor")
        actor.name = None
        db.session.add(actor)
        with pytest.raises(StatementError):
            db.session.commit()

        db.session.rollback()

        director = _create_person(Director, "director")
        director.name = None
        db.session.add(director)
        with pytest.raises(StatementError):
            db.session.commit()

        db.session.rollback()
        
        writer = _create_person(Writer, "writer")
        writer.name = None
        db.session.add(writer)
        with pytest.raises(StatementError):
            db.session.commit()

        db.session.rollback()

        # Names must be unique
        actor1 = _create_person(Actor, "actor")
        actor2 = _create_person(Actor, "actor")
        db.session.add(actor1)
        db.session.add(actor2)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        director1 = _create_person(Director, "director")
        director2 = _create_person(Director, "director")
        db.session.add(director1)
        db.session.add(director2)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        writer1 = _create_person(Writer, "writer")
        writer2 = _create_person(Writer, "writer")
        db.session.add(writer1)
        db.session.add(writer2)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

