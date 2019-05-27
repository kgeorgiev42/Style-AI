import unittest

from st_webservice import create_app, db
from st_webservice.models import User, Image
from st_webservice.main import utils

class FlaskMainTestCase(unittest.TestCase):
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

    def test_utils(self):
        gen_filename = utils.generate_image_filename()
        self.assertEqual(gen_filename.split('.')[1], 'png')
        gen_filename = utils.generate_image_filename(extension=False)
        self.assertTrue('.' not in gen_filename)
        self.assertTrue(utils.allowed_file('example.png'))
        self.assertFalse(utils.allowed_file('example.gif'))
