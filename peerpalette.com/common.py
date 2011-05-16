from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.api import users

from gaesessions import get_current_session
import config
import models

import datetime
import os
import hashlib
import base64

# Source: http://stackoverflow.com/questions/561486/how-to-convert-an-integer-to-the-shortest-url-safe-string-in-python
import string
ALPHABET = '-' + string.digits + string.ascii_uppercase + '_' + string.ascii_lowercase
ALPHABET_REVERSE = dict((c, i) for (i, c) in enumerate(ALPHABET))
BASE = len(ALPHABET)
SIGN_CHARACTER = '$'
def num_encode(n, digits = None):
  if n < 0:
    return SIGN_CHARACTER + num_encode(-n, digits)
  s = []
  while True:
    n, r = divmod(n, BASE)
    s.append(ALPHABET[r])
    if n == 0: break
  if digits is not None:
    if len(s) > digits:
      s = s[0-digits:]
    elif len(s) < digits:
      s.extend([ALPHABET[0]] * (digits-len(s)))
  return ''.join(reversed(s))
def num_decode(s):
  if s[0] == SIGN_CHARACTER:
    return -num_decode(s[1:])
  n = 0
  for c in s:
    n = n * BASE + ALPHABET_REVERSE[c]
  return n

def get_online_users():
  u = memcache.get('online_users')
  if not u:
    t = datetime.datetime.now() - datetime.timedelta(seconds = OFFLINE_THRESHOLD)
    q = db.Query(models.User, keys_only = True).filter('last_been_online >', t)
    u = set(q.fetch())
    memcache.set('online_users', u, STATUS_UPDATE_THRESHOLD)

  return u

def clear_old_unread_messages(unread):
  threshold = datetime.datetime.now() - datetime.timedelta(seconds = 5)
  for k in unread.keys():
    v = unread[k]
    try:
      if v['read_timestamp'] >= v['last_timestamp'] and v['last_timestamp'] < threshold:
        del unread[k]
        continue
    except KeyError:
      pass

    try:
      v['messages'] = [(m,t) for m,t in v['messages'] if t > threshold]
    except KeyError:
      pass

def get_current_user_key():
  session = get_current_session()
  if session.has_key("user"):
    return session["user"]
  elif session.has_key("anon_user"):
    return session["anon_user"]

  return None

def get_user_status(user_keys):
  if type(user_keys).__name__ == 'list':
    ids = []
    for u in user_keys:
      ids.append(db.Key.from_path('UserStatus', u.id_or_name()))
  else:
    ids = db.Key.from_path('UserStatus', user_keys.id_or_name())

  return models.UserStatus.get(ids)

def get_user_context(user_key, cache_duration = 300):
  m = memcache.get("user_%s_context" % user_key.id_or_name())
  if m is None:
    context_key = db.Key.from_path('UserContext', user_key.id_or_name())
    m = models.UserContext.get(context_key)
    if m is None:
      m = models.UserContext(key = context_key, context = None)
    memcache.set("user_%s_context" % user_key.id_or_name(), m, cache_duration)
  return m.context

def set_user_context(user_key, context, cache_duration = 300):
  context_key = db.Key.from_path('UserContext', user_key.id_or_name())
  m = models.UserContext(key = context_key, context = context)
  m.put()
  memcache.set("user_%s_context" % user_key.id_or_name(), m, cache_duration)

def get_user_idle_time(user_status):
  if user_status is None:
    return 5184000

  timediff = datetime.datetime.now() - user_status.last_been_online
  return (timediff.seconds) + (timediff.days * 24 * 60 * 60)

def get_status_class(status):
  if status < config.OFFLINE_THRESHOLD:
    return "online"
  elif status < config.INACTIVE_THRESHOLD:
    return "offline"

  return "inactive"

# source: http://stackoverflow.com/questions/531157/parsing-datetime-strings-with-microseconds
def str2datetime(s):
    parts = s.split('.')
    dt = datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
    if len(parts) > 1:
      return dt.replace(microsecond=int(parts[1]))
    return dt

def get_hash(string):
  hsh = base64.urlsafe_b64encode(hashlib.md5(string.encode('utf-8')).digest())
  return hsh.rstrip('=')

def get_query_hash(clean_string):
  return get_hash(clean_string)

def xor(hash1, hash2):
  r = ''
  for i in range(len(hash1)):
    r += chr(ord(hash1[i]) ^ ord(hash2[i]))
  return r

def get_chat_key_name(user_key_1, user_key_2):
  return base64.urlsafe_b64encode(xor(hashlib.md5(str(user_key_1)).digest(), hashlib.md5(str(user_key_2)).digest()))

def get_ref_key(inst, prop_name):
  return getattr(inst.__class__, prop_name).get_value_for_datastore(inst)

def create_chat(query_1 = None, query_2 = None, user_key_1 = None, user_key_2 = None, title_1 = None, title_2 = None):
  if query_1 is not None:
    user_key_1 = query_1.key().parent()
    title_2 = query_1.query_string
  
  if query_2 is not None:
    user_key_2 = query_2.key().parent()
    title_1 = query_2.query_string

  chat_id = get_chat_key_name(user_key_1, user_key_2)

  userchat_key_1 = db.Key.from_path('User', user_key_1.id_or_name(), 'UserChat', chat_id)
  userchat_key_2 = db.Key.from_path('User', user_key_2.id_or_name(), 'UserChat', chat_id)

  userchat_1, userchat_2 = db.get([userchat_key_1, userchat_key_2])
  if userchat_1 is not None and userchat_2 is not None:
    return userchat_1, userchat_2

  chat_key = db.Key.from_path('Chat', chat_id)
  chat = models.Chat(key = chat_key)

  userchat_name_1 = models.User.get_username(user_key_2)
  userchat_name_2 = models.User.get_username(user_key_1)

  userchat_1 = models.UserChat(key = userchat_key_1, chat = chat_key, peer_userchat = userchat_key_2, name = userchat_name_1, title = title_1)
  userchat_2 = models.UserChat(key = userchat_key_2, chat = chat_key, peer_userchat = userchat_key_1, name = userchat_name_2, title = title_2)

  db.put([chat, userchat_1, userchat_2])

  return userchat_1, userchat_2

def encode_if_num(s):
  if isinstance(s, (int, long)):
    return "#%d" % s
  return s

def decode_if_num(s):
  if s[0] == '#':
    return long(s[1:])
  return s

def encode_query_index_key_name(query_key):
  td = datetime.datetime(2040, 1, 1) - datetime.datetime.now()
  timestamp = num_encode(td.seconds + (td.days * 24 * 3600), 5)
  query_id = encode_if_num(query_key.id_or_name())
  username = encode_if_num(query_key.parent().id_or_name())
  return "%s %s %s" % (timestamp, username, query_id)

def decode_query_index_key_name(key_name):
  timestamp, username, query_id = key_name.split()
  return db.Key.from_path('User', decode_if_num(username), 'Query', decode_if_num(query_id))

def sanitize_string(string, num_characters = 400, num_lines = 4):
  return "\n".join(string[:num_characters].split("\n")[:num_lines])

def htmlize_string(string):
  from cgi import escape
  return escape(string).replace("\n", "<br/>")

