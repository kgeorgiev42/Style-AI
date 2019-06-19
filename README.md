# Style-AI

<b>StyleAI</b> is a Flask web app, which integrates the [Neural Style Transfer](https://www.cv-foundation.org/openaccess/content_cvpr_2016/papers/Gatys_Image_Style_Transfer_CVPR_2016_paper.pdf) algorithm for generating artistic images. It allows the user to import custom style and content images used for generation and to set the initial model parameters before starting the model. After the generation is complete, the result image is saved to the user's gallery, where the image can be viewed along with the model performance statistics (content loss, style loss, etc..) and also deleted.

![Image generation](https://i.imgur.com/8fcui0K.png)

![Learning curves](https://i.imgur.com/LKuy3Cu.png)

![Gallery](https://i.imgur.com/X1F0RJG.png)

## Main features

- User registration and an <b>OAuth2</b> authentication service through Google, Facebook and Github using the <b>Rauth</b> library.
- Reset password feature using <b>Flask-Mail</b> as an asynchronous <b>Celery</b> task for seding emails in the background.
- <b>SQLite</b> database for storing image-related data and creating the user gallery.
- <b>Tensorflow Keras</b>-based Deep Learning model for Neural Style Transfer created on [Google Colab](https://colab.research.google.com/drive/1DGL1r83hRhIq7HXGFbre53tsGUSnDlNK)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1DGL1r83hRhIq7HXGFbre53tsGUSnDlNK)

## Project structure

![Project structure](https://i.imgur.com/Udhs8y0.png)

## Requirements

- An NVIDIA GPU with the CUDA and CuDNN libraries installed (preferably GTX 8th gen and above) to run tensorflow's GPU version (if you don't have an NVIDIA GPU, you can switch to the CPU version by replacing  ```tensorflow-gpu==1.13.1 ```  with  ```tensorflow==1.13.1 ```  in the <i>requirements.txt</i> file.)
- Python v3.5 or above, preferably in the Anaconda environment.
- [Ngrok](https://ngrok.com/) server for creating a tunneled session, in order to run the app locally in a real domain. This is required for the <b>OAuth</b> authentication services, because they don't accept localhost.
- [Redis](https://redis.io/) server for running background <b>Celery</b> workers for the email service.

## Running the app

<b>1.</b> Clone the project from this repository to your local directory using:
```
git clone https://github.com/JadeBlue96/Style-AI.git 
```
<b>2.</b> If you have Anaconda installed, it would be a good idea to create a separate environment for the project, for example:
```
conda create -n tf-style python=3.5
conda activate tf-style
```
<b>3.</b> Install the required libraries by navigating to the <i>st_webservice</i> folder and using pip:
```
cd st_webservice 
pip install –r requirements.txt
```
<b>4.</b> Run the app in <b>Visual Studio 2017</b> or from the console by setting the <b>Flask</b> environment variables:
```
set FLASK_APP=runserver.py
set FLASK_ENV=development / testing
flask run
```
<b>5.</b> Run the unit tests with the following command:
```
flask test --coverage
```
<b>6.</b> To reset the database, delete the <i>db</i> file and the migrations folder and enter:
```
flask db init
flask db migrate -m "custom message"
```
<b>7.</b> Testing the authentication services:
- Run the Ngrok server on port 5000:
```
ngrok.exe http 5000
```
- Change the URLs in <i>layout.html</i> to the generated one in the <b>Forwarding</b> section for HTTPS, for example:
```
$('.facebook-btn').click(function () {window.location = "https://1e498486.ngrok.io/authorize/facebook";}); 
$('.google-btn').click(function () {window.location = "https://1e498486.ngrok.io/authorize/google";}); 
$('.github-btn').click(function () {window.location = "https://1e498486.ngrok.io/authorize/github";});
```
- Create a developer's app for the service you want to test:

-- For <b>Facebook</b>: add the <b>Facebook Login</b> extension to your app and set the following URLs in <b>Valid OAuth Redirect URIs</b>:
```<your-generated-url>```, ```<your-generated-url>/callback/facebook```, ```<your-generated-url>/authorize/facebook```

-- For <b>Github</b>: go to your app in <i>Settings/Developer Settings/OAuth Apps</i> and change the homepage URL to your generated base url and the authorization callback URL to: ```<your-generated-url>/callback/github```

-- For <b>Google</b>: go to <i>Credentials/OAuth Consent Screen/Authorized Domains</i> and add your generated base url; then in the app's settings in <b>Authorized Redirect URIs</b> add your base url and ```<your-generated-url>/callback/google```

<b>8.</b> Testing the reset password feature:
- Start the Redis server
- Create a pool of <b>Celery</b> workers from a separate console using:

```celery –A st_webservice worker –-pool=eventlet –l info```

- Set the environment variables for the mail server (example for Gmail):
```
set MAIL_SERVER=smtp.googlemail.com 
set MAIL_PORT=587 
set MAIL_USE_TLS=1 
set MAIL_USERNAME=<client username> 
set MAIL_PASSWORD=<client password>
```

<b>9. (Update)</b> Create your own free [Amazon S3](https://aws.amazon.com/s3/) storage bucket for serving the images to the cloud. After that, edit your <i>.env</i> file and/or <i>config.py</i> and set the environment variables concerning the credentials and the bucket url (example):

```
.env

AWS_ACCESS_KEY_ID=<your amazon access key id>
AWS_SECRET_ACCESS_KEY=<your amazon secret access key>
```

```
config.py

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
FLASKS3_BUCKET_NAME = <your bucket name>
S3_LOCATION = 'https://{}.s3.amazonaws.com/'.format(FLASKS3_BUCKET_NAME)
S3_OBJECT_URL = <your object url> (example: 'https://styleai.s3.us-east-2.amazonaws.com/')
```

## Update: Heroku Deployment
As of this point, the app has now been successfully deployed to Heroku in the cloud and is available on https://style-ai.herokuapp.com/.

However, due to the fact that I am using free tier dynos, bear in mind that it takes about 1 minute to load the server and the working pool. Heroku also does not provide GPU support and has limited CPU memory, so the model will inevitably run significantly slower in the cloud.

With that said, here is how to configure this app to run locally through <b>Heroku</b> with <b>GPU</b> support:
<b>1.</b> Create a <i>.env</i> file in the main directory with your environment variables:
```
.env

FLASK_APP=runserver.py
FLASK_CONFIG=heroku
MAIL_USERNAME=<your mail username>
MAIL_PASSWORD=<your mail password>
REDIS_URL=redis://
AWS_ACCESS_KEY_ID=<your amazon access key id>
AWS_SECRET_ACCESS_KEY=<your amazon secret access key>
```

<b>2.</b> Make sure that <i>config.py</i> has the url for the local Redis server specified:
```
CELERY_BROKER_URL = 'redis://localhost:6379/0' #os.environ['REDIS_URL'] for cloud version
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0' #os.environ['REDIS_URL']
```

<b>3.</b> Make sure that the <i>Procfile</i> has the local port set for the <b>waitress</b> server:
```
web: waitress-serve --port=5000 runserver:app 
worker: celery -A st_webservice worker --pool=eventlet -l info
```

<b>4.</b> Start your Redis server and initialize the heroku server using:
```
heroku local:run flask deploy
heroku local
```

If you want to test the cloud deployment version make sure you switch to the <b>deployment</b> branch. The correct environment variables should be specified there. After making a change to the cloud version, commit your changes and push them to <b>Heroku</b> using:
```
git push heroku deployment:master
```
Afterwards, you might want to restart the working dynos or run an upgrade to the database depending on your changes:
```
heroku run flask deploy
heroku restart
```


## Acknowledgements
Big thanks to Miguel Grinberg for his [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world) series, as well as his Flask Web Development book.





