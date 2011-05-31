from google.appengine.api import memcache
from google.appengine.ext import db

import models
import common

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

def create_chat(query_1 = None, query_2 = None, user_key_1 = None, user_key_2 = None, title_1 = None, title_2 = None):
  if query_1 is not None:
    user_key_1 = query_1.key().parent()
    title_2 = query_1.query_string
  
  if query_2 is not None:
    user_key_2 = query_2.key().parent()
    title_1 = query_2.query_string

  chat_id = common.get_chat_key_name(user_key_1, user_key_2)

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

def delete_userchat(userchat_key):
  pass

def delete_user(user_id):
  user_key = db.Key.from_path('User', user_id)
  todel = []
  todel.append(user_key)

  # queries
  todel.extend(db.Query(models.Query, keys_only = True).ancestor(user_key).fetch(5000))

  # query indexes
  todel.extend(db.Query(models.QueryIndex, keys_only = True).filter('user =', user_key).fetch(5000))

  # unread chats
  todel.extend(db.Query(models.UnreadChat, keys_only = True).ancestor(user_key).fetch(5000))

  # google logins
  todel.extend(db.Query(models.GoogleLogin, keys_only = True).filter('user =', user_key).fetch(5000))

  db.delete(todel)

def get_top_searches(count = 10):
  top_searches_query = db.Query(models.TopSearch).order('-rating')

  top_searches = []
  for r in top_searches_query.fetch(count):
    top_searches.append(r.query_string)
  return top_searches

def get_login_hash():
  import random
  random.seed()
  return common.get_hash(str(random.random()))

def get_cookie_expiration(num_days):
    from datetime import datetime, timedelta
    d = datetime.now() + timedelta(days = num_days)
    return d.strftime("%a, %d-%b-%Y %H:%M:%S GMT")

