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
      u.unread_timestamp[i] = timestamp
    except:
      i = len(u.unread_chat)
      u.unread_chat[i:] = [chat_key_name]
      u.unread_timestamp[i:] = [timestamp]
    u.put()

class SendMessage(webapp.RequestHandler):
  def post(self):
    user = common.get_user()
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

    msg = self.request.get("msg")
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
        peer_title = "random chat (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + ")"
      else:
        peer_title = "in: " + my_chat.query.query_string + " (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + ")"

      peer_chat = models.UserChat(key_name = peer_chat_key.id_or_name(), user = peer_key, peer = user, peer_query = my_chat.query, my_query = peer_query_key, title = peer_title, peer_chat = my_chat, last_updated = datetime.datetime.now())
      peer_chat.put()
      db.run_in_transaction(update_recipient_user, my_chat.peer.key().id(), peer_chat.key().id_or_name(), datetime.datetime.now())
    else:
      peer_chat.last_updated = datetime.datetime.now()
      peer_chat.put()
      db.run_in_transaction(update_recipient_user, my_chat.peer.key().id(), peer_chat.key().id_or_name(), datetime.datetime.now())

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write('{"status": "ok"}')


class ReceiveMessages(webapp.RequestHandler):
  def get(self):
    chat_key_name = self.request.get('chat_key_name')
    user = common.get_user(chat_key_name)
    cur = self.request.get("cursor")

    keys = memcache.get_multi(["user_key", "peer_key"], key_prefix = "chat_" + chat_key_name + "_")
    try:
      user_key = keys["user_key"]
      peer_key = keys["peer_key"]
    except KeyError:
      my_chat = models.UserChat.get_by_key_name(chat_key_name)
      user_key = my_chat.user.key()
      peer_key = my_chat.peer.key()
      memcache.set_multi({"user_key" : user_key, "peer_key" : peer_key}, key_prefix = "chat_" + chat_key_name + "_")

    if user_key != user.key():
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write('{"status": "error"}')
      return

    # peer status
    idle_time = common.get_user_idle_time(common.get_user_status(peer_key))
    status_class = common.get_status_class(idle_time)
    
    new_messages = []
    chat_key = db.Key.from_path("UserChat", chat_key_name)
    new_messages_query = db.Query(models.Message).filter('to =', chat_key).order('date_time')
    new_messages_query.with_cursor(start_cursor=cur)
    messages = new_messages_query.fetch(10)

    if messages:
      for msg in new_messages_query:
        new_messages.append(msg.message_string)

      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps({\
        "status": "ok", "messages": new_messages,\
        "cursor" : str(new_messages_query.cursor()),\
        "unread": common.get_unread_count(user),\
        "status_class" : status_class,\
      }))
      return

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({
      "status": "ok",\
      "unread": common.get_unread_count(user),\
      "status_class" : status_class,\
    }))


class GetUnread(webapp.RequestHandler):
  def get(self):
    user = common.get_user()

    unread_count = common.get_unread_count(user)
    
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({"status" : "ok", "unread": unread_count}))
