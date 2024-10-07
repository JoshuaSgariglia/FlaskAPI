import flask
from flask_jwt_extended import current_user, jwt_required
import requests

from authorization import allow, deny
from models import Task, User

# Define Blueprint
bp = flask.Blueprint('api', __name__)

# Base route
@bp.route('/')
def testdb():
    user_dict: dict = User.query.all()[0].__dict__
    user_dict.pop("_sa_instance_state")
    return user_dict

# Route to get sensor info
@bp.route("/get_sensor_info", methods=["GET"])
@jwt_required()
def get_sensor_info():
    try:
        print(flask.jsonify(requests.get(url="http://192.168.104.78:5000/api/data?sensor_id=http:%2F%2Fhomey\%2Fexample_graph%2Fsensor_mix_kitchen")))
    except Exception as e:
        print(e)

    return {}, 200

# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
@bp.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    return flask.jsonify(logged_in_as = current_user.username), 200


# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
@bp.route("/teachers_only", methods=["GET"])
@allow(roles = ["Professore", "Direttore"])
def teachers_only():
    # Access the identity of the current user with get_jwt_identity
    return flask.jsonify(msg = current_user.username + " entered the teachers area"), 200

# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
@bp.route("/public", methods=["GET"])
@allow(roles = ["Studente", "Professore", "Direttore"])
def public():
    # Access the identity of the current user with get_jwt_identity
    return flask.jsonify(msg = current_user.username + " entered the public area"), 200

# Get user tasks
@bp.route("/user_tasks", methods=["GET"])
@jwt_required()
def get_user_tasks():
    return flask.jsonify(Task.get_by_user_id(current_user.get_id)), 200


