"""Unit tests for the TaskService."""

import unittest
from unittest.mock import patch, MagicMock
from app import create_app
from app.models import db, User, Task
from app.services.task_service import TaskService


class TestTaskService(unittest.TestCase):
    """Tests for TaskService business logic."""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.task_service = TaskService()
        self.user = User(username='svcuser', email='svc@test.com')
        self.user.set_password('Password1!')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_task_success(self):
        """create_task should persist and return a Task object."""
        task_data = {
            'title': 'New Task',
            'description': 'A description',
            'priority': 'high'
        }
        result = self.task_service.create_task(self.user.id, task_data)
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.id)
        self.assertEqual(result.title, 'New Task')
        self.assertEqual(result.priority, 'high')
        self.assertEqual(result.user_id, self.user.id)

    def test_create_task_default_priority(self):
        """create_task should default priority to medium."""
        task_data = {'title': 'Simple Task'}
        result = self.task_service.create_task(self.user.id, task_data)
        self.assertEqual(result.priority, 'medium')

    def test_create_task_default_status(self):
        """create_task should default status to todo."""
        task_data = {'title': 'Simple Task'}
        result = self.task_service.create_task(self.user.id, task_data)
        self.assertEqual(result.status, 'todo')

    def test_get_user_tasks_returns_all(self):
        """get_user_tasks should return all tasks for a user."""
        self.task_service.create_task(self.user.id, {'title': 'Task 1'})
        self.task_service.create_task(self.user.id, {'title': 'Task 2'})
        tasks = self.task_service.get_user_tasks(self.user.id)
        self.assertEqual(len(tasks), 2)

    def test_get_user_tasks_filter_by_status(self):
        """get_user_tasks should filter by status correctly."""
        self.task_service.create_task(self.user.id,
            {'title': 'Todo Task', 'status': 'todo'})
        t2 = self.task_service.create_task(self.user.id,
            {'title': 'Progress Task', 'status': 'todo'})
        self.task_service.update_task(t2, {'status': 'in_progress'})
        tasks = self.task_service.get_user_tasks(
            self.user.id, {'status': 'todo'}
        )
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, 'Todo Task')

    def test_get_user_tasks_filter_by_priority(self):
        """get_user_tasks should filter by priority correctly."""
        self.task_service.create_task(self.user.id,
            {'title': 'High Task', 'priority': 'high'})
        self.task_service.create_task(self.user.id,
            {'title': 'Low Task', 'priority': 'low'})
        tasks = self.task_service.get_user_tasks(
            self.user.id, {'priority': 'high'}
        )
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, 'High Task')

    def test_get_task_by_id_found(self):
        """get_task_by_id should return the task when it exists."""
        task = self.task_service.create_task(
            self.user.id, {'title': 'Find Me'}
        )
        found = self.task_service.get_task_by_id(task.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.title, 'Find Me')

    def test_get_task_by_id_not_found(self):
        """get_task_by_id should return None for missing task."""
        result = self.task_service.get_task_by_id(99999)
        self.assertIsNone(result)

    def test_update_task_title(self):
        """update_task should update the task title."""
        task = self.task_service.create_task(
            self.user.id, {'title': 'Old Title'}
        )
        updated = self.task_service.update_task(task, {'title': 'New Title'})
        self.assertEqual(updated.title, 'New Title')

    def test_update_task_status(self):
        """update_task should transition status correctly."""
        task = self.task_service.create_task(
            self.user.id, {'title': 'Status Task'}
        )
        updated = self.task_service.update_task(
            task, {'status': 'in_progress'}
        )
        self.assertEqual(updated.status, 'in_progress')

    def test_complete_task_success(self):
        """complete_task should mark task as completed."""
        task = self.task_service.create_task(
            self.user.id, {'title': 'Finish Me'}
        )
        self.task_service.update_task(task, {'status': 'in_progress'})
        completed = self.task_service.complete_task(task.id)
        self.assertEqual(completed.status, 'completed')

    def test_complete_task_sends_notification(self):
        """complete_task should call notification service when email given."""
        task = self.task_service.create_task(
            self.user.id, {'title': 'Notify Task'}
        )
        self.task_service.update_task(task, {'status': 'in_progress'})
        with patch.object(
            self.task_service.__class__,
            'complete_task',
            wraps=self.task_service.complete_task
        ):
            with patch(
                'app.services.task_service.notification_service'
                '.send_completion_email'
            ) as mock_notify:
                self.task_service.complete_task(
                    task.id, user_email='svc@test.com'
                )
                mock_notify.assert_called_once()

    def test_complete_task_not_found_raises(self):
        """complete_task should raise ValueError for missing task."""
        with self.assertRaises(ValueError):
            self.task_service.complete_task(99999)

    def test_delete_task(self):
        """delete_task should remove the task from the database."""
        task = self.task_service.create_task(
            self.user.id, {'title': 'Delete Me'}
        )
        task_id = task.id
        self.task_service.delete_task(task)
        self.assertIsNone(self.task_service.get_task_by_id(task_id))

    def test_assign_task_success(self):
        """assign_task should set assigned_to on the task."""
        assignee = User(username='assignee', email='assignee@test.com')
        assignee.set_password('Password1!')
        db.session.add(assignee)
        db.session.commit()
        task = self.task_service.create_task(
            self.user.id, {'title': 'Assign Me'}
        )
        updated = self.task_service.assign_task(task, assignee.id)
        self.assertEqual(updated.assigned_to, assignee.id)

    def test_assign_task_invalid_user_raises(self):
        """assign_task should raise ValueError for non-existent user."""
        task = self.task_service.create_task(
            self.user.id, {'title': 'Assign Fail'}
        )
        with self.assertRaises(ValueError):
            self.task_service.assign_task(task, 99999)