"""Notification service for task-related alerts."""


class NotificationService:
    """Handles sending notifications for task events."""

    def send_completion_email(self, user_email, task_title):
        """Simulate sending a task completion email."""
        print(f"[EMAIL] Task '{task_title}' completed. Notifying {user_email}")
        return True

    def send_assignment_email(self, user_email, task_title, assigned_by):
        """Simulate sending a task assignment notification."""
        print(f"[EMAIL] Task '{task_title}' assigned by {assigned_by} "
              f"to {user_email}")
        return True