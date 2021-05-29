from twitchBot.channelHandler import channelHandler
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope
from twitchAPI.webhook import TwitchWebHook
from twitchBot.userAuth import authenticate
from threading import Thread
from random import randint
from time import sleep
import itertools
import more_itertools
import socket
import webbrowser
import ssl
import irc.bot
import logging
import logging.handlers
import pickle
import os


class twitchBot(irc.bot.SingleServerIRCBot):

    def __init__(self, username, client_id, client_secret, channels, handler=channelHandler, webhook_host='', webhook_port=0, ssl_cert='fullchain.pem', ssl_key='privkey.pem'):
        self.username = username
        self.logger = logging.getLogger(f"twitchBot.{username}")
        self.client_id = client_id
        self.client_secret = client_secret
        self.setup_twitch()
        if webhook_host != '':
            self.webhook = self.setup_webhook(webhook_host, webhook_port, self.client_id, ssl_cert, ssl_key, self.twitch)
        else:
            self.webhook = None
        self.irc_server = 'irc.chat.twitch.tv'
        self.irc_port = 6667
        self.channel_handlers = {}
        for channel in channels:
            self.channel_handlers[channel.lower()] = handler(channel.lower(), self)
        irc.bot.SingleServerIRCBot.__init__(self, [(self.irc_server, self.irc_port, 'oauth:'+self.token)], self.username, self.username)
    
    def setup_webhook(self, host, port, client_id, cert, key, twitch):
        if port == 0:
            while True:
                p = randint(1025, 65535)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    is_open = s.connect_ex(('localhost', port)) == 0
                    s.shutdown()
                    s.close()
                    if is_open:
                        port = p
                        break
        ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(certfile=cert, keyfile=key)
        hook = TwitchWebHook('https://' + host + ":" + str(port), client_id, port, ssl_context=ssl_context)
        hook.authenticate(twitch)
        hook.start()
        return hook

    def on_welcome(self, c, e):
        self.logger.info('Joined Twitch IRC server!')
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        for channel in self.channel_handlers:
            c.join('#' + channel.lower())

    def on_join(self, c, e):
        self.logger.debug(f'Joined {e.target}!')

    def on_pubmsg(self, c, e):
        self.logger.debug(f'Passing message to {e.target[1:]} handler')
        Thread(target=self.channel_handlers[e.target[1:]].on_pubmsg, args=(c, e, )).start()
    
    def setup_twitch(self):
        self.logger.info(f'Setting up Twitch API client...')
        self.twitch = Twitch(self.client_id, self.client_secret)
        self.twitch.user_auth_refresh_callback = self.oauth_user_refresh
        self.twitch.authenticate_app([])
        self.get_oauth_token()
        self.auth_thread = Thread(target=self.authentication_loop, args=(), daemon=True)
        self.auth_thread.start()
        self.logger.info(f'Twitch API client set up!')
    
    def authentication_loop(self):
        while True:
            sleep(24*60**2)
            try:
                self.twitch.refresh_used_token()
            except Exception as e:
                self.logger.error(e)

    def authenticate_twitch(self, target_scope):
        try:
            cli = webbrowser.get().name == 'www-browser'
            if cli:
                self.token, self.refresh_token = authenticate(self.twitch, target_scope)
            else:
                auth = UserAuthenticator(self.twitch, target_scope, force_verify=False)
                self.token, self.refresh_token = auth.authenticate()
        except Exception as e:
            self.logger.error(e)
            self.token, self.refresh_token = authenticate(self.twitch, target_scope)
        self.save_oauth_token()

    def get_oauth_token(self):
        tokens = self.load_oauth_token()
        target_scope = [AuthScope.CHAT_EDIT, AuthScope.CHAT_READ]
        if tokens == None:
            self.authenticate_twitch(target_scope)
        else:
            self.token = tokens[0]
            self.refresh_token = tokens[1]
        try:
            self.twitch.set_user_authentication(self.token, target_scope, self.refresh_token)
        except Exception as e:
            self.logger.error(e)
            self.authenticate_twitch(target_scope)
            self.twitch.set_user_authentication(self.token, target_scope, self.refresh_token)

    def save_oauth_token(self):
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
        else: return None

    def get_oauth_file(self):
        pickle_dir = os.path.join(os.path.dirname(__file__), 'oauth')
        if not os.path.exists(pickle_dir): os.mkdir(pickle_dir)
        pickle = os.path.join(pickle_dir, f'{self.username}_oauth.pickle')
        return pickle
    
    def oauth_user_refresh(self, token, refresh_token):
        self.logger.debug(f'Refreshing OAuth Token')
        self.token = token
        self.refresh_token = refresh_token
        self.save_oauth_token()
        self.disconnect()
        specs = map(irc.bot.ServerSpec.ensure, [(self.irc_server, self.irc_port, 'oauth:'+self.token)])
        self.servers = more_itertools.peekable(itertools.cycle(specs))
        self._connect()
        self.logger.debug(f'Oauth Token is refreshed!')