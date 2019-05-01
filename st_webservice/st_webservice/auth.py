
import json
import urllib3
from bs4 import BeautifulSoup
from rauth import OAuth2Service, OAuth1Service
from flask import current_app, url_for, request, redirect, session

class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]

class FacebookSignIn(OAuthSignIn):
    def __init__(self):
        super(FacebookSignIn, self).__init__('facebook')
        self.service = OAuth2Service(
            name='facebook',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://graph.facebook.com/oauth/authorize',
            access_token_url='https://graph.facebook.com/oauth/access_token',
            base_url='https://graph.facebook.com/')

    def authorize(self):
        url = str(self.get_callback_url())
        url = url.replace("http://", "https://")
        return redirect(self.service.get_authorize_url(
                scope='email',
                response_type='code',
                redirect_uri=url))

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))

        if 'code' not in request.args:
            return None, None, None

        url = str(self.get_callback_url())
        url = url.replace("http://", "https://")
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': url},
            decoder=decode_json
        )
        me = oauth_session.get('me?fields=id,name,email').json()
        social_id = 'facebook$' + me['id']
        username = me['name']
        email = me.get('email', None)
        return (social_id, username, email)

class GithubSignIn(OAuthSignIn):
    def __init__(self):
        super(GithubSignIn, self).__init__('github')
        self.service = OAuth2Service(
            name='github',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://github.com/login/oauth/authorize',           
            access_token_url='https://github.com/login/oauth/access_token',
            base_url='https://api.github.com/'
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code')
        )

    def callback(self):
        if 'code' not in request.args:
            return None, None, None
        
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code']}
        )
        me = oauth_session.get('user').json()
        social_id = 'github$' + str(me['id'])
        username = me.get('name')
        return social_id, username, None

class GoogleSignIn(OAuthSignIn):
    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        response = urllib3.PoolManager().request('GET', 'https://accounts.google.com/.well-known/openid-configuration')
        google_params = json.loads(response.data.decode('utf-8'))
        self.service = OAuth2Service(
                name='google',
                client_id=self.consumer_id,
                client_secret=self.consumer_secret,
                authorize_url=google_params.get('authorization_endpoint'),
                base_url=google_params.get('userinfo_endpoint'),
                access_token_url=google_params.get('token_endpoint')
        )

    def authorize(self):
        url = str(self.get_callback_url())
        url = url.replace("http://", "https://")
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=url)
            )

    def callback(self):
        def decode_json(payload):
            return json.loads(payload.decode('utf-8'))

        if 'code' not in request.args:
            return None, None, None

        url = str(self.get_callback_url())
        url = url.replace("http://", "https://")
        oauth_session = self.service.get_auth_session(
                data={'code': request.args['code'],
                      'grant_type': 'authorization_code',
                      'redirect_uri': url
                     },
                decoder = decode_json
        )
        me = oauth_session.get('').json()
        social_id = 'google$' + me['sub']
        return (social_id,
                me.get('email').split('@')[0],
                me['email'])
