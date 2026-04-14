"""Authentication service for user registration and login."""

from app.models import db, User
from app.utils.validators import validate_email, validate_password_strength


class AuthService:
    """Handles user registration and credential validation."""

    def register_user(self, username, email, password):
        """
        Register a new user.
        Returns the User object on success.
        Raises ValueError for invalid input or duplicate users.
        """
        if not username or not username.strip():
            raise ValueError("Username is required.")
        if not validate_email(email):
            raise ValueError("Invalid email format.")
        if not validate_password_strength(password):
            raise ValueError("Password does not meet strength requirements.")
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already exists.")
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already registered.")
        user = User(username=username.strip(), email=email.strip())
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def authenticate_user(self, username, password):
        """
        Validate credentials and return the User if valid.
        Returns None if authentication fails.
        """
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None