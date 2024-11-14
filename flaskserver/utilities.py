from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from core import Context
from models import UserRole

# Redis utilities
class RedisUtils:
    # Generates the redis key for the access 
    @classmethod
    def get_access_token_key(cls, user_id: int) -> str:
        return f"user_{user_id}:access_token_identifier"
    
    # Generates the redis key for the refresh token
    @classmethod
    def get_refresh_token_key(cls, user_id: int) -> str:
        return f"user_{user_id}:refresh_token_identifier"
    
    # Generates the redis key for the roles
    @classmethod
    def get_roles_key(cls, user_id: int) -> str:
        return f"user_{user_id}:roles"
    
    # Returns the access token for the specified user
    @classmethod
    def get_access_token(cls, user_id: int) -> str:
        return Context.redis().get(cls.get_access_token_key(user_id))
    
    # Returns the refresh token for the specified user
    @classmethod
    def get_refresh_token(cls, user_id: int) -> str:
        return Context.redis().get(cls.get_refresh_token_key(user_id))

    # Saves access token to Redis database
    @classmethod
    def save_access_token(cls, user_id: int, token: str):
        Context.redis().set(cls.get_access_token_key(user_id), decode_token(token)["jti"], ex=Context.app().config["JWT_ACCESS_TOKEN_EXPIRES"])

    # Saves refresh token to Redis database
    @classmethod
    def save_refresh_token(cls, user_id: int, token: str):
        Context.redis().set(cls.get_refresh_token_key(user_id), decode_token(token)["jti"], ex=Context.app().config["JWT_REFRESH_TOKEN_EXPIRES"])

    # Saves access and refresh tokens to Redis database
    @classmethod
    def save_tokens(cls, user_id: int, access_token: str, refresh_token: str):
        cls.save_access_token(user_id, access_token)
        cls.save_refresh_token(user_id, refresh_token)

    # Deletes any saved tokens for the provided user
    @classmethod
    def delete_tokens(cls, user_id: int):
        Context.redis().delete(cls.get_access_token_key(user_id), cls.get_refresh_token_key(user_id))

    # Add roles to the list of roles for a user
    @classmethod
    def get_roles(cls, user_id: int) -> list[str]:
        roles_key = cls.get_roles_key(user_id)
        return Context.redis().lrange(roles_key, 0, Context.redis().llen(roles_key))

    # Add roles to the list of roles for a user
    @classmethod
    def add_roles(cls, user_id: int, roles: list[str]):
        Context.redis().rpush(cls.get_roles_key(user_id), *roles)

    # Deletes a list of roles for a user
    @classmethod
    def delete_roles(cls, user_id: int):
        Context.redis().delete(cls.get_roles_key(user_id))

    # Set a new list of roles for a user
    @classmethod
    def set_roles(cls, user_id: int, roles: list[str]):
        cls.delete_roles(user_id)
        cls.add_roles(user_id, roles)
        Context.redis().expire(cls.get_roles_key(user_id), Context.app().config["JWT_REFRESH_TOKEN_EXPIRES"] + Context.app().config["JWT_ACCESS_TOKEN_EXPIRES"])


# Flask utilities
class FlaskUtils:
    # Generates a new access token and saves it to Redis database
    @classmethod
    def generate_access_token(cls, user_id: int, fresh: bool = False) -> str:
        # Creates new access token
        access_token = create_access_token(identity = user_id, fresh = fresh)

        # Saves access token to redis database
        RedisUtils.save_access_token(user_id, access_token)

        return access_token

    # Generates a new refresh token and saves it to Redis database
    @classmethod
    def generate_refresh_token(cls, user_id: int) -> str:
        # Creates new refresh token
        refresh_token = create_refresh_token(identity = user_id)

        # Saves refresh token to redis database
        RedisUtils.save_refresh_token(user_id, refresh_token)

        return refresh_token

    # Generates new access and refresh tokens and saves them to Redis database
    @classmethod
    def generate_tokens(cls, user_id: int, fresh_access_token: bool = False) -> tuple[str]:
        access_token = cls.generate_access_token(user_id, fresh_access_token)
        refresh_token = cls.generate_refresh_token(user_id)
        return access_token, refresh_token
    
    # Saves user roles that are stored in SQL database in Redis
    @classmethod
    def save_roles_in_redis(cls, user_id: int):
        RedisUtils.set_roles(user_id, UserRole.get_rolenames_by_user_id(user_id))