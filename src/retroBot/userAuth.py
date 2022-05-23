from twitchAPI.helper import build_url, build_scope, TWITCH_AUTH_BASE_URL, get_uuid
from time import sleep
from twitchAPI.oauth import UserAuthenticator, refresh_access_token
from twitchAPI.types import AuthScope
from threading import Thread
from appdirs import user_data_dir
import requests
import webbrowser
import pickle
import os
import logging


class userAuth:

    def __init__(self, twitch, username, scope=[AuthScope.CHAT_EDIT, AuthScope.CHAT_READ], refresh_callback=None):
        self.logger = logging.getLogger(f'retroBot.{username}.userAuth')
        self.username = username
        self.twitch = twitch
        self.twitch.user_auth_refresh_callback = self.oauth_user_refresh_callback
        self.scope = scope
        self.refresh_callback = refresh_callback
        self.get_oauth_token()
        self.refresh_thread = Thread(target=self.authentication_loop, args=(), daemon=True)
        self.refresh_thread.start()

    def authentication_loop(self, interval=24*60**2):
        self.logger.info(f'Refreshing user authentication every {interval} seconds')
        while True:
            sleep(interval)
            try:
                self.oauth_user_refresh()
            except Exception as e:
                self.logger.error(e)

    def authenticate_twitch(self):
        try:
            if webbrowser.get().name == 'www-browser':
                self.token, self.refresh_token = authenticate_cli(self.twitch, self.scope)
            else:
                self.auth = UserAuthenticator(self.twitch, self.scope, force_verify=False)
                self.token, self.refresh_token = self.auth.authenticate()
        except Exception as e:
            self.logger.error(e)
            self.token, self.refresh_token = authenticate_cli(self.twitch, self.scope)
        self.save_oauth_token()

    def get_oauth_token(self):
        tokens = self.load_oauth_token()
        if tokens == None:
            self.authenticate_twitch()
        else:
            self.token = tokens[0]
            self.refresh_token = tokens[1]
        try:
            self.twitch.set_user_authentication(self.token, self.scope, self.refresh_token)
        except Exception as e:
            self.logger.error(e)
            self.authenticate_twitch()
            self.twitch.set_user_authentication(self.token, self.scope, self.refresh_token)

    def save_oauth_token(self):
        self.logger.debug(f'Saving OAuth Token...')
        pickle_file = self.get_oauth_file()
        with open(pickle_file, 'wb') as f:
            pickle.dump((self.token, self.refresh_token), f)
        self.logger.debug(f'OAuth Token has been saved')

    def load_oauth_token(self):
        pickle_file = self.get_oauth_file()
        if os.path.exists(pickle_file):
            with open(pickle_file, 'rb') as f:
                out = pickle.load(f)
            self.logger.debug(f'OAuth Token has been loaded')
            return out
        else:
            return None

    def get_oauth_file(self):
        pickle_dir = user_data_dir('retroBot', 'retrontology')
        if not os.path.exists(pickle_dir): os.makedirs(pickle_dir, exist_ok=True)
        return os.path.join(pickle_dir, f'{self.username}_oauth.pickle')

    def oauth_user_refresh(self, refresh_token=None):
        if refresh_token == None:
            refresh_token = self.refresh_token
        self.token, self.refresh_token = refresh_access_token(refresh_token, self.twitch.app_id, self.twitch.app_secret)
        self.twitch.set_user_authentication(self.token, self.scope, self.refresh_token)
        self.oauth_user_refresh_callback()
    
    def oauth_user_refresh_callback(self, token=None, refresh_token=None):
        if token == None:
            token = self.token
        if refresh_token == None:
            refresh_token = self.refresh_token
        self.token = token
        self.refresh_token = refresh_token
        self.save_oauth_token()
        if self.refresh_callback:
            self.refresh_callback(token, refresh_token)

def authenticate_cli(twitch, scopes, callback_url='https://retrohollow.com/twitchAuth.php'):
    params = {
        'client_id': twitch.app_id,
        'redirect_uri': callback_url,
        'response_type': 'code',
        'scope': build_scope(scopes),
        'force_verify': 'false',
        'state': str(get_uuid())
    }
    print(f'Visit this URL and paste the code below: {build_url(TWITCH_AUTH_BASE_URL + "oauth2/authorize", params)}')
    user_token = input('Enter Code: ')
    params = {
        'client_id': twitch.app_id,
        'client_secret': twitch.app_secret,
        'code': user_token,
        'grant_type': 'authorization_code',
        'redirect_uri': callback_url
    }
    url = build_url(TWITCH_AUTH_BASE_URL + 'oauth2/token', params)
    response = requests.post(url)
    data = response.json()
    return data['access_token'], data['refresh_token']
        