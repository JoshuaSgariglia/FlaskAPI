from datetime import timedelta
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from redis import StrictRedis


# Singleton superclass
class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# Context class   
class Context(metaclass = SingletonMeta):
    __app: Flask = None
    __db: SQLAlchemy = None
    __jwt: JWTManager = None
    __bcrypt: Bcrypt = None
    __redis: StrictRedis = None

    def __init__(self):
        ApplicationInitializer.initialize()
        print(f"Initialization completed")

    @classmethod
    def initialize(cls, app: Flask, db: SQLAlchemy, jwt: JWTManager, bcrypt: Bcrypt, redis: StrictRedis):
        # Initialize the class variables
        cls.__app = app
        cls.__db = db
        cls.__jwt = jwt
        cls.__bcrypt = bcrypt
        cls.__redis = redis

    @classmethod
    def app(cls) -> Flask:
        return cls.__app
    
    @classmethod
    def db(cls) -> SQLAlchemy:
        return cls.__db
    
    @classmethod
    def jwt(cls) -> JWTManager:
        return cls.__jwt
    
    @classmethod
    def bcrypt(cls) -> Bcrypt:
        return cls.__bcrypt
    
    @classmethod
    def redis(cls) -> StrictRedis:
        return cls.__redis


# ApplicationInitializer class  
class ApplicationInitializer:
    @classmethod
    def initialize(cls):
        # Initialize the Flask library
        app = Flask(__name__)

        # Initialize the database
        app.config['SECRET_KEY'] = 'LzLIDNOvsfDEwqXogc6CNhjXkJn1C7mx'

        USERPASS = 'mysql+pymysql://root:@'
        BASEDIR  = '127.0.0.1'
        DBNAME   = '/flask_db'
        #SOCKET   = '?unix_socket=/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock'

        app.config['SQLALCHEMY_DATABASE_URI'] = USERPASS + BASEDIR + DBNAME
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

        db = SQLAlchemy(app)

        # Initialize the Authentication module
        app.config["JWT_SECRET_KEY"] = '5PJijcrNhrXNaCqeJ4KJmMRBlu7iUAPc'
        app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours = 1)
        app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days = 30)
        
        jwt = JWTManager(app)

        # Initialize the Password Hashing module
        bcrypt = Bcrypt(app)

        # Setup our redis connection for storing the blocklisted tokens. You will probably
        # want your redis instance configured to persist data to disk, so that a restart
        # does not cause your application to forget that a JWT was revoked.
        redis = StrictRedis(
            host="redis-13586.c91.us-east-1-3.ec2.redns.redis-cloud.com", 
            port=13586, 
            db=0, 
            username="default",
            password="3LSmYtaQ22Zhtd7g2wcBlVInlLVrSVrJ",
            decode_responses=True
        )

        # Initialize the Context with the Flask app and the database
        Context.initialize(app, db, jwt, bcrypt, redis)
