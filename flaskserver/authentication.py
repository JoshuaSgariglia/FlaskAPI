from functools import wraps
import flask
from flask_jwt_extended import current_user as current_user_id, get_jwt, jwt_required
from flask_jwt_extended.view_decorators import LocationType
from models import User
from core import Context
from utilities import FlaskUtils, RedisUtils

# Define Blueprint
bp = flask.Blueprint('authentication', __name__)

# Get the references to JWT and Redis
jwt = Context().jwt()


# Callbacks

# Register a callback function that takes whatever object is passed in as the
# identity when creating JWTs and converts it to a JSON serializable format.
@jwt.user_identity_loader
def user_identity_lookup(user_id: int) -> int:
    return user_id

# Register a callback function that loads the user id whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason.
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data) -> int:
    return jwt_data["sub"]


# Decorators

# Function to check if a provided JWT is valid and exists in the redis database (not revoked)
def verify_token(
        optional: bool = False, 
        fresh: bool = False, 
        refresh: bool = False, 
        locations: LocationType = None,
        verify_type: bool = True,
        skip_revocation_check: bool = True  # Recommended method not implemented because it is based on a blocklist
        ):
    def decorator(f):
        @wraps(f)
        @jwt_required(optional, fresh, refresh, locations, verify_type, skip_revocation_check)
        def decorator_function(*args, **kwargs):
            # Checking if token is revoked
            # Getting access or refresh token - Access\refresh token is not present in Redis if revoked or expired
            token_in_redis = RedisUtils.get_refresh_token(current_user_id) if refresh else RedisUtils.get_access_token(current_user_id)

            # Getting the provided token
            token_provided = get_jwt()["jti"]

            if token_in_redis is None or token_in_redis != token_provided:  # Must evaluate to TRUE if revoked
                return flask.jsonify(message = "Token has been revoked"), 401
            return f(*args, **kwargs)
        return decorator_function
    return decorator


# Routes

# Login route
@bp.route('/login', methods=['POST'])
def login():

    # Get the args
    args = flask.request.form
    username = args.get("username", None)
    password = args.get("password", None)

    print(args.__str__())

    user: User = User.get_by_username(username)

    if user is not None and Context.bcrypt().check_password_hash(user.password, password):

        # Creates and stores\overrides the access token and refresh token
        access_token, refresh_token = FlaskUtils.generate_tokens(user.id, True)  # Fresh access token

        # Saves user roles that are stored in SQL database in Redis
        FlaskUtils.cache_roles_in_redis(user.id)

        return flask.jsonify(access_token = access_token, refresh_token = refresh_token), 200

    return flask.jsonify(msg = "Bad username or password"), 401

# Fresh login endpoint. This is designed to be used if we need to
# make a fresh token for a user (by verifying they have the
# correct username and password). Unlike the standard login endpoint,
# this will only return a new access token, so that we don't keep
# generating new refresh tokens, which entirely defeats their point.
@bp.route('/fresh-login', methods=['POST'])
def fresh_login():
    
    # Get the args
    args = flask.request.form
    username = args.get("username", None)
    password = args.get("password", None)

    user: User = User.get_by_username(username)

    if user is not None and Context.bcrypt().check_password_hash(user.password, password):

        # Creates and stores\overrides the access token
        access_token = FlaskUtils.generate_access_token(user.id, True)  # Fresh access token
        
        # Saves user roles that are stored in SQL database in Redis
        FlaskUtils.cache_roles_in_redis(user.id)

        return flask.jsonify(access_token = access_token), 200

    return flask.jsonify(msg = "Bad username or password"), 401

# Refresh token endpoint. This will generate a new access token from
# the refresh token, but will mark that access token as non-fresh,
# as we do not actually verify a password in this endpoint.
# We are using the "refresh=True" option in verify_token to only allow
# refresh tokens to access this route.
@bp.route("/refresh", methods=["GET", "POST"])
@verify_token(refresh = True)
def refresh():
    # Creates and stores\overrides the access token
    access_token = FlaskUtils.generate_access_token(int(current_user_id), False)  # Non-fresh access token
    
    return flask.jsonify(access_token = access_token), 200

# Endpoint for revoking the current users access and refresh tokens.
@bp.route("/logout", methods=["DELETE"])
@verify_token()
def logout():
    # Revokes both the access and the refresh tokens
    RedisUtils.delete_tokens(current_user_id)

    # Deletes the list of roles of the user
    RedisUtils.delete_roles(current_user_id)

    return flask.jsonify(msg = "Access and refresh tokens revoked")