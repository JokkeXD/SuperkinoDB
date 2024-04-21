import json
from flask import Response, request, url_for
from superkinodb import db
from superkinodb.db_models import *

class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

class SuperkinodbBuilder(MasonBuilder):

    def add_control_all_movies(self):
        self.add_control(
            "superkinodb:movies",
            url_for("api.moviecollection"),
            title="All movies"
        )
    def add_control_all_actors(self):
        self.add_control(
            "superkinodb:actors",
            url_for("api.actorcollection"),
            title="All actors"
        )
    def add_control_all_directors(self):
        self.add_control(
            "superkinodb:directors",
            url_for("api.directorcollection"),
            title="All directors"
        )
    def add_control_all_writers(self):
        self.add_control(
            "superkinodb:writers",
            url_for("api.writercollection"),
            title="All writers"
        )
    def add_control_add_movie(self):
        self.add_control(
            "add_movie",
            url_for("api.moviecollection"),
            method="POST",
            encoding="json",
            title="Add a movie to the database",
            schema=Movie.get_schema()
        )
    def add_control_edit_movie(self, movie_item):
        self.add_control(
            "edit_movie",
            url_for("api.moviecollection", movie=movie_item),
            method="PUT",
            encoding="json",
            title="Edit a movie in the database",
            schema=Movie.get_schema()
        )
    def add_control_delete_movie(self, movie_item):
        self.add_control(
            "delete_movie",
            url_for("api.moviecollection", movie=movie_item),
            method="DELETE",
            title="Delete a movie from the database"
        )
    def add_control_movie_reviews(self, movie_item):
        self.add_control(
            "reviews",
            url_for("api.reviewcollection", movie=movie_item),
            title="Movie review collection"
        )
    def add_control_add_review(self, movie_item):
        self.add_control(
            "add_review",
            url_for("api.reviewcollection", movie=movie_item),
            encoding="json",
            title="Add review",
            schema=Review.get_schema()
        )
    def add_control_edit_review(self, movie_item, review_item):
        self.add_control(
            "edit_review",
            url_for("api.reviewitem", movie=movie_item, review=review_item),
            method="PUT",
            encoding="json",
            title="Edit review",
            schema=Review.get_schema()
        )
    def add_control_delete_review(self, movie_item, review_item):
        self.add_control(
            "delete_review",
            url_for("api.reviewitem", movie=movie_item, review=review_item),
            method="DELETE",
            title="Delete review"
        )
def error_response(status_code, text, error_message):
    url = request.url
    body = MasonBuilder(url=url)
    body.add_error(text, error_message)
    return Response(json.dumps(body), status_code)

def add_person(PersonObject, name):
    person = PersonObject(
        name=name
    )
    db.session.add(person)
    return person

def cleanup_personnel(PersonObject):
    orphans = PersonObject.query.filter(~PersonObject.movies.any()).all()
    if orphans:
        for orphan in orphans:
            db.session.delete(orphan)
    return

