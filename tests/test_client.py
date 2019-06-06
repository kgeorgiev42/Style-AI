import unittest

from unittest.mock import patch, MagicMock
from st_webservice import create_app, db
from st_webservice.models import User, Image

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse('Currently logged in as ' in response.get_data(as_text=True))

    def test_about_page(self):
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertFalse('Currently logged in as ' in response.get_data(as_text=True))

    def test_gallery_page(self):
        response = self.client.get('/gallery')
        self.assertEqual(response.status_code, 200)
        self.assertFalse('Currently logged in as ' in response.get_data(as_text=True))

    def test_register_rpwd_and_login(self):
        # register a new account
        response = self.client.post('/register', data={
            'reg_email': 'dummy@example.com',
            'reg_username': 'Dummy_96',
            'reg_password': 'Dummy_pwd_96',
            'reg_rpassword': 'Dummy_pwd_96'
        })
        self.assertEqual(response.status_code, 302)

        # reset password
        user = User.query.filter_by(email='dummy@example.com').first()
        token = user.get_reset_password_token()
        response = self.client.post('/reset_pwd_token/{}'.format(token), data={
            'resetPassword': 'Dummy_pwd_96',
            'resetPassword2': 'Dummy_pwd_96'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            'Your password has been reset.' in response.get_data(
                as_text=True))

        # log in with the new account
        response = self.client.post('/login', data={
            'log_username': 'Dummy_96',
            'log_password': 'Dummy_pwd_96',
            'log_remember': False
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Currently logged in as Dummy_96',
                                  response.get_data(as_text=True))


        # log out
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have been successfully logged out.' in response.get_data(
            as_text=True))

    def test_authorizers(self):
        fb_response = self.client.get('/authorize/facebook')
        self.assertEqual(fb_response.status_code, 302)
        self.assertEqual(fb_response.location.split('?')[0], 'https://graph.facebook.com/oauth/authorize')
        gh_response = self.client.get('/authorize/github')
        self.assertEqual(gh_response.status_code, 302)
        self.assertEqual(gh_response.location.split('?')[0], 'https://github.com/login/oauth/authorize')
        gg_response = self.client.get('/authorize/google')
        self.assertEqual(gg_response.status_code, 302)
        self.assertEqual(gg_response.location.split('?')[0], 'https://accounts.google.com/o/oauth2/v2/auth')

    @patch('rauth.OAuth2Service.get_auth_session')
    def test_callbacks(self, mock_get_auth_session):
        mock_session = MagicMock()
        mock_get_response = MagicMock(status_code=200, json=MagicMock(return_value={'name': 'Dummy', 'id': '3617923766551'}))
        mock_session.get.return_value = mock_get_response
        mock_get_auth_session.return_value = mock_session

        #facebook session
        response = self.client.get('/callback/facebook?code=some_code', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # when response is new user, db entry created
        self.assertEqual(db.session.query(User).count(), 1)
        # when response is existing user, no entry added
        mock_get_response.json.return_value = {'name': 'Dummy', 'id': '3617923766551'}
        self.assertTrue('Currently logged in as Dummy' in response.get_data(
            as_text=True))

        #github session
        response = self.client.get('/callback/github?code=some_code', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # when response is new user, db entry created
        self.assertEqual(db.session.query(User).count(), 1)
        # when response is existing user, no entry added
        mock_get_response.json.return_value = {'name': 'Dummy', 'id': '3617923766551'}
        self.assertTrue('Currently logged in as Dummy' in response.get_data(
            as_text=True))

        #google session
        response = self.client.get('/callback/google?code=some_code', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # when response is new user, db entry created
        self.assertEqual(db.session.query(User).count(), 1)
        # when response is existing user, no entry added
        mock_get_response.json.return_value = {'name': 'Dummy', 'id': '3617923766551'}
        self.assertTrue('Currently logged in as Dummy' in response.get_data(
            as_text=True))
        
        
