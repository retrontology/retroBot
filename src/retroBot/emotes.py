import requests
from logging import getLogger

RETRY_LIMIT = 5

class emoteParser():

    global_emotes = None
    global_url = None
    channel_url = None
    logger = getLogger('retrobot.emoteparser')

    def __init__(self, channel):
        self.channel = channel
        self.logger = f'{self.logger.name}.{channel}'
        self.channel_emotes = None
        if self.global_emotes == None:
            self.update_globals()
        self.update_channel()

    def get_channel_url(self):
        return self.channel_url.format(self.channel)

    @staticmethod
    def get_emotes(url):
        response = None
        tries = 0
        while tries < (response is None or response.code not in (200,)):
            response = requests.get(url)
            tries += 1
        return response.json()

    @classmethod
    def update_globals(cls):
        pass

    def update_channel(self):
        pass

    def parse_emotes(self):
        pass

class ffzEmoteParser(emoteParser):

    logger = getLogger(emoteParser.logger.name + '.ffz')
    global_url = 'https://api.frankerfacez.com/v1/set/global'
    channel_url = 'https://api.frankerfacez.com/v1/room/id/{}'

    @staticmethod
    def ffz_map(emote):
        return {'id': emote['id'], 'text': emote['name']}
    
    @classmethod
    def update_globals(cls):
        response = cls.get_emotes(cls.global_url)
        global_emotes = []
        if response:
            for emote_set in response['default_sets']:
                emote_set = response['sets'][set]
                emotes = [map(cls.ffz_map, emote_set['emoticons'])]
                global_emotes.extend(emotes)
        cls.global_emotes = global_emotes


    def update_channel(self):
        response = self.get_emotes(self.get_channel_url())
        channel_emotes = []
        if response:
            emote_set = response['sets'][response['room']['set']]
            channel_emotes = [map(self.ffz_map, emote_set['emoticons'])]
        self.channel_emotes = channel_emotes



class bttvEmoteParser(emoteParser):

    logger = getLogger(emoteParser.logger.name + '.bttv')
    global_url = 'https://api.betterttv.net/3/cached/emotes/global'
    channel_url = 'https://api.betterttv.net/3/cached/users/twitch/{}'

    @staticmethod
    def bttv_map(emote):
        return {'id': emote['id'], 'text': emote['code']}

    @classmethod
    def update_globals(cls):
        response = cls.get_emotes(cls.global_url)
        global_emotes = []
        if response:
            global_emotes = [map(cls.bttv_map, response)]
        cls.global_emotes = global_emotes

    def update_channel(self):
        response = self.get_emotes(self.get_channel_url())
        channel_emotes = []
        if response:
            channel_emotes = [map(self.bttv_map, response['channelEmotes'])]
            channel_emotes.extend(map(self.bttv_map, response['sharedEmotes']))
        self.channel_emotes = channel_emotes

class seventvEmoteParser(emoteParser):

    logger = getLogger(emoteParser.logger.name + '.seventv')
    global_url = 'https://api.7tv.app/v2/emotes/global'
    channel_url = 'https://api.7tv.app/v2/users/{}/emotes'

    @staticmethod
    def seventv_map(emote):
        return {'id': emote['id'], 'text': emote['name']}

    @classmethod
    def update_globals(cls):
        response = cls.get_emotes(cls.global_url)
        global_emotes = []
        if response:
            global_emotes = [map(cls.seventv_map, response)]
        cls.global_emotes = global_emotes

    def update_channel(self):
        response = self.get_emotes(self.get_channel_url())
        channel_emotes = []
        if response:
            channel_emotes = [map(self.seventv_map, response)]
        self.channel_emotes = channel_emotes