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
    m = models.UserContext.get_by_key_name(str(user_key.id_or_name()))
    if m is None:
      m = models.UserContext(key_name = str(user_key.id_or_name()), context = None)
    memcache.set("user_%s_context" % user_key.id_or_name(), m, cache_duration)
  return m.context

def set_user_context(user_key, context, cache_duration = 300):
  m = models.UserContext(key_name = str(user_key.id_or_name()), context = context)
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

def get_query_key_name(clean_string):
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

def calc_query_rating(user_idle_time, query_time):
  if user_idle_time < config.OFFLINE_THRESHOLD:
    u = 1
  elif user_idle_time < config.INACTIVE_THRESHOLD:
    u = 0.5
  else:
    u = 0

  timediff = datetime.datetime.now() - query_time
  a = min(timediff.days / 30, 1)

  rating = (u * 0.7)
  rating += (1 - a) * 0.3

  return rating

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

