from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache
from django.utils import simplejson
from google.appengine.api import datastore_errors

import datetime
import time

import config
import models
import common
import os
import cgi

def update_recipient_user(user_id, chat_key_name, timestamp):
    u = models.User.get_by_id(user_id)
    try:
      i = u.unread_chat.index(chat_key_name)
      u.unread_last_timestamp[i] = timestamp
    except:
      i = len(u.unread_chat)
      u.unread_chat.insert(i, chat_key_name)
      u.unread_first_timestamp.insert(i, timestamp)
      u.unread_last_timestamp.insert(i, timestamp)
    u.put()

class SendMessage(webapp.RequestHandler):
  def post(self):
    user = common.get_current_user_info()
    my_chat = models.UserChat.get_by_key_name(self.request.get("chat_key_name"))

    if not my_chat:
       self.response.headers['Content-Type'] = 'application/json'
       self.response.out.write('{"status": "error"}')
       return

    if my_chat.user.key() != user.key():
       self.response.headers['Content-Type'] = 'application/json'
       self.response.out.write('{"status": "error"}')
       return

    peer_chat_key = common.get_ref_key(my_chat, 'peer_chat')

    msg = self.request.get("msg")[:400]
    message = models.Message(to = peer_chat_key, message_string = msg)
    message.put()

    if not my_chat.last_updated:
      my_chat.last_updated = datetime.datetime.now()
      my_chat.put()

    try:
      peer_chat = my_chat.peer_chat
    except datastore_errors.Error, e:
      if e.args[0] == "ReferenceProperty failed to be resolved":
        peer_chat = None
      else:
        raise

    if not peer_chat:
      my_query_key = common.get_ref_key(my_chat, 'query')
      peer_query_key = common.get_ref_key(my_chat, 'peer_query')
      peer_key = common.get_ref_key(my_chat, 'peer')

      if my_query_key is None:
        peer_title = "random chat"
      else:
        peer_title = "in: " + my_chat.query.query_string

      peer_chat = models.UserChat(key_name = peer_chat_key.id_or_name(), user = peer_key, peer = user, peer_query = my_chat.query, my_query = peer_query_key, title = peer_title, peer_chat = my_chat, last_updated = datetime.datetime.now())
      peer_chat.excerpt = msg
      peer_chat.put()
      db.run_in_transaction(update_recipient_user, my_chat.peer.key().id(), peer_chat.key().id_or_name(), datetime.datetime.now())
    else:
      peer_chat.last_updated = datetime.datetime.now()
      peer_chat.excerpt = msg.splitlines()[0][:80]
      peer_chat.put()
      db.run_in_transaction(update_recipient_user, my_chat.peer.key().id(), peer_chat.key().id_or_name(), datetime.datetime.now())

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write('{"status": "ok"}')


class ReceiveMessages(webapp.RequestHandler):
  def get(self):
    chat_key_name = self.request.get('chat_key_name')

    timestamp = self.request.get("timestamp", None)
    if timestamp is not None:
      timestamp = common.str2datetime(timestamp)
    user = common.get_current_user_info(clear_unread = chat_key_name, timestamp = timestamp)

    cur = self.request.get("cursor")

    keys = memcache.get_multi(["user_key", "peer_key"], key_prefix = "chat_" + chat_key_name + "_")
    try:
      user_key = keys["user_key"]
      peer_key = keys["peer_key"]
    except KeyError:
      my_chat = models.UserChat.get_by_key_name(chat_key_name)
      user_key = common.get_ref_key(my_chat, 'user')
      peer_key = common.get_ref_key(my_chat, 'peer')
      memcache.set_multi({"user_key" : user_key, "peer_key" : peer_key}, key_prefix = "chat_" + chat_key_name + "_")

    if user_key != user.key():
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write('{"status": "error"}')
      return

    # peer status
    idle_time = common.get_user_idle_time(common.get_user_status(peer_key))
    status_class = common.get_status_class(idle_time)

    if user._cleared:
      chat_key = db.Key.from_path("UserChat", chat_key_name)
      new_messages_query = db.Query(models.Message).filter('to =', chat_key).order('date_time')
      new_messages_query.with_cursor(start_cursor=cur)

      new_messages = [msg.message_string for msg in new_messages_query]

      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps({
        "unread_count" : user._unread_count,
        "unread_alert" : True if len(user._new_chats) > 0 else False,
        "timestamp" : str(user._new_timestamp),
        "status": "ok",
        "messages": new_messages,
        "cursor" : str(new_messages_query.cursor()),
        "status_class" : status_class,
      }))
      return

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({
      "unread_count" : user._unread_count,
      "unread_alert" : True if len(user._new_chats) > 0 else False,
      "timestamp" : str(user._new_timestamp),
      "status": "ok",
      "status_class" : status_class,
    }))


class GetUnread(webapp.RequestHandler):
  def get(self):
    timestamp = self.request.get("timestamp", None)
    if timestamp is not None:
      timestamp = common.str2datetime(timestamp)
    user = common.get_current_user_info(timestamp = timestamp)
    
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({"status" : "ok", "timestamp" : str(user._new_timestamp), "unread_count": user._unread_count, "unread_alert": True if len(user._new_chats) > 0 else False}))

class UpdateContext(webapp.RequestHandler):
  def post(self):
    context = self.request.get("context")
    user = common.get_current_user_info()
    user.context = context
    user.put()

