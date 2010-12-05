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


def update_recipient(user_chat, amount, last_updated):
    if user_chat.unread < 0:
      user_chat.unread = amount
    else:
      user_chat.unread += amount
    user_chat.last_updated = last_updated
    user_chat.put()


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

    db.run_in_transaction(update_recipient, my_chat.peer_chat, amount=1, last_updated = datetime.datetime.now())

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write('{"status": "ok"}')


class ReceiveMessages(webapp.RequestHandler):
  def get(self):
    user = common.get_user()
    my_chat = models.UserChat.get_by_id(int(self.request.get("cid")))
    timestamp = self.request.get("timestamp")

    if not my_chat:
       self.response.headers['Content-Type'] = 'application/json'
       self.response.out.write('{"status": "error"}')
       return

    if my_chat.user.key() != user.key():
       self.response.headers['Content-Type'] = 'application/json'
       self.response.out.write('{"status": "error"}')
       return

    timestamp = common.str2datetime(timestamp)
    if not timestamp:
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
    timestamp = self.request.get("timestamp")
    if timestamp == "":
      timestamp = datetime.datetime.now() - datetime.timedelta(seconds = config.UNREAD_THRESHOLD)
    else:
      timestamp = common.str2datetime(timestamp)

    if not timestamp:
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write('{"status": "error"}')
      return

    unread_count = common.get_unread_count(user)
    
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({"status" : "ok", "timestamp" : str(datetime.datetime.now() - datetime.timedelta(seconds = config.UNREAD_THRESHOLD)), "unread": unread_count}))
