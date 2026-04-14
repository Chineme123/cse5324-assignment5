"""System/End-to-End tests for complete user workflows."""

import unittest
import json
from app import create_app
from app.models import db


class BaseSystemTest(unittest.TestCase):
    """Base class for system tests with shared helpers."""

    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def register(self, username, email, password='SecurePass123!'):
        """Register a user and return response data."""
        resp = self.client.post('/api/auth/register', json={
            'username': username,
            'email': email,
            'password': password
        })
        return json.loads(resp.data)

    def login(self, username, password='SecurePass123!'):
        """Login and return access token."""
        resp = self.client.post('/api/auth/login', json={
            'username': username,
            'password': password
        })
        return json.loads(resp.data)['access_token']

    def headers(self, token):
        """Return auth headers for a token."""
        return {'Authorization': f'Bearer {token}'}

    def create_task(self, token, title, **kwargs):
        """Create a task and return response data."""
        payload = {'title': title, **kwargs}
        resp = self.client.post(
            '/api/tasks/', json=payload, headers=self.headers(token)
        )
        return json.loads(resp.data), resp.status_code

    def get_task(self, token, task_id):
        """Get a task by ID."""
        resp = self.client.get(
            f'/api/tasks/{task_id}', headers=self.headers(token)
        )
        return json.loads(resp.data), resp.status_code

    def update_task(self, token, task_id, **kwargs):
        """Update a task and return response data."""
        resp = self.client.put(
            f'/api/tasks/{task_id}',
            json=kwargs,
            headers=self.headers(token)
        )
        return json.loads(resp.data), resp.status_code

    def delete_task(self, token, task_id):
        """Delete a task and return status code."""
        resp = self.client.delete(
            f'/api/tasks/{task_id}', headers=self.headers(token)
        )
        return resp.status_code

    def get_all_tasks(self, token, **filters):
        """Get all tasks with optional filters."""
        query = '&'.join(f'{k}={v}' for k, v in filters.items())
        url = f'/api/tasks/?{query}' if query else '/api/tasks/'
        resp = self.client.get(url, headers=self.headers(token))
        return json.loads(resp.data), resp.status_code


class TestFullTaskLifecycleWorkflow(BaseSystemTest):
    """
    Workflow 1: Full Task Lifecycle
    Register → Login → Create Task → Update Status → Complete → Delete
    """

    def test_full_task_lifecycle(self):
        """Complete task lifecycle from creation to deletion."""

        # Step 1: Register a new user
        reg_data = self.register('lifecycle_user', 'lifecycle@example.com')
        self.assertIn('user_id', reg_data)
        self.assertIn('access_token', reg_data)
        user_id = reg_data['user_id']

        # Step 2: Login with the registered user
        token = self.login('lifecycle_user')
        self.assertIsNotNone(token)

        # Step 3: Create a task
        task_data, status = self.create_task(
            token, 'Lifecycle Task',
            description='Full lifecycle test',
            priority='high'
        )
        self.assertEqual(status, 201)
        self.assertEqual(task_data['title'], 'Lifecycle Task')
        self.assertEqual(task_data['status'], 'todo')
        self.assertEqual(task_data['priority'], 'high')
        task_id = task_data['id']

        # Step 4: Update status to in_progress
        updated, status = self.update_task(
            token, task_id, status='in_progress'
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated['status'], 'in_progress')

        # Step 5: Complete the task
        completed, status = self.update_task(
            token, task_id, status='completed'
        )
        self.assertEqual(status, 200)
        self.assertEqual(completed['status'], 'completed')

        # Step 6: Verify final state in DB
        final_task, status = self.get_task(token, task_id)
        self.assertEqual(status, 200)
        self.assertEqual(final_task['status'], 'completed')
        self.assertEqual(final_task['user_id'], user_id)

        # Step 7: Delete the task
        delete_status = self.delete_task(token, task_id)
        self.assertEqual(delete_status, 204)

        # Step 8: Verify task is gone
        _, get_status = self.get_task(token, task_id)
        self.assertEqual(get_status, 404)

    def test_multiple_tasks_lifecycle(self):
        """Multiple tasks can be managed independently."""
        self.register('multi_user', 'multi@example.com')
        token = self.login('multi_user')

        # Create three tasks
        task1, _ = self.create_task(token, 'Task One', priority='low')
        task2, _ = self.create_task(token, 'Task Two', priority='medium')
        task3, _ = self.create_task(token, 'Task Three', priority='high')

        # Progress task1 all the way to completed
        self.update_task(token, task1['id'], status='in_progress')
        self.update_task(token, task1['id'], status='completed')

        # Progress task2 to in_progress only
        self.update_task(token, task2['id'], status='in_progress')

        # Leave task3 as todo

        # Verify all tasks have correct final states
        all_tasks, status = self.get_all_tasks(token)
        self.assertEqual(status, 200)
        self.assertEqual(len(all_tasks), 3)

        statuses = {t['title']: t['status'] for t in all_tasks}
        self.assertEqual(statuses['Task One'], 'completed')
        self.assertEqual(statuses['Task Two'], 'in_progress')
        self.assertEqual(statuses['Task Three'], 'todo')


class TestCategoryWorkflow(BaseSystemTest):
    """
    Workflow 2: Category Workflow
    Login → Create Category → Create Task in Category →
    Filter by Category → Verify Results
    """

    def test_category_workflow(self):
        """Tasks can be organized and filtered by category."""
        from app.models import Category

        # Step 1: Register and login
        self.register('cat_user', 'cat@example.com')
        token = self.login('cat_user')

        # Step 2: Create two categories directly in DB
        with self.app.app_context():
            from app.models import User
            user = User.query.filter_by(username='cat_user').first()
            work_cat = Category(name='Work', user_id=user.id)
            personal_cat = Category(name='Personal', user_id=user.id)
            db.session.add(work_cat)
            db.session.add(personal_cat)
            db.session.commit()
            work_id = work_cat.id
            personal_id = personal_cat.id

        # Step 3: Create tasks in each category
        work_task, status = self.create_task(
            token, 'Work Task 1',
            priority='high',
            category_id=work_id
        )
        self.assertEqual(status, 201)
        self.assertEqual(work_task['category_id'], work_id)

        _, status = self.create_task(
            token, 'Work Task 2',
            priority='medium',
            category_id=work_id
        )
        self.assertEqual(status, 201)

        _, status = self.create_task(
            token, 'Personal Task',
            priority='low',
            category_id=personal_id
        )
        self.assertEqual(status, 201)

        # Step 4: Filter tasks by Work category
        work_tasks, status = self.get_all_tasks(
            token, category_id=work_id
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(work_tasks), 2)
        for task in work_tasks:
            self.assertEqual(task['category_id'], work_id)

        # Step 5: Filter tasks by Personal category
        personal_tasks, status = self.get_all_tasks(
            token, category_id=personal_id
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(personal_tasks), 1)
        self.assertEqual(personal_tasks[0]['title'], 'Personal Task')

        # Step 6: Verify total task count
        all_tasks, status = self.get_all_tasks(token)
        self.assertEqual(status, 200)
        self.assertEqual(len(all_tasks), 3)

    def test_tasks_without_category_not_in_category_filter(self):
        """Tasks without a category should not appear in category filters."""
        from app.models import Category, User

        self.register('nocat_user', 'nocat@example.com')
        token = self.login('nocat_user')

        with self.app.app_context():
            user = User.query.filter_by(username='nocat_user').first()
            cat = Category(name='Work', user_id=user.id)
            db.session.add(cat)
            db.session.commit()
            cat_id = cat.id

        # Create one categorized and one uncategorized task
        self.create_task(token, 'Categorized Task', category_id=cat_id)
        self.create_task(token, 'No Category Task')

        # Filter by category — should only return the categorized task
        filtered, status = self.get_all_tasks(token, category_id=cat_id)
        self.assertEqual(status, 200)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['title'], 'Categorized Task')


class TestErrorRecoveryWorkflow(BaseSystemTest):
    """
    Workflow 3: Error Recovery Workflow
    Attempt invalid operations and verify appropriate errors at each step.
    """

    def test_unauthenticated_operations_all_return_401(self):
        """All protected endpoints should return 401 without a token."""
        # Attempt task creation without auth
        resp = self.client.post('/api/tasks/', json={'title': 'No Auth'})
        self.assertEqual(resp.status_code, 401)

        # Attempt task listing without auth
        resp = self.client.get('/api/tasks/')
        self.assertEqual(resp.status_code, 401)

        # Attempt profile access without auth
        resp = self.client.get('/api/users/me')
        self.assertEqual(resp.status_code, 401)

    def test_invalid_status_transition_returns_400(self):
        """Skipping status transitions should return 400."""
        self.register('err_user', 'err@example.com')
        token = self.login('err_user')

        # Create task (starts as todo)
        task_data, _ = self.create_task(token, 'Error Task')
        task_id = task_data['id']

        # Try to skip directly to completed — should fail
        _, status = self.update_task(token, task_id, status='completed')
        self.assertEqual(status, 400)

        # Task status should still be todo
        task, _ = self.get_task(token, task_id)
        self.assertEqual(task['status'], 'todo')

    def test_wrong_owner_cannot_modify_task(self):
        """User cannot update or delete another user's task."""
        # Setup two users
        self.register('owner', 'owner@example.com')
        self.register('intruder', 'intruder@example.com')
        owner_token = self.login('owner')
        intruder_token = self.login('intruder')

        # Owner creates a task
        task_data, _ = self.create_task(owner_token, 'Owner Task')
        task_id = task_data['id']

        # Intruder tries to read — 403
        _, status = self.get_task(intruder_token, task_id)
        self.assertEqual(status, 403)

        # Intruder tries to update — 403
        _, status = self.update_task(
            intruder_token, task_id, title='Stolen Task'
        )
        self.assertEqual(status, 403)

        # Intruder tries to delete — 403
        status = self.delete_task(intruder_token, task_id)
        self.assertEqual(status, 403)

        # Original task should be unchanged
        task, status = self.get_task(owner_token, task_id)
        self.assertEqual(status, 200)
        self.assertEqual(task['title'], 'Owner Task')

    def test_get_nonexistent_task_returns_404(self):
        """Requesting a task that does not exist should return 404."""
        self.register('notfound_user', 'notfound@example.com')
        token = self.login('notfound_user')
        _, status = self.get_task(token, 99999)
        self.assertEqual(status, 404)

    def test_invalid_login_credentials_blocked(self):
        """Invalid credentials should consistently return 401."""
        self.register('block_user', 'block@example.com')

        # Wrong password
        resp = self.client.post('/api/auth/login', json={
            'username': 'block_user',
            'password': 'WrongPassword1!'
        })
        self.assertEqual(resp.status_code, 401)

        # Non-existent user
        resp = self.client.post('/api/auth/login', json={
            'username': 'ghost',
            'password': 'SecurePass123!'
        })
        self.assertEqual(resp.status_code, 401)

    def test_registration_validation_errors(self):
        """Invalid registration data should return 400 with error message."""
        # Weak password
        resp = self.client.post('/api/auth/register', json={
            'username': 'weakuser',
            'email': 'weak@example.com',
            'password': 'weak'
        })
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn('error', data)

        # Invalid email
        resp = self.client.post('/api/auth/register', json={
            'username': 'bademail',
            'email': 'notanemail',
            'password': 'SecurePass123!'
        })
        self.assertEqual(resp.status_code, 400)

        # Duplicate username
        self.register('dupuser', 'dup1@example.com')
        resp = self.client.post('/api/auth/register', json={
            'username': 'dupuser',
            'email': 'dup2@example.com',
            'password': 'SecurePass123!'
        })
        self.assertEqual(resp.status_code, 400)

    def test_task_creation_validation_errors(self):
        """Invalid task data should return 400."""
        self.register('val_user', 'val@example.com')
        token = self.login('val_user')

        # Missing title
        resp = self.client.post(
            '/api/tasks/', json={'priority': 'high'},
            headers=self.headers(token)
        )
        self.assertEqual(resp.status_code, 400)

        # Invalid priority
        resp = self.client.post(
            '/api/tasks/',
            json={'title': 'Bad Task', 'priority': 'urgent'},
            headers=self.headers(token)
        )
        self.assertEqual(resp.status_code, 400)