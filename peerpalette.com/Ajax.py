from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import config
import models
import common
import os
import cgi

import datetime
import time
from threading import Thread

from django.utils import simplejson


def update_recipient_user(user_id, chat_key, timestamp):
    u = models.User.get_by_id(user_id)
    try:
      i = u.unread_chat.index(chat_key)
      u.unread_timestamp[i] = timestamp
    except:
      i = len(u.unread_chat)
      u.unread_chat[i:] = [chat_key]
      u.unread_timestamp[i:] = [timestamp]
    u.put()

class SendMessage(webapp.RequestHandler):
  def post(self):
    user = common.get_user()
    my_chat = models.UserChat.get_by_id(int(self.request.get("cid")))

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
    db.run_in_transaction(update_recipient_user, my_chat.peer.key().id(), my_chat.peer_chat.key(), datetime.datetime.now())

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write('{"status": "ok"}')


class ReceiveMessages(webapp.RequestHandler):
  def get(self):
    my_chat = models.UserChat.get_by_id(int(self.request.get("cid")))
    user = common.get_user(my_chat.key())
    timestamp = self.request.get("timestamp")

    if not my_chat:
       self.response.headers['Content-Type'] = 'application/json'
       self.response.out.write('{"status": "error"}')
       return

    if my_chat.user.key() != user.key():
       self.response.headers['Content-Type'] = 'application/json'
       self.response.out.write('{"status": "error"}')
       return

    try:
      timestamp = common.str2datetime(timestamp)
    except:
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write('{"status": "error"}')
      return

    # other info like new chats and chat status
    unread_count = common.get_unread_count(user)

    # peer status
    user_status = common.get_user_status(my_chat.peer_chat.user)
    status_class = common.get_status_class(user_status)
    status_text = common.get_status_text(user_status)
    
    new_messages = []
    new_messages_query = db.Query(models.Message).filter('to =', my_chat).filter('date_time >', timestamp).fetch(101)

    for msg in new_messages_query:
      timestamp = msg.date_time
      new_messages.append(msg.message_string)

    if len(new_messages) > 0:
      my_chat.unread = 0
      my_chat.put()
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps({"status": "ok", "messages": new_messages, "timestamp" : str(timestamp), "unread": unread_count, "status_class" : status_class, "status_text" : status_text}))
      return

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({"status": "ok", "unread": unread_count, "status_class" : status_class, "status_text" : status_text}))


class GetUnread(webapp.RequestHandler):
  def get(self):
    user = common.get_user()

    unread_count = common.get_unread_count(user)
    
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({"status" : "ok", "unread": unread_count}))
