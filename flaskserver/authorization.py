from functools import wraps
import flask
from flask_jwt_extended import current_user
from flask_jwt_extended.view_decorators import LocationType
from authentication import verify_token
from utilities import RedisUtils
from models import UserRole


# Decorators

# Grants access to users with at least one of "roles"
def allow(
        roles: list[str] = [], 
        optional: bool = False, 
        fresh: bool = False, 
        refresh: bool = False, 
        locations: LocationType = None,
        verify_type: bool = True,
        skip_revocation_check: bool = True  # Recommended method not implemented because it is based on a blocklist
        ):
    def decorator(f):
        @wraps(f)
        @verify_token(optional, fresh, refresh, locations, verify_type, skip_revocation_check)
        def decorator_function(*args, **kwargs):
            # Checking user role
            print(roles)
            print(RedisUtils.get_roles(current_user))
            for user_role in RedisUtils.get_roles(current_user):
                if user_role in roles:
                    return f(*args, **kwargs)
            return flask.jsonify(msg = "Unauthorized"), 401
        return decorator_function
    return decorator

# Denies access to users with at least one of "roles"
def deny(
        roles: list[str] = [], 
        optional: bool = False, 
        fresh: bool = False, 
        refresh: bool = False, 
        locations: LocationType = None,
        verify_type: bool = True,
        skip_revocation_check: bool = True  # Recommended method not implemented because it is based on a blocklist
        ):
    def decorator(f):
        @wraps(f)
        @verify_token(optional, fresh, refresh, locations, verify_type, skip_revocation_check)
        def decorator_function(*args, **kwargs):
            # Checking user role
            for user_role in RedisUtils.get_roles(current_user):
                if user_role in roles:
                    return flask.jsonify(msg = "Unauthorized"), 401
            return f(*args, **kwargs)
        return decorator_function
    return decorator