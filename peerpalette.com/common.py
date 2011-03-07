from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.api import users

from gaesessions import get_current_session
import models
import datetime

import os
import config
import hashlib
import base64

def get_online_users():
  u = memcache.get('online_users')
  if not u:
    t = datetime.datetime.now() - datetime.timedelta(seconds = OFFLINE_THRESHOLD)
    q = db.Query(models.User, keys_only = True).filter('last_been_online >', t)
    u = set(q.fetch())
    memcache.add('online_users', u, STATUS_UPDATE_THRESHOLD)

  return u

def _get_user(user_key, clear_unread):
  user = models.User.get(user_key)
  try:
    i = user.unread_chat.index(clear_unread)
    del user.unread_chat[i]
    del user.unread_first_timestamp[i]
    t = user.unread_last_timestamp.pop(i)
    user.put()
    return user, True
  except: # TODO use specific exception
    pass

  return user, False

def get_current_user_info(timestamp = None, clear_unread = None):
  now = datetime.datetime.now()
  if timestamp is None:
    timestamp = now - config.REQUEST_TIMESTAMP_PADDING
  user = None
  session = get_current_session()
  user_key = None
  if session.has_key("user"):
    user_key = session["user"]
  elif session.has_key("anon_user"):
    user_key = session["anon_user"]

  if user_key is not None:
    if clear_unread:
      user, cleared = db.run_in_transaction(_get_user, user_key, clear_unread)
      user._cleared = cleared
    else:
      user = models.User.get(user_key)

  if user is None:
    user = models.User()
    user.put()
    session["anon_user"] = str(user.key())
    session.pop("user")

  user._unread_count = 0
  user._new_chats = []
  user._updated_chats = []
  user._new_timestamp = timestamp

  for i in range(len(user.unread_chat)):
    if now > user.unread_first_timestamp[i] + config.UNREAD_THRESHOLD:
      user._unread_count += 1
      if timestamp < user.unread_first_timestamp[i]:
        user._new_chats.append(user.unread_chat[i])
        try:
          user._new_timestamp = max(user._new_timestamp, user.unread_first_timestamp[i])
        except:
          user._new_timestamp = user.unread_first_timestamp[i]
      elif timestamp < user.unread_last_timestamp[i] and now > user.unread_last_timestamp[i] + config.UNREAD_THRESHOLD:
        user._updated_chats.append(user.unread_chat[i])
        try:
          user._new_timestamp = max(user._new_timestamp, user.unread_last_timestamp[i])
        except:
          user._new_timestamp = user.unread_last_timestamp[i]

  last_been_online = memcache.get("last_been_online_%d" % user.key().id())

  if last_been_online is None:
    user_status = models.UserStatus.get_by_key_name(str(user.key().id()))
    if user_status:
      last_been_online = user_status.last_been_online

  if last_been_online is None or (datetime.datetime.now() - last_been_online).seconds >= config.STATUS_UPDATE_THRESHOLD:
    status = models.UserStatus(key_name = str(user.key().id_or_name()))
    status.put()
    memcache.set("last_been_online_%d" % user.key().id(), datetime.datetime.now(), time = config.OFFLINE_THRESHOLD)

  if last_been_online is None or (datetime.datetime.now() - last_been_online).seconds >= config.OFFLINE_THRESHOLD:
    online_user = models.OnlineUser(key_name = str(user.key().id_or_name()))
    online_user.put()

  return user

def get_user_status(user_keys):
  if type(user_keys).__name__ == 'list':
    ids = []
    for u in user_keys:
      ids.append(str(u.id()))
  else:
    ids = str(user_keys.id())

  return models.UserStatus.get_by_key_name(ids)

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

def get_query_key_name(user_id, clean_string):
  return get_hash(str(user_id) + ':' + clean_string)

def get_chat_key_name(user_id, peer_query_key_name):
  return get_hash(str(user_id) + ':' + peer_query_key_name)

def get_random_chat_key_name(user_id, peer_id):
  return get_hash("random:" + str(user_id) + ":" + str(peer_id))

def get_ref_key(inst, prop_name):
  return getattr(inst.__class__, prop_name).get_value_for_datastore(inst)

def calc_query_rating(user_idle_time, num_keywords, query_time):
  if user_idle_time < config.OFFLINE_THRESHOLD:
    u = 1
  elif user_idle_time < config.INACTIVE_THRESHOLD:
    u = 0.5
  else:
    u = 0
  k = min(num_keywords / config.MAX_KEYWORDS, 1)

  timediff = datetime.datetime.now() - query_time
  a = min(timediff.days / 30, 1)

  rating = (u * 0.7)
  rating += (1 - k) * 0.1
  rating += (1 - a) * 0.2

  return rating

