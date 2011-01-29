from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import taskqueue

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

def _update_user(user_key, clear_unread):
  user = models.User.get(user_key)

  try:
    i = user.unread_chat.index(clear_unread)
    del user.unread_chat[i]
    del user.unread_timestamp[i]
    user.put()
    return user
  except: # TODO use specific exception
    pass

  return user

def get_user(clear_unread = None):
  user = None
  session = get_current_session()

  if session.has_key("user"):
    if clear_unread:
      user = db.run_in_transaction(_update_user, session["user"], clear_unread)
    else:
      user = models.User.get(session["user"])

  if user is None:
    user = models.User()
    user.put()
    session["user"] = str(user.key())

  last_been_online = memcache.get("last_been_online_%d" % user.key().id())

  if last_been_online is None:
    user_status = models.UserStatus.get_by_key_name(str(user.key().id()))
    if user_status:
      last_been_online = user_status.last_been_online

  if last_been_online is None or (datetime.datetime.now() - last_been_online).seconds >= config.STATUS_UPDATE_THRESHOLD:
    status = models.UserStatus(key_name = str(user.key().id()))
    status.put()
    memcache.set("last_been_online_%d" % user.key().id(), datetime.datetime.now(), time = config.OFFLINE_THRESHOLD)

  if last_been_online is None or (datetime.datetime.now() - last_been_online).seconds >= config.OFFLINE_THRESHOLD:
    taskqueue.add(name = "update-user-queries-rating-%d" % user.key().id(), url='/update_user_queries_rating', params={'uid': user.key().id()}, method = 'GET')

  return user

def show_error(user, error, description = ""):
    template_values = {
      "error" : error,
      "description" : description,
      "unread_html" : get_unread_count_html(user),
    }
    path = os.path.join(os.path.dirname(__file__), 'ErrorPage.html')
    return template.render(path, template_values)

def get_unread_count(user):
  unread_threshold = datetime.datetime.now() - datetime.timedelta(seconds = config.UNREAD_THRESHOLD)

  unread_count = 0
  for t in user.unread_timestamp:
    if t < unread_threshold:
      unread_count += 1

  return unread_count

def get_unread_count_html(user):
  unread_count = get_unread_count(user)

  if unread_count > 100:
    return "<b>(100+)</b>"
  elif unread_count > 0:
    return "<b>(" + str(unread_count) + ")</b>"

  return ""

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
  hsh = base64.urlsafe_b64encode(hashlib.md5(string).digest())
  return hsh.rstrip('=')

def get_query_key_name(user_id, clean_string):
  return get_hash(str(user_id) + ':' + clean_string)

def get_chat_key_name(user_id, peer_query_key_name):
  return get_hash(str(user_id) + ':' + peer_query_key_name)

def get_ref_key(inst, prop_name):
  return getattr(inst.__class__, prop_name).get_value_for_datastore(inst)

def calc_query_rating(query, user_idle_time):
  if user_idle_time < config.OFFLINE_THRESHOLD:
    rating = 6
  elif user_idle_time < config.INACTIVE_THRESHOLD:
    rating = 3
  else:
    rating = 0
  num_keywords = len(query.keyword_hashes)
  rating -= num_keywords * 0.2
  timediff = datetime.datetime.now() - query.date_time
  age = timediff.days / 30
  rating -= min(age, 2)
  return rating
