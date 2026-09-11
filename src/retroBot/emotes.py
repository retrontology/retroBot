import requests
from logging import getLogger
import re

RETRY_LIMIT = 5


def emote_regex(text):
    """Compile a regex matching a whitespace delimited emote code.

    The code is escaped so metacharacters in user defined emote names cannot
    break compilation or change the match, and the edges are whitespace
    lookarounds rather than \\b so codes that begin or end with a non word
    character (:tf:, D:, c!) still match.
    """
    return re.compile(f'(?<!\\S){re.escape(text)}(?!\\S)')


class emoteParser():

    global_emotes = None
    global_url = None
    channel_url = None
    logger = getLogger('retrobot.emoteparser')

    def __init__(self, channel):
        self.channel = channel
        self.logger = getLogger(f'{type(self).logger.name}.{channel}')
        self.channel_emotes = None
        if self.global_emotes == None:
            self.update_globals()
        self.update_channel()

    def get_channel_url(self):
        return self.channel_url.format(self.channel)

    @classmethod
    def get_emotes(cls, url):
        response = None
        tries = 0
        while tries < RETRY_LIMIT:
            tries += 1
            try:
                response = requests.get(url)
            except requests.RequestException as e:
                cls.logger.warning(f'Error requesting {url} (attempt {tries}): {e}')
                continue
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as e:
                    cls.logger.warning(f'Invalid JSON from {url} (attempt {tries}): {e}')
                    continue
            if 400 <= response.status_code < 500:
                # A client error is definitive, retrying it will not help
                cls.logger.info(f'Got status {response.status_code} from {url}')
                return None
            cls.logger.warning(f'Got status {response.status_code} from {url} (attempt {tries})')
        cls.logger.error(f'Giving up on {url} after {tries} attempts')
        return None

    @classmethod
    def update_globals(cls):
        pass

    def update_channel(self):
        pass

    def parse_emotes(self, message):
        emote_strings = []
        for emote in (self.global_emotes or []) + (self.channel_emotes or []):
            regexp = emote['regex']
            matches = [match for match in regexp.finditer(message)]
            if len(matches) > 0:
                emote_string = f'{emote["id"]}:'
                occurances = []
                for match in matches:
                    occurances.append(f'{match.start()}-{match.end()-1}')
                emote_string += ','.join(occurances)
                emote_strings.append(emote_string)
        if emote_strings:
            return '/'.join(emote_strings)
        else:
            return None
            

class ffzEmoteParser(emoteParser):

    logger = getLogger(emoteParser.logger.name + '.ffz')
    global_url = 'https://api.frankerfacez.com/v1/set/global'
    channel_url = 'https://api.frankerfacez.com/v1/room/id/{}'

    @staticmethod
    def ffz_map(emote):
        return {
            'id': emote['id'], 
            'text': emote['name'],
            'regex': emote_regex(emote['name'])
        }
    
    @classmethod
    def update_globals(cls):
        response = cls.get_emotes(cls.global_url)
        global_emotes = []
        if isinstance(response, dict) and 'default_sets' in response and 'sets' in response:
            for emote_set in response['default_sets']:
                emote_set = response['sets'].get(str(emote_set))
                if not emote_set:
                    continue
                emotes = [x for x in map(cls.ffz_map, emote_set['emoticons'])]
                global_emotes.extend(emotes)
        else:
            cls.logger.warning('Could not load FFZ global emotes')
        cls.global_emotes = global_emotes

    def update_channel(self):
        response = self.get_emotes(self.get_channel_url())
        channel_emotes = []
        if isinstance(response, dict) and 'sets' in response:
            emote_set = response['sets'].get(str(response.get('room', {}).get('set')))
            if emote_set:
                channel_emotes = [x for x in map(self.ffz_map, emote_set['emoticons'])]
        else:
            self.logger.info(f'No FFZ emotes for {self.channel}')
        self.channel_emotes = channel_emotes



class bttvEmoteParser(emoteParser):

    logger = getLogger(emoteParser.logger.name + '.bttv')
    global_url = 'https://api.betterttv.net/3/cached/emotes/global'
    channel_url = 'https://api.betterttv.net/3/cached/users/twitch/{}'

    @staticmethod
    def bttv_map(emote):
        return {
            'id': emote['id'], 
            'text': emote['code'],
            'regex': emote_regex(emote['code'])
            }

    @classmethod
    def update_globals(cls):
        response = cls.get_emotes(cls.global_url)
        global_emotes = []
        if isinstance(response, list):
            global_emotes = [x for x in map(cls.bttv_map, response)]
        else:
            cls.logger.warning('Could not load BTTV global emotes')
        cls.global_emotes = global_emotes

    def update_channel(self):
        response = self.get_emotes(self.get_channel_url())
        channel_emotes = []
        if isinstance(response, dict) and 'channelEmotes' in response:
            channel_emotes = [x for x in map(self.bttv_map, response['channelEmotes'])]
            channel_emotes.extend(map(self.bttv_map, response.get('sharedEmotes', [])))
        else:
            self.logger.info(f'No BTTV emotes for {self.channel}')
        self.channel_emotes = channel_emotes

class seventvEmoteParser(emoteParser):

    logger = getLogger(emoteParser.logger.name + '.seventv')
    global_url = 'https://api.7tv.app/v2/emotes/global'
    channel_url = 'https://api.7tv.app/v2/users/{}/emotes'

    @staticmethod
    def seventv_map(emote):
        return {
            'id': emote['id'], 
            'text': emote['name'],
            'regex': emote_regex(emote['name'])
            }

    @classmethod
    def update_globals(cls):
        response = cls.get_emotes(cls.global_url)
        global_emotes = []
        if isinstance(response, list):
            global_emotes = [x for x in map(cls.seventv_map, response)]
        else:
            cls.logger.warning('Could not load 7TV global emotes')
        cls.global_emotes = global_emotes

    def update_channel(self):
        response = self.get_emotes(self.get_channel_url())
        channel_emotes = []
        if isinstance(response, list):
            channel_emotes = [x for x in map(self.seventv_map, response)]
        else:
            self.logger.info(f'No 7TV emotes for {self.channel}')
        self.channel_emotes = channel_emotes
