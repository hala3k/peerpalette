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

def update_recipient_user(user_key, userchat_key_name, timestamp):
    u = models.User.get(user_key)
    try:
      i = u.unread_chat.index(userchat_key_name)
      u.unread_last_timestamp[i] = timestamp
    except:
      i = len(u.unread_chat)
      u.unread_chat.insert(i, userchat_key_name)
      u.unread_first_timestamp.insert(i, timestamp)
      u.unread_last_timestamp.insert(i, timestamp)
    u.put()

class SendMessage(webapp.RequestHandler):
  def post(self):
    user = common.get_current_user_info()
    userchat = models.UserChat.get_by_key_name(self.request.get("userchat_key_name"), parent = user)

    if not userchat:
       self.response.headers['Content-Type'] = 'application/json'
       self.response.out.write('{"status": "error"}')
       return

    chat_key = common.get_ref_key(userchat, 'chat')
    msg = self.request.get("msg")[:400]
    message = models.Message(chat = chat_key, message_string = msg, sender = userchat)

    if not userchat.last_updated:
      userchat.last_updated = datetime.datetime.now()
      userchat.put()

    peer_userchat = userchat.peer_userchat
    peer_userchat.last_updated = datetime.datetime.now()
    peer_userchat.excerpt = msg.splitlines()[0][:80]
    db.put([message, peer_userchat])

    db.run_in_transaction(update_recipient_user, peer_userchat.parent_key(), str(peer_userchat.key().id_or_name()), datetime.datetime.now())

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
    userchat_key_name = self.request.get('userchat_key_name')

    timestamp = self.request.get("timestamp", None)
    if timestamp is not None:
      timestamp = common.str2datetime(timestamp)
    user = common.get_current_user_info(clear_unread = userchat_key_name, timestamp = timestamp)

    cur = self.request.get("cursor")

    memcache_peer_key = "user_%s_userchat_%s_peer_key" % (user.key().id_or_name(), userchat_key_name)
    memcache_chat_key = "user_%s_userchat_%s_chat_key" % (user.key().id_or_name(), userchat_key_name)
    r = memcache.get_multi([memcache_peer_key, memcache_chat_key])
    try:
      peer_key = r[memcache_peer_key]
      chat_key = r[memcache_chat_key]
    except KeyError:
      userchat = models.UserChat.get_by_key_name(userchat_key_name, parent = user)
      if userchat is None:
        self.response.set_status(404)
        return
      peer_key = common.get_ref_key(userchat, 'peer_userchat').parent()
      chat_key = common.get_ref_key(userchat, 'chat')
      memcache.set_multi({memcache_peer_key:peer_key, memcache_chat_key: chat_key}, 240)

    # peer status
    idle_time = common.get_user_idle_time(common.get_user_status(peer_key))
    status_class = common.get_status_class(idle_time)

    if user._cleared:
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
    
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(simplejson.dumps({"status" : "ok", "timestamp" : str(user._new_timestamp), "unread_count": user._unread_count, "unread_alert": True if len(user._new_chats) > 0 else False}))

class UpdateContext(webapp.RequestHandler):
  def post(self):
    context = self.request.get("context").strip()
    user = common.get_current_user_info()
    user.context = context
    user.put()
    self.response.out.write(context if context else "<click to add a personal message>")

