from twitchBot.bot import twitchBot
from twitchBot.config import config

c = config('config.yaml')
t = twitchBot(c['username'], c['client_id'], c['client_secret'], c['channels'])
t.start()