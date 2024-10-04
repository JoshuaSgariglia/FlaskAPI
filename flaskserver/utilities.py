from datetime import timedelta
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy


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

    def __init__(self):
        ApplicationInitializer.initialize()
        print("Initialization completed")

    @classmethod
    def initialize(cls, app: Flask, db: SQLAlchemy, jwt: JWTManager):
        # Initialize the class variables
        cls.__app = app
        cls.__db = db
        cls.__jwt = jwt

    @classmethod
    def app(cls):
        return cls.__app
    
    @classmethod
    def db(cls):
        return cls.__db
    
    @classmethod
    def jwt(cls):
        return cls.__jwt


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
        app.config["JWT_SECRET_KEY"] = app.config['SECRET_KEY']
        app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours = 1)
        app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days = 30)
        
        jwt = JWTManager(app)

        # Initialize the Context with the Flask app and the database
        Context.initialize(app, db, jwt)
