
from __future__ import annotations
from datetime import datetime
from sqlalchemy import ForeignKeyConstraint, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import reconstructor
from utilities import Context

# Get the reference from Context
db = Context().db()

# Models
class User(db.Model):
    id: int = db.Column(db.Integer, primary_key = True)
    username: str = db.Column(db.String(30), unique = True, nullable = False)
    password: str = db.Column(db.String(100), nullable = False)
    datetime_added: datetime = db.Column(db.DateTime(timezone = True), server_default = func.now())

    @reconstructor
    def __init_on_load(self):
        self.is_authenticated: bool = False
        self.is_active: bool = True
        self.is_anonymous: bool = False

    @classmethod
    def get(cls, user_id: int) -> User:
        return User.query.filter_by(id = user_id).first()

    @hybrid_property
    def get_id(self) -> int:
        return self.id

class Role(db.Model):
    rolename: str = db.Column(db.String(30), primary_key = True)

class UserRole(db.Model):
    user: int = db.Column(db.Integer, primary_key = True)
    role: str = db.Column(db.String(30), primary_key = True)
    __table_args__ = (
        ForeignKeyConstraint([user], [User.id]),
        ForeignKeyConstraint([role], [Role.rolename])
    )

    @classmethod
    def get_by_user_id(cls, user_id: int) -> list[str]:
        return UserRole.query.filter_by(user = user_id).all()
    
    @hybrid_property
    def get_rolename(self) -> str:
        return self.role

class Task(db.Model):
    id: int = db.Column(db.Integer, primary_key = True)
    user: str = db.Column(db.String(20), unique = True, nullable = False)
    description: str = db.Column(db.String(200), nullable = False)
    completed: bool = db.Column(db.Boolean, default = False, nullable = False)
    __table_args__ = (
        ForeignKeyConstraint([user], [User.id]),
    )