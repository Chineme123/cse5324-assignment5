"""Task CRUD routes."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.task_service import TaskService
from app.models import db, Category
from app.utils.validators import validate_task_data

tasks_bp = Blueprint('tasks', __name__)
task_service = TaskService()


@tasks_bp.route('/', methods=['POST'])
@jwt_required()
def create_task():
    """Create a new task for the authenticated user."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    valid, error = validate_task_data(data)
    if not valid:
        return jsonify({'error': error}), 400
    current_user_id = get_jwt_identity()
    task = task_service.create_task(current_user_id, data)
    return jsonify(task.to_dict()), 201


@tasks_bp.route('/', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get all tasks for the authenticated user with optional filters."""
    current_user_id = get_jwt_identity()
    filters = {
        'status': request.args.get('status'),
        'priority': request.args.get('priority'),
        'category_id': request.args.get('category_id')
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    tasks = task_service.get_user_tasks(current_user_id, filters)
    return jsonify([t.to_dict() for t in tasks]), 200


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """Get a specific task by ID."""
    current_user_id = get_jwt_identity()
    task = task_service.get_task_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    if task.user_id != current_user_id:
        return jsonify({'error': 'Access forbidden'}), 403
    return jsonify(task.to_dict()), 200


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update a task owned by the authenticated user."""
    current_user_id = get_jwt_identity()
    task = task_service.get_task_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    if task.user_id != current_user_id:
        return jsonify({'error': 'Access forbidden'}), 403
    data = request.get_json()
    try:
        updated = task_service.update_task(task, data)
        return jsonify(updated.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Delete a task owned by the authenticated user."""
    current_user_id = get_jwt_identity()
    task = task_service.get_task_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    if task.user_id != current_user_id:
        return jsonify({'error': 'Access forbidden'}), 403
    task_service.delete_task(task)
    return jsonify({'message': 'Task deleted'}), 204


@tasks_bp.route('/<int:task_id>/assign', methods=['POST'])
@jwt_required()
def assign_task(task_id):
    """Assign a task to another user."""
    current_user_id = get_jwt_identity()
    task = task_service.get_task_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    if task.user_id != current_user_id:
        return jsonify({'error': 'Access forbidden'}), 403
    data = request.get_json()
    try:
        updated = task_service.assign_task(task, data.get('assigned_to'))
        return jsonify(updated.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400