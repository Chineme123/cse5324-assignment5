"""Unit tests for database models."""

import unittest
from datetime import datetime, timedelta
from app import create_app
from app.models import db, User, Task, Category


class TestUserModel(unittest.TestCase):
    """Tests for the User model."""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        """Password should be hashed and verifiable."""
        user = User(username='test', email='test@test.com')
        user.set_password('password123')
        self.assertNotEqual(user.password_hash, 'password123')
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.check_password('wrongpassword'))

    def test_user_repr(self):
        """User __repr__ should return formatted string."""
        user = User(username='testuser', email='test@test.com')
        self.assertEqual(str(user), '<User testuser>')

    def test_valid_email_validation(self):
        """Valid email should pass validation."""
        user = User(username='test', email='valid@example.com')
        self.assertTrue(user.validate_email())

    def test_invalid_email_validation(self):
        """Invalid email should raise ValueError."""
        user = User(username='test', email='invalid-email')
        with self.assertRaises(ValueError):
            user.validate_email()

    def test_user_to_dict(self):
        """to_dict should return all expected fields."""
        user = User(username='testuser', email='test@test.com')
        db.session.add(user)
        db.session.commit()
        result = user.to_dict()
        self.assertIn('id', result)
        self.assertIn('username', result)
        self.assertIn('email', result)
        self.assertEqual(result['username'], 'testuser')

    def test_user_persisted_to_db(self):
        """User should be retrievable after commit."""
        user = User(username='dbuser', email='db@test.com')
        user.set_password('Password1!')
        db.session.add(user)
        db.session.commit()
        fetched = User.query.filter_by(username='dbuser').first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.email, 'db@test.com')


class TestTaskModel(unittest.TestCase):
    """Tests for the Task model."""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.user = User(username='taskuser', email='task@test.com')
        self.user.set_password('Password1!')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_task_creation(self):
        """Task should be created with correct attributes."""
        task = Task(
            title='Test Task',
            description='Test Description',
            priority='high',
            status='todo',
            user_id=self.user.id
        )
        db.session.add(task)
        db.session.commit()
        self.assertIsNotNone(task.id)
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.priority, 'high')
        self.assertEqual(task.status, 'todo')

    def test_task_status_transition_todo_to_in_progress(self):
        """Task should transition from todo to in_progress."""
        task = Task(title='Test', status='todo', user_id=self.user.id)
        task.update_status('in_progress')
        self.assertEqual(task.status, 'in_progress')

    def test_task_status_transition_in_progress_to_completed(self):
        """Task should transition from in_progress to completed."""
        task = Task(title='Test', status='in_progress', user_id=self.user.id)
        task.update_status('completed')
        self.assertEqual(task.status, 'completed')

    def test_invalid_status_transition_completed_to_todo(self):
        """Completed task cannot go back to todo."""
        task = Task(title='Test', status='completed', user_id=self.user.id)
        with self.assertRaises(ValueError):
            task.update_status('todo')

    def test_invalid_status_transition_todo_to_completed(self):
        """Task cannot skip from todo directly to completed."""
        task = Task(title='Test', status='todo', user_id=self.user.id)
        with self.assertRaises(ValueError):
            task.update_status('completed')

    def test_invalid_status_value(self):
        """Unknown status value should raise ValueError."""
        task = Task(title='Test', status='todo', user_id=self.user.id)
        with self.assertRaises(ValueError):
            task.update_status('unknown_status')

    def test_task_due_date_validation_past_date(self):
        """Past due date should raise ValueError."""
        past_date = datetime.utcnow() - timedelta(days=1)
        task = Task(title='Test', due_date=past_date, user_id=self.user.id)
        with self.assertRaises(ValueError):
            task.validate_due_date()

    def test_task_due_date_validation_future_date(self):
        """Future due date should pass validation."""
        future_date = datetime.utcnow() + timedelta(days=7)
        task = Task(title='Test', due_date=future_date, user_id=self.user.id)
        self.assertTrue(task.validate_due_date())

    def test_task_due_date_none_is_valid(self):
        """Task with no due date should pass validation."""
        task = Task(title='Test', user_id=self.user.id)
        self.assertTrue(task.validate_due_date())

    def test_task_to_dict(self):
        """to_dict should return all expected fields."""
        task = Task(title='Dict Task', priority='low',
                    status='todo', user_id=self.user.id)
        db.session.add(task)
        db.session.commit()
        result = task.to_dict()
        self.assertIn('id', result)
        self.assertIn('title', result)
        self.assertIn('status', result)
        self.assertIn('priority', result)
        self.assertEqual(result['title'], 'Dict Task')

    def test_task_repr(self):
        """Task __repr__ should return formatted string."""
        task = Task(title='My Task')
        self.assertEqual(str(task), '<Task My Task>')

    def test_task_default_status_is_todo(self):
        """Task status should default to todo."""
        task = Task(title='Default Task', user_id=self.user.id)
        self.assertEqual(task.status, 'todo')

    def test_task_default_priority_is_medium(self):
        """Task priority should default to medium."""
        task = Task(title='Default Task', user_id=self.user.id)
        self.assertEqual(task.priority, 'medium')


class TestCategoryModel(unittest.TestCase):
    """Tests for the Category model."""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.user = User(username='catuser', email='cat@test.com')
        self.user.set_password('Password1!')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_category_creation(self):
        """Category should be created with correct attributes."""
        cat = Category(name='Work', user_id=self.user.id)
        db.session.add(cat)
        db.session.commit()
        self.assertIsNotNone(cat.id)
        self.assertEqual(cat.name, 'Work')

    def test_category_to_dict(self):
        """to_dict should return all expected fields."""
        cat = Category(name='Personal', user_id=self.user.id)
        db.session.add(cat)
        db.session.commit()
        result = cat.to_dict()
        self.assertIn('id', result)
        self.assertIn('name', result)
        self.assertIn('user_id', result)

    def test_category_repr(self):
        """Category __repr__ should return formatted string."""
        cat = Category(name='Work', user_id=self.user.id)
        self.assertEqual(str(cat), '<Category Work>')