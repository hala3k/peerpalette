from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache
from django.utils import simplejson

import datetime
import time

import config
import models
import common
import os
import cgi

def update_recipient_user(user_id, chat_id, timestamp):
    u = models.User.get_by_id(user_id)
    try:
      i = u.unread_chat.index(chat_id)
      u.unread_timestamp[i] = timestamp
    except:
      i = len(u.unread_chat)
      u.unread_chat[i:] = [chat_id]
      u.unread_timestamp[i:] = [timestamp]
    u.put()

class SendMessage(webapp.RequestHandler):
  def post(self):
    user = common.get_user()
    my_chat = models.UserChat.get_by_id(long(self.request.get("cid")))

    if not my_chat:
       self.response.headers['Content-Type'] = 'application/json'
       self.response.out.write('{"status": "error"}')
       return

    if my_chat.user.key() != user.key():
       self.response.headers['Content-Type'] = 'application/json'
       self.response.out.write('{"status": "error"}')
       return

    msg = self.request.get("msg")
    message = models.Message(to = my_chat.peer_chat, message_string = msg)
    message.put()

    if not my_chat.last_updated:
      my_chat.last_updated = datetime.datetime.now()
      my_chat.put()

    my_chat.peer_chat.last_updated = datetime.datetime.now()
    my_chat.peer_chat.put()
    db.run_in_transaction(update_recipient_user, my_chat.peer.key().id(), my_chat.peer_chat.key().id(), datetime.datetime.now())

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write('{"status": "ok"}')


class ReceiveMessages(webapp.RequestHandler):
  def get(self):
    chat_id = long(self.request.get("cid"))
    user = common.get_user(chat_id)
    cur = self.request.get("cursor")

    keys = memcache.get_multi(["user_key", "peer_key"], key_prefix = "chat_" + str(chat_id) + "_")
    try:
      user_key = keys["user_key"]
      peer_key = keys["peer_key"]
    except KeyError:
      my_chat = models.UserChat.get_by_id(chat_id)
      user_key = my_chat.user.key()
      peer_key = my_chat.peer.key()
      memcache.set_multi({"user_key" : user_key, "peer_key" : peer_key}, key_prefix = "chat_" + str(chat_id) + "_")

    if user_key != user.key():
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write('{"status": "error"}')
      return

    # peer status
    idle_time = common.get_user_idle_time(common.get_user_status(peer_key))
    status_class = common.get_status_class(idle_time)
    status_text = common.get_status_text(idle_time)
    
    new_messages = []
    chat_key = db.Key.from_path("UserChat", chat_id)
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
        "status_text" : status_text\
      }))
      return

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({
      "status": "ok",\
      "unread": common.get_unread_count(user),\
      "status_class" : status_class,\
      "status_text" : status_text\
    }))


class GetUnread(webapp.RequestHandler):
  def get(self):
    user = common.get_user()

    unread_count = common.get_unread_count(user)
    
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({"status" : "ok", "unread": unread_count}))
