import flask
from flask_jwt_extended import current_user as current_user_id
import requests
from authorization import allow, deny
from authentication import verify_token
from utilities import RedisUtils
from models import Machine, PasswordTooShortException, Role, UsernameException
from models import Task, User, UserRole

# Define Blueprint
bp = flask.Blueprint('api', __name__)

# Base route
@bp.route('/')
def test_connection():
    return flask.jsonify(message = "Authentication Service is online")

# Protect a route with verify_token, which will kick out requests
# without a valid JWT present.


# Management Routes

# Get user data
@bp.route("/user-data", methods=["GET"])
@verify_token()
def user_data():
    # Gets basic data
    user_dict: dict[str, any] = User.get_current_user().__dict__
    user_dict.pop("password")
    user_dict.pop("_sa_instance_state")

    # Gets roles
    user_dict["role_list"] = RedisUtils.get_roles(current_user_id)
    
    return flask.jsonify(user_dict), 200

# Only fresh JWTs can access this endpoint
@bp.route('/update-username', methods=['PUT'])
@verify_token(fresh = True)
def update_username():
    # Get the args
    print()
    username = flask.request.data.decode("utf-8")

    try:
        User.get_current_user().update_username(username)
        
    except UsernameException as exception:
        return flask.jsonify(msg = exception.message, exceptionType = exception.__class__.__name__), 400

    return flask.jsonify(msg = "Username updated successfully"), 200

# Only fresh JWTs can access this endpoint
@bp.route('/update-password', methods=['PUT'])
@verify_token(fresh = True)
def update_password():
    # Get the args
    password = flask.request.data.decode("utf-8")

    try: 
        User.get_current_user().update_password(password)
        
    except PasswordTooShortException as exception:
        return flask.jsonify(msg = exception.message, exceptionType = exception.__class__.__name__), 400

    return flask.jsonify(msg = "Password updated successfully"), 200

# Get user tasks
@bp.route("/user-tasks", methods=["GET"])
@verify_token()
def get_user_tasks():
    return flask.jsonify(Task.get_by_user_id_and_area_id(current_user_id, flask.request.args.get("area_id"))), 200

# Update user task
@bp.route("/user-task-update", methods=["PUT"])
@verify_token()
def update_user_task_state():
    # Get the args
    data: dict[str, any] = eval(flask.request.data.decode("utf-8"))
    task_id: int = data.get("task_id")
    completed: bool = data.get("completed")

    # Searches for the task
    task: Task = Task.get_by_id(task_id)

    # A user is only allowed to edit his tasks
    if task.user != current_user_id:
        return flask.jsonify(msg = "Not allowed to modify the requested user task"), 403

    # Updates the task state in the database
    task.set_completed(completed)

    # Informs the use that the operation was successful
    return flask.jsonify(msg = "Task state updated successfully"), 200

# Create and save a new user in the database
@bp.route("/insert-user", methods=["POST"])
@allow(roles = ["Titolare", "Amministratore di sistema"])
def insert_user():
    # Get body data
    # Get the args
    args = flask.request.form
    username = args.get("username", None)
    password = args.get("password", None)
    rolename = args.get("rolename", None)
    try:
        # Username and password can't be None
        if username is None:
            return flask.jsonify(msg = "Bad request: missing username field"), 400
        
        if password is None:
            return flask.jsonify(msg = "Bad request: missing password field"), 400

        # Insert new user
        new_user_id: int = User.insert(username, password)

        # Insert new role if it is not None
        if rolename is not None:

            # Insert new role if it doesn't exist
            if not Role.exists(rolename):
                Role.insert(rolename)
            
            # Assign that role to the new user
            UserRole.insert(new_user_id, rolename)
        
    except (UsernameException, PasswordTooShortException) as exception:
        return flask.jsonify(msg = exception.message, exceptionType = exception.__class__.__name__), 400

    return flask.jsonify(msg = "User account created successfully"), 200

# Get machine data
@bp.route("/machines", methods=["GET"])
@allow("Dipendente", "Titolare", "Amministratore di sistema")
def get_machines_by_area():
    return flask.jsonify(Machine.get_by_area_id(flask.request.args.get("area_id"))), 200


# API Routes

# Route to access Monitoring API
@bp.route("/monitoring", methods=["GET"])
@allow("Dipendente", "Titolare", "Amministratore di sistema")
def monitoring():
    url = f"http://193.205.129.120:63429/api/data"
    print(f"Sensor data requested from {url}")

    # Gets streams from API monitoring server
    response = requests.get(url, flask.request.args, stream = True)
    
    # Acts like a Proxy and returns same stream response
    return flask.Response(response.iter_content(), content_type = response.headers['Content-Type'])

# Route to access Querying API
@bp.route("/querying", methods=["GET"])
@allow("Dipendente", "Titolare", "Amministratore di sistema")
def querying():
    url = f"http://193.205.129.120:63429/api/data"
    print(f"Sensor data requested from {url}")

    # Gets streams from API querying server
    response = requests.get(url, flask.request.args)
    
    # Acts like a Proxy and returns same stream response
    return flask.Response(response, content_type = response.headers['Content-Type'])

