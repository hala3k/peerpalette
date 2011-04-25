from google.appengine.ext import webapp
from gaesessions import get_current_session
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp import template

import config
import models
import common
from BatchFetcher import BatchFetcher

import datetime
import simplejson
import os

class RequestHandler(webapp.RequestHandler):
  def __init__(self):
    super(RequestHandler, self).__init__()
    self.now = datetime.datetime.now()

  def init(self, chat_id = None, timestamp = None):
    if timestamp is None:
      timestamp = self.now - config.REQUEST_TIMESTAMP_PADDING
    self.template_values = {}
    self.update = {}
    self.timestamp = timestamp
    self.fetcher = BatchFetcher()
    self._get_open_chats(chat_id)
    self._get_current_user(chat_id)
    self._get_update()

  def is_unread(self, chat_id):
    if chat_id in self.user.unread and chat_id not in self.open_chats:
      try:
        if self.user.unread[chat_id]['read_timestamp'] >= self.user.unread[chat_id]['last_timestamp']:
          return False
      except KeyError:
        pass
      return True
    return False

  def render_page(self, template_filename):
    self._get_client_update()

    self.template_values['unread_count'] = self.unread_count
    self.template_values["username"] = self.user.username()
    self.template_values["anonymous"] = self.user.anonymous()
    self.template_values["update"] = simplejson.dumps(self.update)

    path = os.path.join(os.path.dirname(__file__), template_filename)
    self.response.out.write(template.render(path, self.template_values))


  def _get_current_user(self, read_chat_id = None):
    self.user = None
    self.session = get_current_session()
    user_key = None
    if self.session.has_key("user"):
      user_key = self.session["user"]
    elif self.session.has_key("anon_user"):
      user_key = self.session["anon_user"]

    if user_key is not None:
      if read_chat_id:
        self.user, self.read_timestamp = db.run_in_transaction(_get_user, user_key, read_chat_id, self.now)
      else:
        self.user = models.User.get(user_key)

    if self.user is None:
      self.user = models.User()
      self.user.put()
      self.session["anon_user"] = self.user.key()
      self.session.pop("user")

    last_been_online = memcache.get("last_been_online_%s" % self.user.key().id_or_name())

    if last_been_online is None:
      user_status = models.UserStatus.get(db.Key.from_path('UserStatus', self.user.key().id_or_name()))
      if user_status:
        last_been_online = user_status.last_been_online

    if last_been_online is None or (self.now - last_been_online).seconds >= config.STATUS_UPDATE_THRESHOLD:
      status_key = db.Key.from_path('UserStatus', self.user.key().id_or_name())
      status = models.UserStatus(key = status_key)
      status.put()
      memcache.set("last_been_online_%s" % self.user.key().id_or_name(), self.now, time = config.OFFLINE_THRESHOLD)

    if last_been_online is None or (self.now - last_been_online).seconds >= config.OFFLINE_THRESHOLD:
      online_user_key = db.Key.from_path('OnlineUser', self.user.key().id_or_name())
      online_user = models.OnlineUser(key = online_user_key)
      online_user.put()

  def _get_update(self):
    self.unread_count = 0
    self.new_timestamp = self.timestamp

    if self.user.unread:
      for chat_id, details in self.user.unread.iteritems():
        self.new_timestamp = max(self.new_timestamp, details['last_timestamp'])

        if chat_id in self.open_chats:
          continue

        if 'read_timestamp' in details and details['read_timestamp'] >= details['last_timestamp']:
          continue

        self.unread_count += 1
        if self.timestamp < details['first_timestamp']:
          self.new_chat_alert = True

        if 'messages' in details:
          background_messages = []
          for message_id, message_timestamp in details['messages']:
            if self.timestamp < message_timestamp:
              background_messages.append(self.fetcher.get(db.Key.from_path('Message', message_id)))
          if background_messages:
            self.background_messages = background_messages


  def _get_open_chats(self, chat_id = None):
    try:
      self.open_chats = cookie_decode(self.request.cookies["open_chats"])
    except:
      self.open_chats = {}

    threshold = self.now - config.OPEN_CHAT_THRESHOLD
    min_timestamp = self.now
    chat_timestamp = None

    for cid in self.open_chats.keys():
      if cid == chat_id:
        chat_timestamp = self.open_chats[cid]
      elif self.open_chats[cid] < threshold:
        del self.open_chats[cid]
      elif self.open_chats[cid] < min_timestamp:
        min_timestamp = self.open_chats[cid]

    if chat_id is None and len(self.open_chats) == 0:
      self.response.headers.add_header("Set-Cookie", "open_chats=%s; path=/" % cookie_encode(self.open_chats))
    elif chat_timestamp == None or chat_timestamp <= min_timestamp:
      self.open_chats[chat_id] = self.now
      self.response.headers.add_header("Set-Cookie", "open_chats=%s; path=/" % cookie_encode(self.open_chats))

  def _get_client_update(self):
    self.update['unread_count'] = self.unread_count

    try: self.update['new_chat_alert'] = self.new_chat_alert
    except AttributeError: pass

    try: self.update['timestamp'] = str(self.new_timestamp)
    except AttributeError: pass

    try: self.update['background_messages'] = [{"username" : models.User.get_username(common.get_ref_key(m.get_model(), 'sender').parent()), "message" : m.message_string} for m in self.background_messages]
    except AttributeError: pass


def _get_user(user_key, read_chat_id, read_timestamp):
  user = models.User.get(user_key)
  if read_chat_id is None:
    return user
  elif read_chat_id in user.unread:
    old_timestamp = None
    try:
      old_timestamp = user.unread[read_chat_id]['read_timestamp']
      if old_timestamp >= user.unread[read_chat_id]['last_timestmap']:
        return user, old_timestamp
    except KeyError:
      pass
    user.unread[read_chat_id]['read_timestamp'] = user.unread[read_chat_id]['last_timestamp']
    common.clear_old_unread_messages(user.unread)
    user.put()
    return user, old_timestamp
  return user, None

def cookie_encode(v):
  from urllib import quote_plus
  import pickle
  return quote_plus(pickle.dumps(v, 1))

def cookie_decode(v):
  from urllib import unquote_plus
  import pickle
  return pickle.loads(unquote_plus(str(v)))

