from datetime import timedelta

OFFLINE_THRESHOLD = 10
STATUS_UPDATE_THRESHOLD = 5

ITEMS_PER_PAGE = 15
MAX_SEARCH_KEYWORDS = 6
MAX_KEYWORDS = 100

RANDOM_CHAT_WAIT = 2

REQUEST_TIMESTAMP_PADDING = timedelta(seconds = 3)

OPEN_CHAT_THRESHOLD = timedelta(seconds = 3)

CHAT_HISTORY_MESSAGE_COUNT = 40

MAX_UNREAD_CHATS = 20

NOTIFICATION_DURATION = 3

LOGIN_EXPIRATION_DAYS = 60

def MEMCACHE_LAST_BEEN_ONLINE(user_id):
  return 'last_been_online_%s' % user_id

def MEMCACHE_CHAT_UPDATE_ID(chat_id):
  return '%s_chat_update_id' % chat_id

def MEMCACHE_USER_UPDATE_ID(user_id):
  return '%s_user_update_id' % user_id

def MEMCACHE_USER_NOTIFICATION(user_id, notification_id):
  return '%s_update_%s' % (user_id, notification_id)

def MEMCACHE_USER_UNREAD_COUNT(user_id):
  return '%s_unread_count' % user_id

def MEMCACHE_USER_OPEN_CHAT(user_id, chat_id):
  return '%s_open_chat_%s' % (user_id, chat_id)

def MEMCACHE_PEER_ID(user_id, chat_id):
  return '%s_peer_id_%s' % (user_id, chat_id)
