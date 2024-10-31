import flask
from flask_jwt_extended import current_user
import requests
from authorization import allow, deny
from authentication import verify_token
from models import PasswordTooShortException, UsernameException
from models import Task, User, UserRole

# Define Blueprint
bp = flask.Blueprint('api', __name__)

# Base route
@bp.route('/')
def test_connection():
    return flask.jsonify(message = "Authentication Service is online")

# Protect a route with verify_token, which will kick out requests
# without a valid JWT present.

# Get user data
@bp.route("/user-data", methods=["GET"])
@verify_token()
def user_data():
    # Gets basic data
    user_dict: dict[str, any] = current_user.__dict__
    user_dict.pop("password")
    user_dict.pop("_sa_instance_state")

    # Gets roles
    role_list: list[UserRole] = UserRole.get_by_user_id(current_user.id)
    rolenames: list[str] = []
    for role in role_list:
        rolenames.append(role.get_rolename)
    user_dict["role_list"] = rolenames
    
    return flask.jsonify(user_dict), 200

# Route to get sensor info
@bp.route("/get-sensor-info", methods=["GET"])
@verify_token()
def get_sensor_info():

    url = "http://193.205.129.120:63429/api/data?sensor_id=http:%2F%2Fhomey%2Fexample_graph%2Fsensor_mix_kitchen"
    print(f"Sensor data requested from {url}")

    # Gets streams from API monitoring server
    response = requests.get(url, stream = True)
    
    # Acts like a Proxy and returns same stream response
    return flask.Response(response.iter_content(), content_type = response.headers['Content-Type'])

# Route potected with token and role
@bp.route("/teachers-only", methods=["GET"])
@allow(roles = ["Professore", "Direttore"])
def teachers_only():
    # Access the identity of the current user with get_jwt_identity
    return flask.jsonify(message = current_user.username + " entered the teachers area"), 200

# Route protected with token and role
@bp.route("/public", methods=["GET"])
@allow(roles = ["Studente", "Professore", "Direttore"])
def public():
    # Access the identity of the current user with get_jwt_identity
    return flask.jsonify(message = current_user.username + " entered the public area"), 200

# Get user tasks
@bp.route("/user-tasks", methods=["GET"])
@verify_token()
def get_user_tasks():
    return flask.jsonify(Task.get_by_user_id(current_user.id)), 200

# Only fresh JWTs can access this endpoint
@bp.route('/update-username', methods=['PUT'])
@verify_token(fresh = True)
def update_username():
    # Get the args
    args = flask.request.form
    username = args.get("username", None)

    try:
        current_user.update_username(username)
        
    except UsernameException as exception:
        return flask.jsonify(message = exception.message), 400

    return flask.jsonify(message = "Username updated successfully"), 200

# Only fresh JWTs can access this endpoint
@bp.route('/update-password', methods=['PUT'])
@verify_token(fresh = True)
def update_password():
    # Get the args
    args = flask.request.form
    password = args.get("password", None)

    try: 
        current_user.update_password(password)
        
    except PasswordTooShortException as exception:
        return flask.jsonify(message = exception.message), 400

    return flask.jsonify(message = "Password updated successfully"), 200


