import datetime
import pytz

class message():

    def __init__(self, event):
        self.parse_msg_event(event)
   
    def parse_msg_event(self, event):
        self.content = event.arguments[0]
        for tag in event.tags:
            if tag['key'] == 'display-name':
                self.username = tag['value']
            elif tag['key'] == 'user-id':
                self.user_id = int(tag['value'])
            elif tag['key'] == 'tmi-sent-ts':
                self.time = pytz.utc.localize(datetime.datetime.fromtimestamp(float(tag['value'])/1000))
            elif tag['key'] == 'badge-info':
                self.parse_sub_length(tag['value'])
            elif tag['key'] == 'badges':
                self.badges = self.parse_badges(tag['value'])
                self.broadcaster = 'broadcaster/1' in self.badges
            elif tag['key'] == 'client-nonce':
                self.client_nonce = tag['value']
            elif tag['key'] == 'color':
                self.color = tag['value']
            elif tag['key'] == 'emotes':
                self.emotes = self.parse_emotes(tag['value'])
            elif tag['key'] == 'flags':
                self.flags = self.parse_flags(tag['value'])
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
        badges = []
        if value != None:
            badges = value.split(',')
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
    def parse_sub_length(value):
        sub_length = None
        if value != None:
            sub_length = value.split('/')[1]
        return sub_length

    def __str__(self):
        return str(self.__dict__)