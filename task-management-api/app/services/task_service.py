"""Task service for business logic around task operations."""

from datetime import datetime
from app.models import db, Task
from app.services.notification_service import NotificationService

notification_service = NotificationService()


class TaskService:
    """Handles task creation, retrieval, updates, and deletion."""

    def create_task(self, user_id, task_data):
        """Create and persist a new task. Returns the Task object."""
        task = Task(
            title=task_data['title'],
            description=task_data.get('description', ''),
            priority=task_data.get('priority', 'medium'),
            status=task_data.get('status', 'todo'),
            user_id=user_id,
            category_id=task_data.get('category_id')
        )
        if task_data.get('due_date'):
            task.due_date = datetime.fromisoformat(task_data['due_date'])
        db.session.add(task)
        db.session.commit()
        return task

    def get_user_tasks(self, user_id, filters=None):
        """Return all tasks for a user, optionally filtered."""
        query = Task.query.filter_by(user_id=user_id)
        if filters:
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('priority'):
                query = query.filter_by(priority=filters['priority'])
            if filters.get('category_id'):
                query = query.filter_by(category_id=filters['category_id'])
        return query.all()

    def get_task_by_id(self, task_id):
        """Return a task by ID or None if not found."""
        return Task.query.get(task_id)

    def update_task(self, task, update_data):
        """Apply updates to a task and persist. Returns the updated Task."""
        if 'title' in update_data:
            task.title = update_data['title']
        if 'description' in update_data:
            task.description = update_data['description']
        if 'priority' in update_data:
            task.priority = update_data['priority']
        if 'status' in update_data:
            task.update_status(update_data['status'])
        if 'due_date' in update_data:
            task.due_date = datetime.fromisoformat(update_data['due_date'])
        task.updated_at = datetime.utcnow()
        db.session.commit()
        return task

    def complete_task(self, task_id, user_email=None):
        """
        Mark a task as completed and send notification.
        Raises ValueError if task not found or transition invalid.
        """
        task = Task.query.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")
        task.update_status('completed')
        db.session.commit()
        if user_email:
            notification_service.send_completion_email(user_email, task.title)
        return task

    def delete_task(self, task):
        """Delete a task from the database."""
        db.session.delete(task)
        db.session.commit()

    def assign_task(self, task, assigned_user_id, assigned_by_email=None):
        """Assign a task to a user and send notification."""
        from app.models import User
        assigned_user = User.query.get(assigned_user_id)
        if not assigned_user:
            raise ValueError(f"User {assigned_user_id} not found.")
        task.assigned_to = assigned_user_id
        db.session.commit()
        if assigned_by_email:
            notification_service.send_assignment_email(
                assigned_user.email, task.title, assigned_by_email
            )
        return task