
from functools import wraps
import flask
from http_utils import url_has_allowed_host_and_scheme
from flask_jwt_extended import create_access_token, create_refresh_token, current_user, decode_token, get_jti, get_jwt, jwt_required, verify_jwt_in_request
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
def user_identity_lookup(user: User) -> int:
    return user.get_id

# Register a callback function that loads a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data) -> User:
    identity = jwt_data["sub"]
    return User.query.filter_by(id = identity).one_or_none()



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
        def decorator_function(*args, **kwargs):
            # Calling @jwt_required()
            verify_jwt_in_request(optional, fresh, refresh, locations, verify_type, skip_revocation_check)

            # Checking if token is revoked
            # Getting access or refresh token - Access\refresh token is not present in Redis if revoked or expired
            token_in_redis = RedisUtils.get_refresh_token(current_user) if refresh else RedisUtils.get_access_token(current_user)

            # Getting the provided token
            token_provided = get_jwt()["jti"]

            if token_in_redis is None or token_in_redis != token_provided:  # Must evaluate to TRUE if revoked
                return flask.jsonify({"msg": "Token has been revoked"}), 401
            return f(*args, **kwargs)
        return decorator_function
    return decorator


# Routes

# Login route
@bp.route('/login', methods=['GET', 'POST'])
def login():

    # Get the args
    args = flask.request.args
    username = args.get("username", None)
    password = args.get("password", None)

    user: User = User.query.filter_by(username = username).first()

    if user is not None and Context.bcrypt().check_password_hash(user.password, password):

        '''next = args.get('next', None)

        if next is not None:
            # url_has_allowed_host_and_scheme should check if the url is safe
            # for redirects, meaning it matches the request host.
            if not url_has_allowed_host_and_scheme(next, flask.request.host):
                return flask.abort(400)

            return flask.redirect(next, methods = ["GET"])'''

        # Creates and stores\overrides the access token access and refresh tokens
        access_token, refresh_token = FlaskUtils.generate_tokens(user)

        return flask.jsonify(access_token = access_token, refresh_token = refresh_token), 200

    return flask.jsonify({"msg": "Bad username or password"}), 401

# We are using the `refresh=True` option in jwt_required to only allow
# refresh tokens to access this route.
@bp.route("/refresh", methods=["POST"])
@verify_token(refresh = True)
def refresh():
    # Creates and stores\overrides the access token
    access_token = FlaskUtils.generate_access_token(current_user)
    
    return flask.jsonify(access_token = access_token), 200

# Endpoint for revoking the current users access and refresh tokens.
@bp.route("/logout", methods=["DELETE"])
@verify_token()
def logout():
    # Revokes both the access and the refresh tokens
    RedisUtils.delete_tokens(current_user)

    return flask.jsonify(msg="Access and refresh tokens revoked")