
import flask
from http_utils import url_has_allowed_host_and_scheme
from flask_jwt_extended import create_access_token, create_refresh_token, current_user, get_jwt, jwt_required
from models import User
from utilities import Context

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

# Callback function to check if a JWT exists in the redis blocklist
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
    jti = jwt_payload["jti"]
    token_in_redis = Context.redis().get(jti)
    return token_in_redis is not None  # Must return TRUE if revoked


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

        access_token = create_access_token(identity = user)
        refresh_token = create_refresh_token(identity = user)

        return flask.jsonify(access_token = access_token, refresh_token = refresh_token), 200

    return flask.jsonify({"msg": "Bad username or password"}), 401

# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
@bp.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    return flask.jsonify(logged_in_as = current_user.username), 200

# We are using the `refresh=True` options in jwt_required to only allow
# refresh tokens to access this route.
@bp.route("/refresh", methods=["POST"])
@jwt_required(refresh = True)
def refresh():
    access_token = create_access_token(identity = current_user)
    return flask.jsonify(access_token = access_token), 200

# Endpoint for revoking the current users access token. Save the JWTs unique
# identifier (jti) in redis. Also set a Time to Live (TTL)  when storing the JWT
# so that it will automatically be cleared out of redis after the token expires.
@bp.route("/logout", methods=["DELETE"])
@jwt_required(optional = False)
def logout():
    jti = get_jwt()["jti"]
    Context.redis().set(jti, current_user.get_id, ex=Context.app().config["JWT_ACCESS_TOKEN_EXPIRES"])
    return flask.jsonify(msg="Access token revoked")