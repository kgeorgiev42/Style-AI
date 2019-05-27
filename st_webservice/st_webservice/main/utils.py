import uuid

ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'bmp'])

def generate_image_filename(extension=True):
    if extension:
        return str(uuid.uuid4()) + '.png'
    else:
        return str(uuid.uuid4())

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
