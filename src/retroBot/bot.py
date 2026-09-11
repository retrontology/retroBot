from twitchAPI import Twitch, EventSub
from retroBot.userAuth import userAuth
from threading import Thread, Lock
from random import randint
import itertools
import more_itertools
import irc.bot
import irc.client
import logging
import logging.handlers
from time import sleep, monotonic


JOIN_RETRY_LIMIT = 5
JOIN_RETRY_INTERVAL = 1
JOIN_RATE_LIMIT = 20
JOIN_RATE_WINDOW = 10.1


class retroBot(irc.bot.SingleServerIRCBot):

    def __init__(
        self, 
        username, 
        client_id, 
        client_secret, 
        channels=None,
        handler=None, 
        multithread=False, 
        ffz=False, 
        bttv=False, 
        seventv=False,
        eventsub=False,
        callback_url=None,
        port=None
    ):
        self.username = username
        self._multithread = multithread
        self.logger = logging.getLogger(f"retroBot.{username}")
        self.client_id = client_id
        self.client_secret = client_secret
        self.ffz = ffz
        self.bttv = bttv
        self.seventv = seventv
        self._joining = False
        self._join_lock = Lock()
        self._join_times = []
        # The IRC target has to be set before setup_twitch, because the token
        # refresh callback installed there rebuilds the server list from it.
        self.irc_server = 'irc.chat.twitch.tv'
        self.irc_port = 6667
        self.setup_twitch(eventsub, callback_url, port)
        self.channel_handlers = None
        if handler:
            self.channel_handlers = {}
            for channel in (channels or []):
                try:
                    self.channel_handlers[channel.lower()] = handler(channel.lower(), self, ffz=ffz, bttv=bttv, seventv=seventv)
                except Exception as e:
                    self.logger.error(f'Error setting up handler for channel {channel}: {e}')
        super().__init__([(self.irc_server, self.irc_port, 'oauth:'+self.user_auth.token)], self.username, self.username)
        self.connection.add_global_handler('privnotice', self._on_privnotice, -20)

    def on_welcome(self, c, e):
        self.logger.info('Joined Twitch IRC server!')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        if self.channel_handlers:
            Thread(target=self.join_channels, daemon=True).start()
    
    def _on_privnotice(self, connection, event):
        if len(event.arguments) == 1 and event.arguments[0] == 'Login authentication failed':
            self.logger.warning('Login authentication failed, refreshing user token')
            # This runs on the reactor thread, so an exception escaping here
            # would take down the bot's event loop.
            try:
                self.user_auth.oauth_user_refresh()
            except Exception as e:
                self.logger.error(f'Could not refresh user token after login failure: {e}')
        else:
            self.logger.info(f'privnotice event: {event}')

    def _throttle_joins(self):
        """Hold sent JOINs to Twitch's limit of 20 per 10 seconds.

        Retries count against the limit as well, so this tracks every JOIN
        actually put on the wire rather than the number of channels processed.
        """
        now = monotonic()
        self._join_times = [t for t in self._join_times if now - t < JOIN_RATE_WINDOW]
        if len(self._join_times) >= JOIN_RATE_LIMIT:
            wait = JOIN_RATE_WINDOW - (now - self._join_times[0])
            if wait > 0:
                self.logger.debug(f'Join rate limit reached, waiting {wait:.1f}s')
                sleep(wait)
            now = monotonic()
            self._join_times = [t for t in self._join_times if now - t < JOIN_RATE_WINDOW]
        self._join_times.append(monotonic())

    def join_channel(self, channel):
        """Join a channel, retrying a bounded number of times.

        Returns True once the channel appears in self.channels. A channel that
        can never be joined is logged and skipped instead of retried forever.
        """
        channel = f'#{channel.lower()}'
        for attempt in range(1, JOIN_RETRY_LIMIT + 1):
            if channel in self.channels:
                return True
            self._throttle_joins()
            try:
                self.connection.join(channel)
            except irc.client.ServerNotConnectedError:
                self.logger.warning(f'Disconnected while trying to join {channel}')
                return False
            sleep(JOIN_RETRY_INTERVAL)
            if channel in self.channels:
                return True
            self.logger.debug(f'No join confirmation for {channel} on attempt {attempt}')
        self.logger.warning(f'Could not join {channel} after {JOIN_RETRY_LIMIT} attempts, skipping it')
        return False

    def join_channels(self):
        # Serialised rather than guarded by a flag, so a reconnect arriving
        # while an earlier pass is still running queues behind it instead of
        # being dropped. Each pass is idempotent: join_channel returns
        # immediately for channels that are already joined.
        with self._join_lock:
            self._joining = True
            try:
                for channel in list(self.channel_handlers):
                    if not self.connection.is_connected():
                        self.logger.warning('Disconnected, abandoning the remaining channel joins')
                        return
                    self.join_channel(channel)
            except Exception:
                self.logger.exception('Unhandled error while joining channels')
            finally:
                self._joining = False

    def on_join(self, c, e):
        if e.source.nick == c.get_nickname():
            self.logger.debug(f'Joined {e.target}!')

    def on_pubmsg(self, c, e):
        if not self.channel_handlers:
            return
        channel = e.target[1:]
        handler = self.channel_handlers.get(channel)
        if handler is None:
            self.logger.warning(f'Got a message for {channel}, which has no handler')
            return
        self.logger.debug(f'Passing message to {channel} handler')
        if self._multithread:
            Thread(target=handler.on_pubmsg, args=(c, e, ), daemon=True).start()
        else:
            handler.on_pubmsg(c, e)
    
    def setup_twitch(self, eventsub=False, callback_url=None, port=None):
        self.logger.info(f'Setting up Twitch API client...')
        self.twitch = Twitch(self.client_id, self.client_secret)
        self.twitch.authenticate_app([])
        self.user_auth = userAuth(self.twitch, self.username, refresh_callback=self.oauth_user_refresh)
        if eventsub:
            if not callback_url or not port:
                raise Exception('callback_url and port must be specified when using EventSub!')
            self.eventsub = EventSub(callback_url, self.client_id, port, self.twitch)
            self.eventsub.unsubscribe_all()
            self.eventsub.start()
            self.logger.info(f'EventSub initiated!')
        else:
            self.eventsub = None
        self.logger.info(f'Twitch API client set up!')
    
    def oauth_user_refresh(self, token=None, refresh_token=None):
        # userAuth installs this callback during setup_twitch, which runs before
        # super().__init__ creates self.connection, so a refresh that lands
        # during construction has no connection to rebuild yet.
        if not hasattr(self, 'connection'):
            self.logger.debug('User token refreshed before IRC setup, nothing to reconnect')
            return
        password = 'oauth:' + (token or self.user_auth.token)
        specs = map(irc.bot.ServerSpec.ensure, [(self.irc_server, self.irc_port, password)])
        self.servers = more_itertools.peekable(itertools.cycle(specs))
        self.logger.info('Reconnecting with the refreshed user token')
        self.disconnect()
        self._connect()
