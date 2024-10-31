from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import ForeignKeyConstraint, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import reconstructor
from core import Context

# Get the reference from Context
db = Context().db()

# Models
@dataclass
class User(db.Model):
    id: int = db.Column(db.Integer, primary_key = True)
    username: str = db.Column(db.String(30), unique = True, nullable = False)
    password: str = db.Column(db.String(100), nullable = False)
    datetime_added: datetime = db.Column(db.DateTime(timezone = True), server_default = func.now())

    # Acts as the default init
    @reconstructor
    def __init_on_load(self):
        '''self.is_authenticated: bool = False
        self.is_active: bool = True
        self.is_anonymous: bool = False'''

    @classmethod
    def get_by_id(cls, user_id: int) -> User:
        return User.query.filter_by(id = user_id).one_or_none()
    
    @classmethod
    def get_by_username(cls, username: str) -> User:
        return User.query.filter_by(username = username).one_or_none()
    
    def update_username(self, new_username: str) -> None:
        if len(new_username) < Context.min_username_length():
            raise UsernameTooShortException
        
        elif User.get_by_username(new_username) is not None:
            raise UsernameExistsException
        
        else:
            self.username = new_username
            db.session.commit()
    
    def update_password(self, new_password: str) -> None:
        if len(new_password) < Context.min_password_length():
            raise PasswordTooShortException
        
        else:
            self.password = Context.bcrypt().generate_password_hash(new_password)
            db.session.commit()

@dataclass
class Role(db.Model):
    rolename: str = db.Column(db.String(30), primary_key = True)

@dataclass
class UserRole(db.Model):
    user: int = db.Column(db.Integer, primary_key = True)
    role: str = db.Column(db.String(30), primary_key = True)
    __table_args__ = (
        ForeignKeyConstraint([user], [User.id]),
        ForeignKeyConstraint([role], [Role.rolename])
    )

    @classmethod
    def get_by_user_id(cls, user_id: int) -> list[UserRole]:
        return UserRole.query.filter_by(user = user_id).all()
    
    @hybrid_property
    def get_rolename(self) -> str:
        return self.role

@dataclass
class Task(db.Model):
    id: int = db.Column(db.Integer, primary_key = True)
    user: str = db.Column(db.String(20), unique = True, nullable = False)
    description: str = db.Column(db.String(200), nullable = False)
    completed: bool = db.Column(db.Boolean, default = False, nullable = False)
    __table_args__ = (
        ForeignKeyConstraint([user], [User.id]),
    )

    @classmethod
    def get_by_user_id(cls, user_id: int) -> list[str]:
        return Task.query.filter_by(user = user_id).all()
    

# Custom exceptions
class UsernameException(Exception):
    message: str = "The given username is invalid"

class UsernameExistsException (UsernameException):
    message: str = "The given username is already in use"

class UsernameTooShortException (UsernameException):
    message: str = f"The given username must be at least {Context.min_username_length()} characters long"

class PasswordTooShortException (Exception):
    message: str = f"The given password must be at least {Context.min_password_length()} characters long"