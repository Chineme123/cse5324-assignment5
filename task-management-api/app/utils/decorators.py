"""Custom decorators for route protection."""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import Task


def jwt_required_custom(fn):
    """Decorator that enforces JWT authentication on a route."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({'error': 'Authentication required'}), 401
        return fn(*args, **kwargs)
    return wrapper


def task_owner_required(fn):
    """Decorator that ensures the current user owns the requested task."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({'error': 'Authentication required'}), 401
        task_id = kwargs.get('task_id')
        current_user_id = get_jwt_identity()
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        if task.user_id != current_user_id:
            return jsonify({'error': 'Access forbidden'}), 403
        return fn(*args, **kwargs)
    return wrapper