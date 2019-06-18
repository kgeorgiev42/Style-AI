import uuid
import boto3, botocore
from io import BytesIO
from PIL import Image
from flask import current_app
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import StrMethodFormatter

ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'bmp'])

def generate_image_filename(extension=True):
    if extension:
        return str(uuid.uuid4()) + '.png'
    else:
        return str(uuid.uuid4())

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def upload_file_to_s3(file, bucket_name, acl="public-read"):

    """
    Docs: http://boto3.readthedocs.io/en/latest/guide/s3.html
    """

    try:
        s3 = boto3.client("s3", aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'], aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'])
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )

    except Exception as e:
        print("Uncaught exception: ", e)
        return e

    return "{}{}".format(current_app.config["S3_LOCATION"], file.filename)

def save_image_s3(best_img, filename):

  print('Saving image file to s3..')
  in_mem_file = BytesIO()
  best_img.save(in_mem_file, format='png')
  in_mem_file.seek(0)
  app = current_app._get_current_object()
  with app.app_context():
    s3 = boto3.client("s3", aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'], aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'])
    s3.upload_fileobj(
    in_mem_file,
    current_app.config['FLASKS3_BUCKET_NAME'],
    filename,
    ExtraArgs={
        'ACL': 'public-read'
    }
    )

  return "{}{}".format(current_app.config["S3_LOCATION"], filename)

def delete_image_s3(result_file, loss_file, exec_file):

  print('Deleting image files for object from s3..')
  app = current_app._get_current_object()
  with app.app_context():
    s3 = boto3.client("s3", aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'], aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'])
    s3.delete_object(Bucket=current_app.config['FLASKS3_BUCKET_NAME'], Key=result_file)
    s3.delete_object(Bucket=current_app.config['FLASKS3_BUCKET_NAME'], Key=loss_file)
    s3.delete_object(Bucket=current_app.config['FLASKS3_BUCKET_NAME'], Key=exec_file)

def plot_learning_curve_s3(iterations, total_losses, style_losses, content_losses, img_file_name):
  
  plt.figure(figsize=(8, 8))
  
  plt.xlabel('Iterations')
  plt.ylabel('Losses')
  plt.title('Style Transfer: Loss function by iterations')
  
  plt.gca().yaxis.set_major_formatter(StrMethodFormatter('{x:,.1e}'))
  plt.plot(iterations[1:], total_losses, label="Total loss")
  plt.plot(iterations[1:], style_losses, label="Style loss")
  plt.plot(iterations[1:], content_losses, label="Content loss")
  plt.legend()
  
  print('Saving learning curve to s3..')
  in_mem_file = BytesIO()
  plt.savefig(in_mem_file, format='png')
  in_mem_file.seek(0)
  app = current_app._get_current_object()
  with app.app_context():
    s3 = boto3.client("s3", aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'], aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'])
    s3.upload_fileobj(
    in_mem_file,
    current_app.config['FLASKS3_BUCKET_NAME'],
    img_file_name,
    ExtraArgs={
        'ACL': 'public-read'
    }
    )

  return "{}{}".format(current_app.config["S3_LOCATION"], img_file_name)
  #plt.tight_layout()
  #plt.show()


# In[29]:


def plot_time_s3(iterations, times, img_file_name):
  plt.figure(figsize=(8,8))
  
  plt.title("Style Transfer computation time by iterations")
  plt.xlabel("Iterations")
  plt.ylabel("Time (s)")
  
  plt.plot(iterations[1:], times[1:], label="Time")
  
  print('Saving time curve to s3..')
  in_mem_file = BytesIO()
  plt.savefig(in_mem_file, format='png')
  in_mem_file.seek(0)
  app = current_app._get_current_object()
  with app.app_context():
    s3 = boto3.client("s3", aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'], aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'])
    s3.upload_fileobj(
    in_mem_file,
    current_app.config['FLASKS3_BUCKET_NAME'],
    img_file_name,
    ExtraArgs={
        'ACL': 'public-read'
    }
    )

  return "{}{}".format(current_app.config["S3_LOCATION"], img_file_name)
  #plt.tight_layout()
  #plt.show()


