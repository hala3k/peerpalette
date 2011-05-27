from google.appengine.ext import webapp
from gaesessions import get_current_session
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp import template

import config
import models
import common
from BatchFetcher import DatastoreFetcher
from BatchFetcher import MemcacheFetcher

import datetime
import simplejson
import os

class RequestHandler(webapp.RequestHandler):
  def initialize(self, request, response):
    super(RequestHandler, self).initialize(request, response)
    self.now = datetime.datetime.now()
    self.datastore_fetcher = DatastoreFetcher()
    self.memcache_fetcher = MemcacheFetcher()
    self.session = get_current_session()

  def login(self, prev_update_id = None, chat_id = None, prev_chat_update_id = None):
    self.user_key = None
    self.update_id = None
    self.chat_update_id = None
    self.unread_count = 0
    self.notifications = []

    self.template_values = {}
    self.client_update = {}

    batch_status_update = {}

    if self.session.has_key("user"):
      self.user_key = self.session["user"]
    elif self.session.has_key("anon_user"):
      self.user_key = self.session["anon_user"]

    if self.user_key is None:
      user = models.User()
      user.put()
      self.session["anon_user"] = self.user_key = user.key()
      self.session.pop("user")

    refresh_unread_count = False

    last_been_online = self.memcache_fetcher.get(config.MEMCACHE_LAST_BEEN_ONLINE(self.user_key.id_or_name()))
    update_id = self.memcache_fetcher.get(config.MEMCACHE_USER_UPDATE_ID(self.user_key.id_or_name()))
    unread_count = self.memcache_fetcher.get(config.MEMCACHE_USER_UNREAD_COUNT(self.user_key.id_or_name()))

    if chat_id is not None:
      chat_update_id = self.memcache_fetcher.get(config.MEMCACHE_CHAT_UPDATE_ID(chat_id))
      open_chat = self.memcache_fetcher.get(config.MEMCACHE_USER_OPEN_CHAT(self.user_key.id_or_name(), chat_id))

    if last_been_online.get_result() is None or (self.now - last_been_online.get_result()).seconds > config.STATUS_UPDATE_THRESHOLD:
      batch_status_update[last_been_online.get_key()] = self.now

    if last_been_online.get_result() is None:
      online_user_key = db.Key.from_path('OnlineUser', self.user_key.id_or_name())
      online_user = models.OnlineUser(key = online_user_key)
      online_user.put()

    if chat_id is not None:
      if open_chat.get_result() is None or (self.now - open_chat.get_result()).seconds > config.STATUS_UPDATE_THRESHOLD:
        batch_status_update[open_chat.get_key()] = self.now
      if open_chat.get_result() is None:
        db.delete(db.Key.from_path('User', self.user_key.id_or_name(), 'UnreadChat', chat_id))
        refresh_unread_count = True

    if update_id.get_result() is None and prev_update_id != 0:
      self.update_id = 0

    if update_id.get_result() is not None and update_id.get_result() != prev_update_id:
      if prev_update_id is None or update_id.get_result() < update_id:
        start_notification_id = 1
      else:
        start_notification_id = prev_update_id + 1
      end_notification_id = int(update_id.get_result())

      notifications = [(i, self.memcache_fetcher.get(config.MEMCACHE_USER_NOTIFICATION(self.user_key.id_or_name(), i)))
        for i in range(start_notification_id, end_notification_id + 1)]

      for i,n in notifications:
        self.update_id = i
        if n.get_result() is not None:
          self.notifications.append(n.get_result())

    if unread_count.get_result() is None or len(self.notifications) or refresh_unread_count:
      self._refresh_unread_count()
    else:
      self.unread_count = unread_count.get_result()

    if chat_id is not None:
      if chat_update_id.get_result() is None:
        self.chat_update_id = 0
      elif int(chat_update_id.get_result()) != prev_chat_update_id:
        self.chat_update_id = int(chat_update_id.get_result())

    if batch_status_update:
      memcache.set_multi(batch_status_update, time = config.OFFLINE_THRESHOLD)

  def _refresh_unread_count(self):
    self.unread_count = db.Query(models.UnreadChat, keys_only = True).ancestor(self.user_key).count(config.MAX_UNREAD_CHATS + 1)
    memcache.set(config.MEMCACHE_USER_UNREAD_COUNT(self.user_key.id_or_name()), self.unread_count, time = 120)

  def _get_client_update(self):
    self.client_update['unread_count'] = self.unread_count

    try: self.client_update['new_chat_alert'] = self.new_chat_alert
    except AttributeError: pass

    if self.update_id is not None:
      self.client_update['update_id'] = self.update_id

    if self.chat_update_id is not None:
      self.client_update['chat_update_id'] = self.chat_update_id

    try: self.client_update['notifications'] = [{"username" : m['username'], "message" : m['message'], 'link' : m['link']} for m in self.notifications]
    except AttributeError: pass

  def render_page(self, template_filename):
    self._get_client_update()

    self.template_values['unread_count'] = self.unread_count
    self.template_values["username"] = models.User.get_username(self.user_key)
    self.template_values["anonymous"] = models.User.is_anonymous(self.user_key)
    self.template_values["update"] = simplejson.dumps(self.client_update)

    path = os.path.join(os.path.dirname(__file__), template_filename)
    self.response.out.write(template.render(path, self.template_values))


def cookie_encode(v):
  from urllib import quote_plus
  import pickle
  return quote_plus(pickle.dumps(v, 1))

def cookie_decode(v):
  from urllib import unquote_plus
  import pickle
  return pickle.loads(unquote_plus(str(v)))

