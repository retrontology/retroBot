from retroBot.message import message
from threading import Thread
import logging

class channelHandler():

    def __init__(self, channel, parent):
        self.logger = logging.getLogger(f'retroBot.{parent.username}.{channel}')
        self.logger.info(f'Initializing Channel Handler for {channel}')
        self.channel = channel
        self.parent = parent
        self.webhook_uuid = None
        self.live = False
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

    def get_live(self):
        data = self.parent.twitch.get_streams(user_id=self.user_id)
        if not data['data']:
            self.live = False
            self.logger.info(f'{self.channel} is not live')
        elif data['data'][0]['type'] == 'live':
            self.live = True
            self.logger.info(f'{self.channel} is live!')
        else:
            self.live = False
        return self.live

    def webhook_stream_changed_subscribe(self, callback):
        success, uuid = self.parent.webhook.subscribe_stream_changed(self.user_id, callback)
        if success:
            self.webhook_uuid = uuid
            self.logger.info(f'Subscribed to webhook for {self.channel}')
        else:
            self.webhook_uuid = None
        return success

    def webhook_stream_changed_unsubscribe(self):
        if self.webhook_uuid:
            success = self.parent.webhook.unsubscribe(self.webhook_uuid)
            if success:
                self.webhook_uuid = ''
                self.logger.info(f'Unsubscribed from webhook for {self.channel}')
            return success
    
    def callback_stream_changed(self, uuid, data):
        self.logger.info(f'Received webhook callback for {self.channel}')
        if data['type'] == 'live':
            if not self.live:
                self.live = True
                self.logger.info(f'{self.channel} has gone live!')
                Thread(target=self.callback_stream_gone_live, args=(uuid, data), daemon=True).start()
            else:
                self.live = True
                self.logger.info(f'{self.channel} has changed stream data')
                Thread(target=self.callback_stream_changed_data, args=(uuid, data), daemon=True).start()
        else:
            self.live = False
            self.logger.info(f'{self.channel} has gone offline')
            Thread(target=self.callback_stream_gone_live, args=(uuid, data), daemon=True).start()
    
    def callback_stream_gone_live(self, uuid, data):
        pass

    def callback_stream_changed_data(self, uuid, data):
        pass

    def callback_stream_gone_offline(self, uuid, data):
        pass