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
    t = datetime.datetime.now() - datetime.timedelta(seconds = 60)
    q = db.Query(models.User, keys_only = True).filter('last_been_online >', t)
    u = set(q.fetch())
    memcache.add('online_users', u, 40)

  return u

def get_user(update_status = True):
  user = None
  session = get_current_session()
  if session.has_key("user"):
    user = models.User.get(session["user"])

  if not user:
    user = models.User(last_been_online = datetime.datetime.now())
    user.put()
    session["user"] = str(user.key())
  elif update_status and (datetime.datetime.now() - user.last_been_online).seconds >= 40:
    user.last_been_online = datetime.datetime.now()
    user.put()
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
  unreadThreshold = datetime.datetime.now() - datetime.timedelta(seconds = config.UNREAD_THRESHOLD)
  unreadQuery = db.Query(models.UserChat).filter('user =', user).filter('unread >', 0).fetch(101)
  unread_count = 0
  for unreadChat in unreadQuery:
    # exclude very recent messages that might be going to an already open chat session
    if unreadChat.last_updated <= unreadThreshold:
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
  return (timediff.seconds / 60) + (timediff.days * 24 * 60)

def get_status_text(status):
  if status < 1:
    return "online"
  elif status < 60:
    return "offline, minute(s) ago"
  elif status < 60 * 25:
    return "offline, hour(s) ago"
  elif status < 60 * 24 * 7:
    return "offline, day(s) ago"
  elif status < 60 * 24 * 30:
    return "offline, week(s) ago"

  return "offline, month(s) ago"

def get_status_class(status):
  if status < 1:
    return "online"
  elif status < 60 * 25:
    return "offline1"

  return "offline2"

# source: http://stackoverflow.com/questions/531157/parsing-datetime-strings-with-microseconds
def str2datetime(s):
    parts = s.split('.')
    dt = datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
    if len(parts) > 1:
      return dt.replace(microsecond=int(parts[1]))
    return dt
