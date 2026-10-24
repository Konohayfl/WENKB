import os
from pathlib import Path
import site
import sqlite3
import sys
import unittest
from unittest.mock import patch

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = ROOT / 'wenkb-server'
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))
VENV_SITE = ROOT / '.venv' / 'Lib' / 'site-packages'
if VENV_SITE.exists():
    site.addsitedir(str(VENV_SITE))

ORIGINAL_CWD = Path.cwd()
os.chdir(SERVER_DIR)
try:
    from config.common import DB_SCHEMA_VERSION
    from server.api.sys.AuthApi import AuthApi
    from server.db import DbManager
    from server.db.DbUpgrade import DDL_DIR, get_sql_scripts
    from server.exception.exception import golbal_exception_handlers
    from server.model.orm_sys import UserAccount
    from server.utils.authmiddleware import request_identity_middleware
    from server.utils.jwtutils import decode_token
    from server.utils.secretutils import aes_encrypt
finally:
    os.chdir(ORIGINAL_CWD)


class AuthApiTest(unittest.TestCase):
    def setUp(self):
        self.original_session_factory = DbManager.SESSION
        self.engine = create_engine(
            'sqlite://',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
        )
        DbManager.Base.metadata.create_all(self.engine)
        DbManager.SESSION = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.jwt_environment = patch.dict(
            os.environ,
            {'WENKB_JWT_SECRET': 'auth-api-test-secret-with-more-than-32-bytes'},
        )
        self.jwt_environment.start()
        self.app = FastAPI(exception_handlers=golbal_exception_handlers)
        self.app.middleware('http')(request_identity_middleware)
        AuthApi(self.app)

        @self.app.get('/private')
        def private_route(request: Request):
            return request.state.user

        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        DbManager.SESSION = self.original_session_factory
        self.engine.dispose()
        self.jwt_environment.stop()

    def encrypted(self, password):
        return aes_encrypt(password)

    def register(self, username='user@example.com', nickname='Test User', password='safe-pass-123'):
        return self.client.post('/sys/auth/regist', json={
            'username': username,
            'nickname': nickname,
            'password': self.encrypted(password),
            'cfimpswd': self.encrypted(password),
        })

    def login(self, username='user@example.com', password='safe-pass-123'):
        return self.client.post('/sys/auth/login', json={
            'username': username,
            'password': self.encrypted(password),
        })

    def test_register_persists_unique_account_with_hash_and_login_token(self):
        registered = self.register()
        self.assertEqual(200, registered.status_code)
        user_id = registered.json()['data']['id']

        with DbManager.session_scope(True) as session:
            account = session.get(UserAccount, user_id)
            self.assertEqual('user@example.com', account.username)
            self.assertEqual('Test User', account.nickname)
            self.assertNotEqual('safe-pass-123', account.passwordHash)
            self.assertTrue(account.passwordHash.startswith('pbkdf2_sha256$'))

        duplicate = self.register(username=' User@Example.com ')
        self.assertEqual(409, duplicate.status_code)

        logged_in = self.login(username='USER@EXAMPLE.COM')
        self.assertEqual(200, logged_in.status_code)
        auth_data = logged_in.json()['data']
        self.assertEqual(user_id, auth_data['id'])
        self.assertEqual(user_id, decode_token(auth_data['token'])['id'])
        protected = self.client.get('/private', headers={'token': auth_data['token']})
        self.assertEqual(200, protected.status_code)
        self.assertEqual(user_id, protected.json()['id'])

        self.register(username='second@example.com', nickname='Second User')
        second_login = self.login(username='second@example.com')
        second_user_id = second_login.json()['data']['id']
        self.assertNotEqual(user_id, second_user_id)
        second_identity = self.client.get(
            '/private', headers={'token': second_login.json()['data']['token']}
        )
        self.assertEqual(second_user_id, second_identity.json()['id'])

    def test_invalid_password_and_confirmation_are_rejected(self):
        self.register()
        wrong_password = self.login(password='not-the-password')
        self.assertEqual(401, wrong_password.status_code)
        self.assertEqual('账号或密码错误', wrong_password.json()['msg'])

        mismatch = self.client.post('/sys/auth/regist', json={
            'username': 'another-user',
            'password': self.encrypted('safe-pass-123'),
            'cfimpswd': self.encrypted('different-pass'),
        })
        self.assertEqual(400, mismatch.status_code)

    def test_registration_and_login_are_public_but_business_routes_require_jwt(self):
        missing_token = self.client.get('/private')
        invalid_token = self.client.get('/private', headers={'token': 'invalid'})
        self.assertEqual(401, missing_token.status_code)
        self.assertEqual(401, invalid_token.status_code)
        self.assertEqual(200, self.register().status_code)
        self.assertEqual(200, self.login().status_code)


class AuthMigrationTest(unittest.TestCase):
    def test_fresh_install_baseline_contains_user_table(self):
        statements = get_sql_scripts(DDL_DIR, 0, DB_SCHEMA_VERSION)
        self.assertTrue(any('t_sys_user' in statement for statement in statements))
        connection = sqlite3.connect(':memory:')
        try:
            for statement in statements:
                connection.execute(statement)
            table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='t_sys_user'"
            ).fetchone()
            self.assertIsNotNone(table)
        finally:
            connection.close()

    def test_schema_six_migration_adds_user_table_and_unique_username(self):
        self.assertEqual(6, DB_SCHEMA_VERSION)
        statements = get_sql_scripts(DDL_DIR, 5, DB_SCHEMA_VERSION)
        self.assertTrue(statements)
        self.assertTrue(all('t_sys_user' in statement for statement in statements))

        connection = sqlite3.connect(':memory:')
        try:
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO t_sys_user (user_id, username, nickname, password_hash, crt_tm) "
                "VALUES ('id-1', 'account', 'Account', 'hash', '2026-10-24 00:00:00')"
            )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO t_sys_user (user_id, username, nickname, password_hash, crt_tm) "
                    "VALUES ('id-2', 'account', 'Other', 'hash', '2026-10-24 00:00:00')"
                )
        finally:
            connection.close()


if __name__ == '__main__':
    unittest.main()
