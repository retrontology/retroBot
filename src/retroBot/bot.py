from retroBot.channelHandler import channelHandler
from twitchAPI.twitch import Twitch
from retroBot.userAuth import userAuth
from threading import Thread
from random import randint
import itertools
import more_itertools
import socket
import ssl
import irc.bot
import logging
import logging.handlers
from time import sleep


class retroBot(irc.bot.SingleServerIRCBot):

    def __init__(self, username, client_id, client_secret, channels, handler=None):
        self.username = username
        self.logger = logging.getLogger(f"retroBot.{username}")
        self.client_id = client_id
        self.client_secret = client_secret
        self.setup_twitch()
        self.irc_server = 'irc.chat.twitch.tv'
        self.irc_port = 6667
        self.channel_handlers = None
        if handler:
            self.channel_handlers = {}
            for channel in channels:
                try:
                    self.channel_handlers[channel.lower()] = handler(channel.lower(), self)
                except Exception as e:
                    self.logger.error(e)
        irc.bot.SingleServerIRCBot.__init__(self, [(self.irc_server, self.irc_port, 'oauth:'+self.user_auth.token)], self.username, self.username)

    def on_welcome(self, c, e):
        self.logger.info('Joined Twitch IRC server!')
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        sleep(1)
        if self.channel_handlers:
            Thread(target=self.join_channels, daemon=True).start()

    def join_channels(self):
        for channel in self.channel_handlers:
            self.connection.join('#' + channel.lower())
            sleep(0.1)

    def on_join(self, c, e):
        self.logger.debug(f'Joined {e.target}!')

    def on_pubmsg(self, c, e):
        self.logger.debug(f'Passing message to {e.target[1:]} handler')
        if self.channel_handlers:
            Thread(target=self.channel_handlers[e.target[1:]].on_pubmsg, args=(c, e, )).start()
    
    def setup_twitch(self):
        self.logger.info(f'Setting up Twitch API client...')
        self.twitch = Twitch(self.client_id, self.client_secret)
        self.twitch.authenticate_app([])
        self.user_auth = userAuth(self.twitch, self.username, refresh_callback=self.oauth_user_refresh)
        self.logger.info(f'Twitch API client set up!')
    
    def oauth_user_refresh(self, token, refresh_token):
        self.disconnect()
        specs = map(irc.bot.ServerSpec.ensure, [(self.irc_server, self.irc_port, 'oauth:'+self.user_auth.token)])
        self.servers = more_itertools.peekable(itertools.cycle(specs))
        self._connect()