import json
import sys
import time
from flask import render_template
from rq import get_current_job
from st_webservice import create_app
from st_webservice.models import User, Image
from st_webservice.auth.email import send_email
import sys

app = create_app()
app.app_context().push()

def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        if progress >= 100:
            task.complete = True
        db.session.commit()


def export_images(user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_images = user.user_images.count()
        for image in user.user_images.order_by(Image.timestamp.asc()):
            data.append({'image_width': image.gen_image_width,
                         'image_height': image.gen_image_height,
                         'timestamp': image.timestamp.isoformat() + 'Z'})
            time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_images)

        send_email('[StyleAI] Your generated image information',
                sender=app.config['ADMINS'][0], recipients=[user.email],
                text_body=render_template('email/export_images.txt', user=user),
                html_body=render_template('email/export_images.html', user=user),
                attachments=[('images.json', 'application/json',
                              json.dumps({'images': data}, indent=4))],
                sync=True)
    except:
        _set_task_progress(100)
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())