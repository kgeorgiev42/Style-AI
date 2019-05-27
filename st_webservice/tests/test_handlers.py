import unittest

from st_webservice import create_app, db
from st_webservice.models import User, Image

class FlaskHandlersTestCase(unittest.TestCase):
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

    def testNotFound(self):
        response = self.client.post('/unknown')
        self.assertEqual(response.status_code, 404)
