from retroBot.channelHandler import channelHandler
from twitchAPI.twitch import Twitch
from retroBot.userAuth import userAuth
from threading import Thread
from random import randint
import itertools
import more_itertools
import irc.bot
from irc.client import ServerConnectionError
import logging
import logging.handlers
from time import sleep


class retroBot(irc.bot.SingleServerIRCBot):

    def __init__(self, username, client_id, client_secret, channels, handler=None, multithread=False, ffz=False, bttv=False, seventv=False ):
        self.username = username
        self._multithread = multithread
        self.logger = logging.getLogger(f"retroBot.{username}")
        self.client_id = client_id
        self.client_secret = client_secret
        self._joining = False
        self.setup_twitch()
        self.irc_server = 'irc.chat.twitch.tv'
        self.irc_port = 6667
        self.channel_handlers = None
        if handler:
            self.channel_handlers = {}
            for channel in channels:
                try:
                    self.channel_handlers[channel.lower()] = handler(channel.lower(), self, ffz=ffz, bttv=bttv, seventv=seventv)
                except Exception as e:
                    self.logger.error(e.with_traceback())
        irc.bot.SingleServerIRCBot.__init__(self, [(self.irc_server, self.irc_port, 'oauth:'+self.user_auth.token)], self.username, self.username)

    def on_welcome(self, c, e):
        self.logger.info('Joined Twitch IRC server!')
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        if self.channel_handlers and not self._joining:
            Thread(target=self.join_channels, daemon=True).start()
    
    def _connect(self):
        server = self.servers.peek()
        try:
            self.connect(
                server.host,
                server.port,
                self._nickname,
                server.password,
                ircname=self._realname,
                **self.__connect_params,
            )
        except ServerConnectionError as e:
            self.logger.error(f'Error connecting to server: {e}')

    def join_channels(self):
        self._joining = True
        count = 0
        for channel in self.channel_handlers:
            self.connection.join('#' + channel.lower())
            if count >= 19:
                sleep(10.1)
                count = 0
            else:
                count += 1
        self._joining = False

    def on_join(self, c, e):
        self.logger.debug(f'Joined {e.target}!')

    def on_pubmsg(self, c, e):
        self.logger.debug(f'Passing message to {e.target[1:]} handler')
        if self.channel_handlers:
            if self._multithread:
                Thread(target=self.channel_handlers[e.target[1:]].on_pubmsg, args=(c, e, )).start()
            else:
                self.channel_handlers[e.target[1:]].on_pubmsg(c, e)
    
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