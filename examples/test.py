from retroBot import retroBot
from retroBot.config import config
import logging

logger = logging.getLogger('retroBot')
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
form = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
stream_handler.setFormatter(form)
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)
c = config('config.yaml')
t = retroBot(c['username'], c['client_id'], c['client_secret'], c['channels'])
t.start()