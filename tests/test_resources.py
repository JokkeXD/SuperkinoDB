import json
import os
import pytest
import random
import string
import tempfile
from datetime import date
from jsonschema import validate
from sqlalchemy.engine import Engine
from sqlalchemy import event
from superkinodb import create_app, db
from superkinodb.db_models import Movie, Review, Actor, Writer, Director

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    
    app = create_app(config)
    
    with app.app_context():
        db.create_all()
        _create_test_data()
        
    yield app.test_client()
    
    os.close(db_fd)
    os.unlink(db_fname)

def _create_test_data():
    for i in range(1, 5):
        m = Movie(
            name="test-movie-{}".format(i),
            release=date.today(),
            genre="horror"
        )

        a = Actor(
            name="test-actor-{}".format(i)
        )

        d = Director(
            name="test-director-{}".format(i)
        )

        w = Writer(
            name="test-writer-{}".format(i)
        )

        m.actors.append(a)
        m.directors.append(d)
        m.writers.append(w)
        
        for j in range(1, 4):
            r = Review(
                reviewer="test-reviewer-{}".format(j),
                score=5.0,
                review_text=''.join(random.choices(string.ascii_lowercase +
                                               string.digits, k=500))

            )
            m.reviews.append(r)

        db.session.add(m)
        db.session.add(a)
        db.session.add(d)
        db.session.add(w)
        db.session.add(r)
        db.session.commit()

def _get_movie_json(name="movie"):
    return {
        "name": "test-{}".format(name),
        "release": str(date.today()),
        "genre": "comedy"
    }

def _get_review_json(reviewer="reviewer"):
    return {
        "reviewer": "test-{}".format(reviewer),
        "score": 9.5,
        "review_text": ''.join(random.choices(string.ascii_lowercase +
                                           string.digits, k=500))
    }

def _check_namespace(client, response):
    href = response["@namespaces"]["superkinodb"]["name"]
    resp = client.get(href)
    assert resp.status_code == 200

def _check_control_get(client, ctrl, obj):
    href = obj["@controls"][ctrl]["href"]
    response = client.get(href)
    assert response.status_code == 200

def _check_control_post(client, ctrl, obj):
    href = obj["@controls"][ctrl]["href"]
    schema = obj["@controls"][ctrl]["schema"]
    
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "post"

    encoding = obj["@controls"][ctrl]["encoding"].lower()
    assert encoding == "json"

    if "movies" in obj:
        body = _get_movie_json()
    elif "reviews" in obj:
        body = _get_review_json()
    else:
        body = None

    validate(body, schema)
    response = client.post(href, json=body)
    assert response.status_code == 201

def _check_control_put(client, ctrl, obj):
    href = obj["@controls"][ctrl]["href"]
    schema = obj["@controls"][ctrl]["schema"]
    
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "put"

    encoding = obj["@controls"][ctrl]["encoding"].lower()
    assert encoding == "json"

    if "edit_movie" in obj["@controls"]:
        body = _get_movie_json()
        body["name"] = obj["data"]["name"]
    elif "edit_review" in obj["@controls"]:
        body = _get_review_json()
        body["reviewer"] = obj["data"]["reviewer"]
    else:
        body = None
    
    validate(body, schema)
    response = client.put(href, json=body)
    assert response.status_code == 204

def _check_control_delete(client, ctrl, obj):
    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"

    response = client.delete(href)
    assert response.status_code == 204

class TestMovieCollection(object):
    VALID_URL = "/api/movies/"
    VALID_METHODS = "GET, POST"

    def test_get(self, client):
        response = client.get(self.VALID_URL)
        assert response.status_code == 200
        body = json.loads(response.data)
        _check_namespace(client, body)
        _check_control_get(client, "superkinodb:actors", body)
        _check_control_get(client, "superkinodb:directors", body)
        _check_control_get(client, "superkinodb:writers", body)
        _check_control_post(client, "add_movie", body)
        assert len(body["movies"]) == 4

        for movie in body["movies"]:
            _check_control_get(client, "self", movie)

    def test_post(self, client):
        data = _get_movie_json()

        response = client.post(self.VALID_URL, data="random")
        assert response.status_code in (400, 415)

        response = client.post(self.VALID_URL, json=data)
        assert response.status_code == 201
        assert response.headers["Location"].endswith(self.VALID_URL +
                                                     data["name"] +
                                                     "/"
                                                     )
        response = client.get(response.headers["Location"])
        assert response.status_code == 200

        response = client.post(self.VALID_URL, json=data)
        assert response.status_code == 409

        data["name"] = None
        response = client.post(self.VALID_URL, json=data)
        assert response.status_code == 400

    def test_put(self, client):
        response = client.put(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

    def test_delete(self, client):
        response = client.delete(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

class TestMovieItem(object):
    VALID_URL = "/api/movies/test-movie-1/"
    INVALID_URL = "/api/movies/non-existent-1/"
    VALID_METHODS = "GET, PUT, DELETE"

    def test_get(self, client):
        response = client.get(self.VALID_URL)
        assert response.status_code == 200
        body = json.loads(response.data)
        _check_namespace(client, body)
        _check_control_get(client, "superkinodb:movies", body)
        _check_control_get(client, "reviews", body)
        _check_control_put(client, "edit_movie", body)
        _check_control_delete(client, "delete_movie", body)
        
        response = client.get(self.INVALID_URL)
        assert response.status_code == 404

    def test_post(self, client):
        response = client.post(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

    def test_put(self, client):
        data = _get_movie_json()

        response = client.put(self.VALID_URL, data="random")
        assert response.status_code in (400, 415)

        response = client.put(self.INVALID_URL, json=data)
        assert response.status_code == 404
        
        data["name"] = "test-movie-2"
        response = client.put(self.VALID_URL, json=data)
        assert response.status_code == 409

        data["name"] = "test-movie-1"
        response = client.put(self.VALID_URL, json=data)
        assert response.status_code == 204

        data["name"] = None
        response = client.put(self.VALID_URL, json=data)
        assert response.status_code == 400

    def test_delete(self, client):
        response = client.delete(self.VALID_URL)
        assert response.status_code == 204
        response = client.delete(self.INVALID_URL)
        assert response.status_code == 404

class TestReviewCollection(object):
    VALID_URL = "/api/movies/test-movie-1/reviews/"
    VALID_METHODS = "GET, POST"

    def test_get(self, client):
        response = client.get(self.VALID_URL)
        assert response.status_code == 200
        body = json.loads(response.data)
        _check_namespace(client, body)
        _check_control_get(client, "movie", body)
        _check_control_post(client, "add_review", body)
        assert len(body["reviews"]) == 3

        for review in body["reviews"]:
            _check_control_get(client, "self", review)

    def test_post(self, client):
        data = _get_review_json()

        response = client.post(self.VALID_URL, data="random")
        assert response.status_code in (400, 415)

        response = client.post(self.VALID_URL, json=data)
        assert response.status_code == 201
        assert response.headers["Location"].endswith(self.VALID_URL +
                                                     data["reviewer"] +
                                                     "/"
                                                     )
        response = client.get(response.headers["Location"])
        assert response.status_code == 200

        response = client.post(self.VALID_URL, json=data)
        assert response.status_code == 409

        data["reviewer"] = None
        response = client.post(self.VALID_URL, json=data)
        assert response.status_code == 400

        data["score"] = None
        response = client.post(self.VALID_URL, json=data)
        assert response.status_code == 400

    def test_put(self, client):
        response = client.put(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

    def test_delete(self, client):
        response = client.delete(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

class TestReviewItem(object):
    VALID_URL = "/api/movies/test-movie-1/reviews/test-reviewer-1/"
    INVALID_URL = "/api/movies/test-movie-1/reviews/non-existent-1/"
    VALID_METHODS = "GET, PUT, DELETE"

    def test_get(self, client):
        response = client.get(self.VALID_URL)
        assert response.status_code == 200
        body = json.loads(response.data)
        _check_namespace(client, body)
        _check_control_get(client, "review_collection", body)
        _check_control_put(client, "edit_review", body)
        _check_control_delete(client, "delete_review", body)
        
        response = client.get(self.INVALID_URL)
        assert response.status_code == 404

    def test_post(self, client):
        response = client.post(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

    def test_put(self, client):
        data = _get_review_json()

        response = client.put(self.VALID_URL, data="random")
        assert response.status_code in (400, 415)

        response = client.put(self.INVALID_URL, json=data)
        assert response.status_code == 404

        data["reviewer"] = "test-reviewer-2"
        response = client.put(self.VALID_URL, json=data)
        assert response.status_code == 409
        
        data["reviewer"] = "test-reviewer-1"
        response = client.put(self.VALID_URL, json=data)
        assert response.status_code == 204
        
        data["reviewer"] = None
        response = client.put(self.VALID_URL, json=data)
        assert response.status_code == 400
        
        data["score"] = None
        response = client.put(self.VALID_URL, json=data)
        assert response.status_code == 400

    def test_delete(self, client):
        response = client.delete(self.VALID_URL)
        assert response.status_code == 204
        response = client.delete(self.INVALID_URL)
        assert response.status_code == 404

class TestActorCollection(object):
    VALID_URL = "/api/actors/"
    VALID_METHODS = "GET"

    def test_get(self, client):
        response = client.post(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

    def test_put(self, client):
        response = client.put(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

    def test_delete(self, client):
        response = client.delete(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

class TestDirectorCollection(object):
    VALID_URL = "/api/directors/"
    VALID_METHODS = "GET"

    def test_get(self, client):
        response = client.post(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

    def test_put(self, client):
        response = client.put(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

    def test_delete(self, client):
        response = client.delete(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

class TestWriterCollection(object):
    VALID_URL = "/api/writers/"
    VALID_METHODS = "GET"

    def test_get(self, client):
        response = client.post(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

    def test_put(self, client):
        response = client.put(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS

    def test_delete(self, client):
        response = client.delete(self.VALID_URL)
        assert response.status_code == 405
        assert response.headers["Allow"] == self.VALID_METHODS
