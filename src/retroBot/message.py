import datetime
import pytz

class message():

    def __init__(self, event):
        self.parse_msg_event(event)
   
    def parse_msg_event(self, event):
        self.content = event.arguments[0]
        self.client_nonce = None
        for tag in event.tags:
            if tag['key'] == 'display-name':
                self.username = tag['value']
            elif tag['key'] == 'user-id':
                self.user_id = int(tag['value'])
            elif tag['key'] == 'tmi-sent-ts':
                self.time = pytz.utc.localize(datetime.datetime.fromtimestamp(float(tag['value'])/1000))
            elif tag['key'] == 'badge-info':
                self.badge_info = self.parse_badge_info(tag['value'])
                if self.badge_info != None:
                    if 'subscriber' in self.badge_info.keys():
                        self.sub_length = int(self.badge_info['subscriber'])
                    else:
                        self.sub_length = None
                    if 'predictions' in self.badge_info.keys():
                        self.prediction = self.badge_info['predictions']
                    else:
                        self.prediction = None
                else:
                    self.sub_length = None
                    self.prediction = None
            elif tag['key'] == 'badges':
                self.badges = self.parse_badges(tag['value'])
                self.broadcaster = 'broadcaster/1' in self.badges
            elif tag['key'] == 'client-nonce':
                self.client_nonce = tag['value']
            elif tag['key'] == 'color':
                self.color = tag['value']
            elif tag['key'] == 'emotes':
                self.emotes = tag['value']
            elif tag['key'] == 'flags':
                self.flags = tag['value']
            elif tag['key'] == 'id':
                self.id = tag['value']
            elif tag['key'] == 'mod':
                self.mod = tag['value'] == '1'
            elif tag['key'] == 'room-id':
                self.room_id = int(tag['value'])
            elif tag['key'] == 'subscriber':
                self.sub = tag['value'] == '1'
            elif tag['key'] == 'turbo':
                self.turbo = tag['value'] == '1'

    @staticmethod
    def parse_badges(value):
        if value != None:
            badges = value.split(',')
        else:
            badges = None
        return badges
    
    @staticmethod
    def parse_emotes(value):
        emotes = {}
        if value != None:
            for e in value.split('/'):
                number, places= e.split(':', 1)
                index = []
                for place in places.split(','):
                    start, end = place.split('-', 1)
                    index.append((int(start), int(end)))
                emotes[number] = index.copy()
        return emotes

    @staticmethod
    def parse_flags(value):
        out = {}
        if value != None:
            for flag in value.split(','):
                pos, flag_indexes = flag.split(':', 1)
                start, end = pos.split('-', 1)
                flags = []
                for flag_index in flag_indexes.split('/'):
                    letter, number = flag_index.split('.')
                    flags.append((letter, int(number)))
                out[(int(start), int(end))] = flags.copy()
        return out
    
    @staticmethod
    def parse_badge_info(value):
        if value != None:
            badge_info = {}
            for info in value.split(','):
                key, value = info.split('/', 1)
                badge_info[key] = value
            return badge_info
        else:
            return None

    def __str__(self):
        return str(self.__dict__)