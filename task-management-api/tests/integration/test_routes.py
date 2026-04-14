"""Integration tests for API routes."""

import unittest
import json
from app import create_app
from app.models import db, User, Task, Category


class BaseIntegrationTest(unittest.TestCase):
    """Base class with shared setup for all integration tests."""

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

    def register_user(self, username='testuser', email='test@example.com',
                      password='SecurePass123!'):
        """Helper to register a user and return the response."""
        return self.client.post('/api/auth/register', json={
            'username': username,
            'email': email,
            'password': password
        })

    def login_user(self, username='testuser', password='SecurePass123!'):
        """Helper to login and return the access token."""
        response = self.client.post('/api/auth/login', json={
            'username': username,
            'password': password
        })
        return json.loads(response.data)['access_token']

    def auth_headers(self, token):
        """Return authorization headers for a given token."""
        return {'Authorization': f'Bearer {token}'}


class TestAuthIntegration(unittest.TestCase):
    """Integration tests for authentication endpoints."""

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

    # ── Scenario 1: Register then login ──

    def test_register_creates_user_in_db(self):
        """Registered user should exist in database."""
        response = self.client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123!'
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('user_id', data)
        self.assertIn('access_token', data)
        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)

    def test_register_then_login_returns_valid_jwt(self):
        """User registered and then logged in should receive valid JWT."""
        self.client.post('/api/auth/register', json={
            'username': 'loginuser',
            'email': 'login@example.com',
            'password': 'SecurePass123!'
        })
        response = self.client.post('/api/auth/login', json={
            'username': 'loginuser',
            'password': 'SecurePass123!'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        self.assertEqual(data['username'], 'loginuser')

    def test_register_duplicate_username_returns_400(self):
        """Registering with existing username should return 400."""
        self.client.post('/api/auth/register', json={
            'username': 'dupuser',
            'email': 'dup1@example.com',
            'password': 'SecurePass123!'
        })
        response = self.client.post('/api/auth/register', json={
            'username': 'dupuser',
            'email': 'dup2@example.com',
            'password': 'SecurePass123!'
        })
        self.assertEqual(response.status_code, 400)

    def test_login_wrong_password_returns_401(self):
        """Login with wrong password should return 401."""
        self.client.post('/api/auth/register', json={
            'username': 'passuser',
            'email': 'pass@example.com',
            'password': 'SecurePass123!'
        })
        response = self.client.post('/api/auth/login', json={
            'username': 'passuser',
            'password': 'WrongPassword1!'
        })
        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user_returns_401(self):
        """Login with non-existent user should return 401."""
        response = self.client.post('/api/auth/login', json={
            'username': 'ghostuser',
            'password': 'SecurePass123!'
        })
        self.assertEqual(response.status_code, 401)

    def test_register_invalid_email_returns_400(self):
        """Registration with invalid email should return 400."""
        response = self.client.post('/api/auth/register', json={
            'username': 'emailuser',
            'email': 'not-an-email',
            'password': 'SecurePass123!'
        })
        self.assertEqual(response.status_code, 400)

    def test_register_weak_password_returns_400(self):
        """Registration with weak password should return 400."""
        response = self.client.post('/api/auth/register', json={
            'username': 'weakuser',
            'email': 'weak@example.com',
            'password': 'weak'
        })
        self.assertEqual(response.status_code, 400)

    def test_password_not_stored_in_plain_text(self):
        """Password hash should not equal the plain text password."""
        self.client.post('/api/auth/register', json={
            'username': 'hashuser',
            'email': 'hash@example.com',
            'password': 'SecurePass123!'
        })
        user = User.query.filter_by(username='hashuser').first()
        self.assertNotEqual(user.password_hash, 'SecurePass123!')


class TestTaskIntegration(BaseIntegrationTest):
    """Integration tests for task endpoints."""

    def setUp(self):
        super().setUp()
        self.register_user()
        self.token = self.login_user()
        self.headers = self.auth_headers(self.token)

    # ── Scenario 2: Create task (authenticated) ──

    def test_create_task_authenticated_persists_to_db(self):
        """Authenticated task creation should persist to database."""
        response = self.client.post('/api/tasks/', json={
            'title': 'Integration Task',
            'priority': 'high'
        }, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
        self.assertEqual(data['title'], 'Integration Task')
        task = Task.query.get(data['id'])
        self.assertIsNotNone(task)

    # ── Scenario 3: Create task (unauthenticated) ──

    def test_create_task_unauthenticated_returns_401(self):
        """Unauthenticated task creation should return 401."""
        response = self.client.post('/api/tasks/', json={
            'title': 'Unauthorized Task'
        })
        self.assertEqual(response.status_code, 401)
        tasks = Task.query.all()
        self.assertEqual(len(tasks), 0)

    # ── Scenario 4: Update task status ──

    def test_update_task_status_reflects_in_db(self):
        """Updated task status should be persisted in database."""
        create_resp = self.client.post('/api/tasks/', json={
            'title': 'Status Task'
        }, headers=self.headers)
        task_id = json.loads(create_resp.data)['id']
        update_resp = self.client.put(f'/api/tasks/{task_id}', json={
            'status': 'in_progress'
        }, headers=self.headers)
        self.assertEqual(update_resp.status_code, 200)
        task = Task.query.get(task_id)
        self.assertEqual(task.status, 'in_progress')

    # ── Scenario 5: Delete task ──

    def test_delete_task_returns_204_and_subsequent_get_returns_404(self):
        """Deleted task should return 404 on subsequent GET."""
        create_resp = self.client.post('/api/tasks/', json={
            'title': 'Delete Me'
        }, headers=self.headers)
        task_id = json.loads(create_resp.data)['id']
        delete_resp = self.client.delete(
            f'/api/tasks/{task_id}', headers=self.headers
        )
        self.assertEqual(delete_resp.status_code, 204)
        get_resp = self.client.get(
            f'/api/tasks/{task_id}', headers=self.headers
        )
        self.assertEqual(get_resp.status_code, 404)

    # ── Scenario 6: Filter tasks by status ──

    def test_filter_tasks_by_status_returns_correct_tasks(self):
        """Filtering tasks by status should return only matching tasks."""
        self.client.post('/api/tasks/', json={
            'title': 'Todo Task', 'status': 'todo'
        }, headers=self.headers)
        create_resp = self.client.post('/api/tasks/', json={
            'title': 'Progress Task', 'status': 'todo'
        }, headers=self.headers)
        task_id = json.loads(create_resp.data)['id']
        self.client.put(f'/api/tasks/{task_id}', json={
            'status': 'in_progress'
        }, headers=self.headers)
        response = self.client.get(
            '/api/tasks/?status=todo', headers=self.headers
        )
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Todo Task')

    # ── Scenario 7: Assign task to user ──

    def test_assign_task_to_another_user(self):
        """Task assignment should record assigned_to in database."""
        self.register_user('assignee', 'assignee@example.com')
        assignee = User.query.filter_by(username='assignee').first()
        create_resp = self.client.post('/api/tasks/', json={
            'title': 'Assign Task'
        }, headers=self.headers)
        task_id = json.loads(create_resp.data)['id']
        assign_resp = self.client.post(
            f'/api/tasks/{task_id}/assign',
            json={'assigned_to': assignee.id},
            headers=self.headers
        )
        self.assertEqual(assign_resp.status_code, 200)
        task = Task.query.get(task_id)
        self.assertEqual(task.assigned_to, assignee.id)

    # ── Scenario 8: Access another user's task ──

    def test_access_other_users_task_returns_403(self):
        """Accessing another user's task should return 403."""
        self.register_user('otheruser', 'other@example.com')
        other_token = self.login_user('otheruser')
        other_headers = self.auth_headers(other_token)
        create_resp = self.client.post('/api/tasks/', json={
            'title': 'Private Task'
        }, headers=other_headers)
        task_id = json.loads(create_resp.data)['id']
        response = self.client.get(
            f'/api/tasks/{task_id}', headers=self.headers
        )
        self.assertEqual(response.status_code, 403)

    # ── Scenario 9: Token refresh flow ──

    def test_token_refresh_issues_new_access_token(self):
        """Refresh token should issue a new valid access token."""
        login_resp = self.client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'SecurePass123!'
        })
        refresh_token = json.loads(login_resp.data)['refresh_token']
        refresh_resp = self.client.post('/api/auth/refresh', headers={
            'Authorization': f'Bearer {refresh_token}'
        })
        self.assertEqual(refresh_resp.status_code, 200)
        data = json.loads(refresh_resp.data)
        self.assertIn('access_token', data)

    # ── Scenario 10: Category-task relationship ──

    def test_filter_tasks_by_category(self):
        """Tasks should be filterable by category_id."""
        user = User.query.filter_by(username='testuser').first()
        cat = Category(name='Work', user_id=user.id)
        db.session.add(cat)
        db.session.commit()
        self.client.post('/api/tasks/', json={
            'title': 'Work Task',
            'category_id': cat.id
        }, headers=self.headers)
        self.client.post('/api/tasks/', json={
            'title': 'Personal Task'
        }, headers=self.headers)
        response = self.client.get(
            f'/api/tasks/?category_id={cat.id}', headers=self.headers
        )
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Work Task')

    def test_get_user_profile(self):
        """Authenticated user should be able to retrieve their profile."""
        response = self.client.get('/api/users/me', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['username'], 'testuser')

    def test_create_task_invalid_data_returns_400(self):
        """Task creation with missing title should return 400."""
        response = self.client.post('/api/tasks/', json={
            'priority': 'high'
        }, headers=self.headers)
        self.assertEqual(response.status_code, 400)