from gaesessions import get_current_session
import models
import datetime

from google.appengine.ext import db
from google.appengine.ext.webapp import template
import os

import config

import logging

import google.appengine.api.memcache

def get_online_users():
  u = memcache.get('online_users')
  if not u:
    t = datetime.datetime.now() - datetime.timedelta(seconds = OFFLINE_THRESHOLD)
    q = db.Query(models.User, keys_only = True).filter('last_been_online >', t)
    u = set(q.fetch())
    memcache.add('online_users', u, STATUS_UPDATE_THRESHOLD)

  return u

def _update_user(user_key, clear_unread = None):
  user = models.User.get(user_key)

  if clear_unread:
    try:
      i = user.unread_chat.index(clear_unread)
      del user.unread_chat[i]
      del user.unread_timestamp[i]
      user.last_been_online = datetime.datetime.now()
      user.put()
      return user
    except:
      pass

  if (datetime.datetime.now() - user.last_been_online).seconds >= config.STATUS_UPDATE_THRESHOLD:
    user.last_been_online = datetime.datetime.now()
    user.put()

  return user

def get_user(clear_unread = None):
  user = None
  session = get_current_session()

  if session.has_key("user"):
    user = db.run_in_transaction(_update_user, session["user"], clear_unread)

  if not user:
    user = models.User(last_been_online = datetime.datetime.now())
    user.put()
    session["user"] = str(user.key())

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

def get_user_status(user):
  timediff = datetime.datetime.now() - user.last_been_online
  return (timediff.seconds) + (timediff.days * 24 * 60 * 60)

def get_status_text(status):
  if status < config.OFFLINE_THRESHOLD:
    return "online"
  elif status < config.INACTIVE_THRESHOLD:
    return "offline"

  return "inactive"

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
