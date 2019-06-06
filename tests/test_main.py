import unittest
import os
from datetime import datetime

from flask import current_app
from flask_login import current_user
from st_webservice import create_app, db
from st_webservice.models import User, Image, load_user
from werkzeug.datastructures import FileStorage
from st_webservice.main import utils
from st_webservice.model.run_st import run_style_transfer

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

    def test_generate_image(self):
        # register a new account
        response = self.client.post('/register', data={
            'reg_email': 'dummy@example.com',
            'reg_username': 'Dummy_96',
            'reg_password': 'Dummy_pwd_96',
            'reg_rpassword': 'Dummy_pwd_96'
        })
        self.assertEqual(response.status_code, 302)
        # log in with the new account
        response = self.client.post('/login', data={
            'log_username': 'Dummy_96',
            'log_password': 'Dummy_pwd_96',
            'log_remember': False
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Currently logged in as Dummy_96',
                                  response.get_data(as_text=True))
        style_file = None
        content_file = None
        with open('st_webservice/static/images/style/hSkxYmV.jpg', 'rb') as sfp:
            with open('st_webservice/static/images/content/BsrOXBL.jpg', 'rb') as cfp:
                style_file = FileStorage(sfp)
                content_file = FileStorage(cfp)
                files = [content_file, style_file]
                content_name = utils.generate_image_filename()
                style_name = utils.generate_image_filename()
                result_name = utils.generate_image_filename()
                result_file_name, file_extension = os.path.splitext(result_name)
                file_names = [content_name, style_name]
                for i, file in enumerate(files):
                    self.assertNotEqual(file.filename, '')
                    self.assertTrue(utils.allowed_file(file.filename))
                    if file:
                       if i == 0:
                            file.save(os.path.join(current_app.config['UPLOAD_CONTENT_FOLDER'], file_names[i]))
                       else:
                            file.save(os.path.join(current_app.config['UPLOAD_STYLE_FOLDER'], file_names[i]))

        #generate 256x256 test_image for 100 iterations
        current_app.config['OUTPUT_PARAMS'] = current_app.config['MODEL_PARAMS'].copy();
        current_app.config['MODEL_PARAMS']['content_path'] = current_app.config['UPLOAD_CONTENT_FOLDER'] + file_names[0];
        current_app.config['MODEL_PARAMS']['style_path'] = current_app.config['UPLOAD_STYLE_FOLDER'] + file_names[1];
        current_app.config['MODEL_PARAMS']['result_path'] = current_app.config['OUTPUT_IMAGE_FOLDER'] + result_name;
        current_app.config['MODEL_PARAMS']['loss_path'] = current_app.config['OUTPUT_STAT_FOLDER'] + result_file_name + "_loss" + file_extension;
        current_app.config['MODEL_PARAMS']['exec_path'] = current_app.config['OUTPUT_STAT_FOLDER'] + result_file_name + "_time" + file_extension;
        current_app.config['MODEL_PARAMS']['num_iterations'] = 100
        current_app.config['MODEL_PARAMS']['img_w'] = 256
        current_app.config['MODEL_PARAMS']['img_h'] = 256

        ## run model
        result_dict = run_style_transfer(**current_app.config['MODEL_PARAMS'])
        self.assertNotEqual(result_dict, None)

        ## update results
        current_app.config['OUTPUT_PARAMS'].update({
        'total_time': result_dict['total_time'],
        'total_loss': result_dict['total_losses'][-1].numpy(),
        'style_loss': result_dict['style_losses'][-1].numpy(),
        'content_loss': result_dict['content_losses'][-1].numpy(),
        'gen_image_width': result_dict['gen_image_width'],
        'gen_image_height': result_dict['gen_image_height'],
        'model_name': result_dict['model_name'],
        'content_path': "../static/test/images/upload/content/" + file_names[0],
        'style_path': "../static/test/images/upload/style/" + file_names[1],
        'result_path': "../static/test/images/output/images/" + result_name,
        'loss_path': "../static/test/images/output/graphs/" + result_file_name + "_loss" + file_extension,
        'exec_path': "../static/test/images/output/graphs/" + result_file_name + "_time" + file_extension,
        });


        ## create a user and associate the generated image
        user = User(
        id=42,
        email='dummytest@example.com',
        username='DummyTest_96',
        )
        user.set_password('Dummypwd_96')
        db.session.add(user)
        db.session.commit()


        image = Image(
        id=42,
        gen_image_path=current_app.config['OUTPUT_PARAMS']['result_path'],
        gen_image_width=current_app.config['OUTPUT_PARAMS']['gen_image_width'],
        gen_image_height=current_app.config['OUTPUT_PARAMS']['gen_image_height'],
        num_iters=current_app.config['OUTPUT_PARAMS']['num_iterations'],
        model_name=current_app.config['OUTPUT_PARAMS']['model_name'],
        total_loss=str(current_app.config['OUTPUT_PARAMS']['total_loss']),
        style_loss=str(current_app.config['OUTPUT_PARAMS']['style_loss']),
        content_loss=str(current_app.config['OUTPUT_PARAMS']['content_loss']),
        timestamp=datetime.utcnow(),
        user_id=42
        )
        image.set_user(user)
        db.session.add(image)
        db.session.commit()
        self.assertEqual(Image.query.filter_by(user_id=42).count(),1)

        # render the results
        response = self.client.get('/results/42', 
                                   follow_redirects=True)
        self.assertEqual(user.id, 42)

        # check gallery page
        response = self.client.get('/user_images/42')
        self.assertEqual(user.user_images.count(), 1)
        self.assertEqual([False, False, False],
            [message
           in response.get_data(
                as_text=True) for message in ['No images to show.','Access denied: Incorrect user.','Authentication failed: User does not exist.']])

        # check image stats
        response = self.client.get('/user_images/42/42/popup')
        self.assertEqual(user.user_images.count(), 1)
        self.assertEqual([False, False, False],
            [message
           in response.get_data(
                as_text=True) for message in ['Image deleted from local storage.','Access denied: Incorrect user.','Authentication failed: User does not exist.']])

        # delete the image
        response = self.client.get('/user_images/42/42/delete')
        self.assertEqual([False, False, False],
            [message
           in response.get_data(
                as_text=True) for message in ['Image not found.','Access denied: Incorrect user.','Authentication failed: User does not exist.']])

        img_location = image.gen_image_path
        db.session.delete(image)
        db.session.commit()
        graph_folder = 'st_webservice/static/test/images/output/graphs'

        # comment the try/except block to save the test images and graphics to disk
        try:
            os.remove(os.path.join('st_webservice/', img_location[3:]))
            # remove all test graphics from disk
            for file in os.listdir(graph_folder):
                file_path = os.path.join(graph_folder, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        except FileNotFoundError:
            logger.error('File not found in path.')

        self.assertEqual(user.user_images.count(), 0)
        self.assertEqual(Image.query.filter_by(user_id=42).count(),0)

