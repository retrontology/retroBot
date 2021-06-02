from retroBot.message import message
import logging

class channelHandler():

    def __init__(self, channel, parent):
        self.logger = logging.getLogger(f'retroBot.{parent.username}.{channel}')
        self.logger.info(f'Initializing Channel Handler for {channel}')
        self.channel = channel
        self.parent = parent
        self.logger.info('Channel handler set up!')
    
    def on_pubmsg(self, c, e):
        msg = message(e)
        if msg.content[:1] == '!':
            self.handle_commands(msg)
        else:
            pass
                
    def send_message(self, message):
        self.logger.info(f'Sending: {message}')
        self.parent.connection.privmsg('#' + self.channel, message)
    
    def handle_commands(self, msg):
        cmd = msg.content.split(' ')[0][1:].lower()
    
    def get_user_id(self):
        return self.parent.twitch.get_users(logins=[self.channel.lower()])['data'][0]['id']