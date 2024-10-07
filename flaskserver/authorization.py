from functools import wraps
import flask
from flask_jwt_extended import current_user, verify_jwt_in_request
from models import UserRole

# Grants access to users with at least one of "roles"
def allow(roles: list[str] = []):
    def decorator(f):
        @wraps(f)
        def decorator_function(*args, **kwargs):
            # calling @jwt_required()
            verify_jwt_in_request()
            # checking user role
            print(roles)
            print(UserRole.get_by_user_id(current_user.get_id))
            for user_role in UserRole.get_by_user_id(current_user.get_id):
                if user_role.get_rolename in roles:
                    return f(*args, **kwargs)
                return flask.jsonify({"msg": "Unauthorized"}), 401
        return decorator_function
    return decorator

# Denies access to users with at least one of "roles"
def deny(roles: list[str] = []):
    def decorator(f):
        @wraps(f)
        def decorator_function(*args, **kwargs):
            # calling @jwt_required()
            verify_jwt_in_request()
            # checking user role
            for user_role in UserRole.get_by_user_id(current_user.get_id):
                if user_role.get_rolename in roles:
                    return flask.jsonify({"msg": "Unauthorized"}), 401
                return f(*args, **kwargs)
        return decorator_function
    return decorator