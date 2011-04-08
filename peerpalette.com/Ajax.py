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

def get_peer_userchat_key(userchat_key):
  # TODO user with key name "1" will be confused with user with key id 1
  memcache_peer_userchat_key = "user_%s_userchat_%s_peer_userchat_key" % (userchat_key.parent().id_or_name(), userchat_key.id_or_name())
  peer_userchat_key = memcache.get(memcache_peer_userchat_key)
  if not peer_userchat_key:
    userchat = models.UserChat.get(userchat_key)
    peer_userchat_key = common.get_ref_key(userchat, 'peer_userchat')
    memcache.set(memcache_peer_userchat_key, peer_userchat_key, time = 600)
  return peer_userchat_key

def update_recipient_user(peer_userchat_key, timestamp, excerpt):
    r = db.get([peer_userchat_key, peer_userchat_key.parent()])
    userchat = r[0]
    user = r[1]
    chat_id = peer_userchat_key.id_or_name()
    if chat_id in user.unread:
      user.unread[chat_id]['last_timestamp'] = timestamp
    else:
      user.unread[chat_id] = {'first_timestamp' : timestamp, 'last_timestamp' : timestamp}
 
    userchat.last_updated = timestamp
    userchat.excerpt = excerpt
    db.put(r)

class SendMessage(webapp.RequestHandler):
  def post(self):
    userchat_key = db.Key(self.request.get("userchat_key"))
    user = common.get_current_user_info()

    if not userchat_key or userchat_key.parent() != user.key():
      self.response.set_status(404)
      return

    chat_key = db.Key.from_path('Chat', userchat_key.id_or_name())
    msg = self.request.get("msg")[:400]
    message = models.Message(chat = chat_key, message_string = msg, sender = userchat_key)

    db.put(message)

    peer_userchat_key = get_peer_userchat_key(userchat_key)
    db.run_in_transaction(update_recipient_user, peer_userchat_key, datetime.datetime.now(), msg.splitlines()[0][:80])

    template_values = {
      "username" : user.username(),
      "messages" : [{'message_string': message.message_string, 'username': user.username()}],
    }

    path = os.path.join(os.path.dirname(__file__), '_messages.html')
    messages_html = template.render(path, template_values)

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({
      "status" : "ok",
      "messages_html" : messages_html,
    }))

class ReceiveMessages(webapp.RequestHandler):
  def get(self):
    userchat_key = db.Key(self.request.get('userchat_key'))

    timestamp = self.request.get("timestamp", None)
    if timestamp is not None:
      timestamp = common.str2datetime(timestamp)
    user = common.get_current_user_info(clear_unread = userchat_key.id_or_name(), timestamp = timestamp)
    if userchat_key.parent() != user.key():
      self.response.set_status(404)
      return;

    cur = self.request.get("cursor")

    peer_userchat_key = get_peer_userchat_key(userchat_key)
    idle_time = common.get_user_idle_time(common.get_user_status(peer_userchat_key.parent()))
    status_class = common.get_status_class(idle_time)

    if user._cleared:
      chat_key = db.Key.from_path('Chat', userchat_key.id_or_name())
      new_messages_query = db.Query(models.Message).filter('chat =', chat_key).order('date_time')
      new_messages_query.with_cursor(start_cursor=cur)

      template_values = {
        "username" : user.username(),
        "messages" : [{'message_string': msg.message_string, 'username': models.User.get_username(common.get_ref_key(msg, 'sender').parent())} for msg in new_messages_query if common.get_ref_key(msg, 'sender').parent() != user.key()],
      }

      path = os.path.join(os.path.dirname(__file__), '_messages.html')
      messages_html = template.render(path, template_values)

      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(simplejson.dumps({
        "unread_count" : user._unread_count,
        "unread_alert" : True if len(user._new_chats) > 0 else False,
        "timestamp" : str(user._new_timestamp),
        "status": "ok",
        "messages_html": messages_html,
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
    messages = []
    if user._new_chats:
      for chat_id in user._new_chats:
        chat_key = db.Key.from_path('Chat', chat_id)
        peer_userchat_key = get_peer_userchat_key(db.Key.from_path('User', user.key().id_or_name(), 'UserChat', chat_id))
        msgs_query = db.Query(models.Message).filter('chat =', chat_key).filter('date_time >=', timestamp)
        for m in msgs_query:
          msg = {"username" : models.User.get_username(peer_userchat_key.parent()), "message" : m.message_string}
          messages.append(msg)

    if user._updated_chats:
      for chat_id in user._updated_chats:
        chat_key = db.Key.from_path('Chat', chat_id)
        peer_userchat_key = get_peer_userchat_key(db.Key.from_path('User', user.key().id_or_name(), 'UserChat', chat_id))
        msgs_query = db.Query(models.Message).filter('chat =', chat_key).filter('date_time >=', timestamp)
        for m in msgs_query:
          msg = {"username" : models.User.get_username(peer_userchat_key.parent()), "message" : m.message_string}
          messages.append(msg)
    
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({
      "status" : "ok",
      "timestamp" : str(user._new_timestamp),
      "unread_count": user._unread_count,
      "unread_alert": True if len(user._new_chats) > 0 else False,
      "messages" : messages,
    }))

class UpdateContext(webapp.RequestHandler):
  def post(self):
    context = self.request.get("context").strip()
    user = common.get_current_user_info()
    if context:
      user.context = context
    else:
      user.context = None
    common.set_user_context(user.key(), context)
    self.response.out.write(context if context else "<click to add a personal message>")

