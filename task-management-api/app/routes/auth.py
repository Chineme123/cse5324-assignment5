"""Authentication routes for register and login."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    try:
        user = auth_service.register_user(
            data.get('username'),
            data.get('email'),
            data.get('password')
        )
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return jsonify({
            'user_id': user.id,
            'username': user.username,
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate a user and return JWT tokens."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    user = auth_service.authenticate_user(
        data.get('username'), data.get('password')
    )
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Issue a new access token from a valid refresh token."""
    from flask_jwt_extended import jwt_required, get_jwt_identity
    from functools import wraps

    @jwt_required(refresh=True)
    def _refresh():
        current_user_id = get_jwt_identity()
        new_token = create_access_token(identity=current_user_id)
        return jsonify({'access_token': new_token}), 200

    return _refresh()