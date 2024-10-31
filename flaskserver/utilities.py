from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from core import Context
from models import User

# Redis utilities
class RedisUtils:
    # Generates the redis key for the access 
    @classmethod
    def get_access_token_key(cls, user: User) -> str:
        return f"user_{user.id}:access_token_identifier"
    
    # Generates the redis key for the refresh token
    @classmethod
    def get_refresh_token_key(cls, user: User) -> str:
        return f"user_{user.id}:refresh_token_identifier"
    
    # Returns the access token for the specified user
    @classmethod
    def get_access_token(cls, user: User) -> str:
        return Context.redis().get(cls.get_access_token_key(user))
    
    # Returns the refresh token for the specified user
    @classmethod
    def get_refresh_token(cls, user: User) -> str:
        return Context.redis().get(cls.get_refresh_token_key(user))

    # Saves access token to Redis database
    @classmethod
    def save_access_token(cls, user: User, token: str):
        Context.redis().set(cls.get_access_token_key(user), decode_token(token)["jti"], ex=Context.app().config["JWT_ACCESS_TOKEN_EXPIRES"])

    # Saves refresh token to Redis database
    @classmethod
    def save_refresh_token(cls, user: User, token: str):
        Context.redis().set(cls.get_refresh_token_key(user), decode_token(token)["jti"], ex=Context.app().config["JWT_REFRESH_TOKEN_EXPIRES"])

    # Saves access and refresh tokens to Redis database
    @classmethod
    def save_tokens(cls, user: User, access_token: str, refresh_token: str):
        user_id = user.id
        cls.save_access_token(user_id, access_token)
        cls.save_refresh_token(user_id, refresh_token)

    # Deletes any saved tokens for the provided user
    @classmethod
    def delete_tokens(cls, user: User):
        user_id = user.id
        Context.redis().delete(cls.get_access_token_key(user), cls.get_refresh_token_key(user))


# Flask utilities
class FlaskUtils:
    # Generates a new access token and saves it to Redis database
    @classmethod
    def generate_access_token(cls, user: User, fresh: bool = False) -> str:
        # Creates new access token
        access_token = create_access_token(identity = user, fresh = fresh)

        # Saves access token to redis database
        RedisUtils.save_access_token(user, access_token)

        return access_token

    # Generates a new refresh token and saves it to Redis database
    @classmethod
    def generate_refresh_token(cls, user: User) -> str:
        # Creates new refresh token
        refresh_token = create_refresh_token(identity = user)

        # Saves refresh token to redis database
        RedisUtils.save_refresh_token(user, refresh_token)

        return refresh_token

    # Generates new access and refresh tokens and saves them to Redis database
    @classmethod
    def generate_tokens(cls, user: User, fresh_access_token: bool = False) -> tuple[str]:
        access_token = cls.generate_access_token(user, fresh_access_token)
        refresh_token = cls.generate_refresh_token(user)
        return access_token, refresh_token


# Custom exceptions
class UsernameExistsException (Exception):
    message: str = "The given username is already in use"

