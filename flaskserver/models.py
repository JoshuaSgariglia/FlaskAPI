from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from flask_jwt_extended import current_user as current_user_id
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import reconstructor
from core import Context

# Get the references from Context
db = Context().db()
bcrypt = Context().bcrypt()

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
    
    @classmethod
    def get_current_user(cls) -> User:
        return User.get_by_id(current_user_id)
    
    @classmethod
    def insert(cls, username: str, password: str) -> int:
        if len(username) < Context.min_username_length():
            raise UsernameTooShortException
        
        elif User.get_by_username(username) is not None:
            raise UsernameExistsException
        
        else:
            new_user = User(username = username, password = bcrypt.generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            return new_user.id
    
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

    @classmethod
    def get_by_rolename(cls, rolename: str) -> Role:
        return Role.query.filter_by(rolename = rolename).one_or_none()

    @classmethod
    def get_rolenames(cls) -> list[str]:
        return [role.rolename for role in Role.query.all()]
    
    @classmethod
    def exists(cls, rolename: str) -> bool:
        return Role.get_by_rolename(rolename) is not None
    
    @classmethod
    def insert(cls, rolename: str) -> None:
        new_role = Role(rolename = rolename)
        db.session.add(new_role)
        db.session.commit()

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
    
    @classmethod
    def get_rolenames_by_user_id(cls, user_id: int) -> list[str]:
        return [role.role for role in UserRole.get_by_user_id(user_id)]
    
    @classmethod
    def insert(cls, user_id: int, rolename: str) -> None:
        new_user_role = UserRole(user = user_id, role = rolename)
        db.session.add(new_user_role)
        db.session.commit()

@dataclass
class Task(db.Model):
    id: int = db.Column(db.Integer, primary_key = True)
    area: int = db.Column(db.Integer, nullable = False)
    user: str = db.Column(db.String(20), nullable = False)
    description: str = db.Column(db.String(200), nullable = False)
    completed: bool = db.Column(db.Boolean, default = False, nullable = False)
    __table_args__ = (
        UniqueConstraint("area", "user", "description"),
        ForeignKeyConstraint([user], [User.id]),
    )

    @classmethod
    def get_by_id(cls, task_id: int) -> Task:
        return Task.query.filter_by(id = task_id).one_or_none()

    @classmethod
    def get_by_user_id(cls, user_id: int) -> list[Task]:
        return Task.query.filter_by(user = user_id).all()
    
    @classmethod
    def get_by_user_id_and_area_id(cls, user_id: int, area_id: int) -> list[Task]:
        return Task.query.filter_by(user = user_id, area = area_id).all()
    
    def set_completed(self, completed: bool) -> None:
        self.completed = completed
        db.session.commit()
    
@dataclass
class Machine(db.Model):
    id: int = db.Column(db.Integer, primary_key = True)
    area: int = db.Column(db.Integer, nullable = False)
    model: str = db.Column(db.String(50), nullable = False)
    serial: str = db.Column(db.String(20), nullable = False)
    type: str = db.Column(db.String(40), nullable = False)
    manufacturer: str = db.Column(db.String(40), nullable = False)
    width: int = db.Column(db.Integer, nullable = False)
    depth: int = db.Column(db.Integer, nullable = False)
    height: int = db.Column(db.Integer, nullable = False)
    weight: int = db.Column(db.Integer, nullable = False)
    purchase_year: str = db.Column(db.String(4), nullable = False)
    __table_args__ = (
        UniqueConstraint("model", "serial"),
    )

    @classmethod
    def get_by_area_id(cls, area_id: int) -> list[Machine]:
        return Machine.query.filter_by(area = area_id).all()
    

# Custom exceptions
class UsernameException(Exception):
    message: str = "The given username is invalid"

class UsernameExistsException(UsernameException):
    message: str = "The given username is already in use"

class UsernameTooShortException(UsernameException):
    message: str = f"The given username must be at least {Context.min_username_length()} characters long"

class PasswordTooShortException(Exception):
    message: str = f"The given password must be at least {Context.min_password_length()} characters long"