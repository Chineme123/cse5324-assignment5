"""Database models for the Task Management API."""

import re
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

VALID_STATUSES = ['todo', 'in_progress', 'completed']
VALID_PRIORITIES = ['low', 'medium', 'high']
VALID_TRANSITIONS = {
    'todo': ['in_progress'],
    'in_progress': ['completed'],
    'completed': []
}


class User(db.Model):
    """Represents a registered user in the system."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('Task', backref='owner', lazy=True,
                            foreign_keys='Task.user_id')

    def set_password(self, password):
        """Hash and store the user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Return True if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def validate_email(self):
        """Raise ValueError if the email format is invalid."""
        pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, self.email):
            raise ValueError(f"Invalid email format: {self.email}")
        return True

    def to_dict(self):
        """Return a dictionary representation of the user."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    """Represents a task category."""

    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tasks = db.relationship('Task', backref='category', lazy=True)

    def to_dict(self):
        """Return a dictionary representation of the category."""
        return {'id': self.id, 'name': self.name, 'user_id': self.user_id}

    def __repr__(self):
        return f'<Category {self.name}>'


class Task(db.Model):
    """Represents a task assigned to a user."""

    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='todo')
    priority = db.Column(db.String(20), default='medium')

    def __init__(self, **kwargs):
        kwargs.setdefault('status', 'todo')
        kwargs.setdefault('priority', 'medium')
        super().__init__(**kwargs)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'),
                            nullable=True)

    def update_status(self, new_status):
        """
        Transition task to new_status.
        Raises ValueError for invalid or disallowed transitions.
        """
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{self.status}' to '{new_status}'"
            )
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def validate_due_date(self):
        """Raise ValueError if due_date is in the past."""
        if self.due_date and self.due_date < datetime.utcnow():
            raise ValueError("Due date cannot be in the past.")
        return True

    def to_dict(self):
        """Return a dictionary representation of the task."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'user_id': self.user_id,
            'assigned_to': self.assigned_to,
            'category_id': self.category_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Task {self.title}>'