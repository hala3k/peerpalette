from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache
from django.utils import simplejson

import models
import common
from RequestHandler import RequestHandler

import os
from cgi import escape

def get_peer_userchat_key(userchat_key):
  # TODO user with key name "1" will be confused with user with key id 1
  memcache_peer_userchat_key = "user_%s_userchat_%s_peer_userchat_key" % (userchat_key.parent().id_or_name(), userchat_key.id_or_name())
  peer_userchat_key = memcache.get(memcache_peer_userchat_key)
  if not peer_userchat_key:
    userchat = models.UserChat.get(userchat_key)
    peer_userchat_key = common.get_ref_key(userchat, 'peer_userchat')
    memcache.set(memcache_peer_userchat_key, peer_userchat_key, time = 600)
  return peer_userchat_key

def update_recipient_user(peer_userchat_key, timestamp, message_id):
    r = db.get([peer_userchat_key, peer_userchat_key.parent()])
    userchat = r[0]
    user = r[1]
    chat_id = peer_userchat_key.id_or_name()
    if chat_id in user.unread:
      unread_chat = user.unread[chat_id]
      unread_chat['last_timestamp'] = timestamp
      if 'read_timestamp' in unread_chat and unread_chat['read_timestamp'] > unread_chat['first_timestamp']:
        unread_chat['first_timestamp'] = timestamp

      unread_chat['messages'].append((message_id, timestamp))
    else:
      user.unread[chat_id] = {'first_timestamp' : timestamp, 'last_timestamp' : timestamp, 'messages' : [(message_id, timestamp)]}
 
    common.clear_old_unread_messages(user.unread)
    userchat.last_updated = timestamp
    db.put(r)

class GetUpdate(RequestHandler):
  def get_update(self):
    userchat_key = db.Key(self.request.get("userchat_key", None))

    timestamp = common.str2datetime(self.request.get("timestamp"))
    chat_id = userchat_key.id_or_name()
    self.init(chat_id, timestamp)

    message = None
    if chat_id:
      if userchat_key.parent() != self.user.key():
        self.response.set_status(404)
        return
      message = self.request.get("message", None)

      chat_key = db.Key.from_path('Chat', chat_id)
      chat_timestamp = common.str2datetime(self.request.get('chat_timestamp'))

      peer_userchat_key = get_peer_userchat_key(userchat_key)
      peer_status = self.fetcher.get(db.Key.from_path('UserStatus', peer_userchat_key.parent().id_or_name()))
      if message:
        message = escape(message[:400]).replace("\n", "<br/>")
        msg = models.Message(parent = chat_key, message_string = message, sender = userchat_key)
        db.put(msg)
        db.run_in_transaction(update_recipient_user, peer_userchat_key, self.now, msg.key().id_or_name())
      if message or (chat_id in self.user.unread and self.timestamp < self.user.unread[chat_id]['last_timestamp']):
        new_messages = db.Query(models.Message).ancestor(chat_key).filter('date_time >', chat_timestamp).order('-date_time').fetch(10)
        self.update['chat_timestamp'] = str(new_messages[0].date_time)
        new_messages.reverse()

        template_values = {
          "username" : self.user.username(),
          "messages" : [{'message_string': msg.message_string, 'username': models.User.get_username(common.get_ref_key(msg, 'sender').parent())} for msg in new_messages],
        }
        path = os.path.join(os.path.dirname(__file__), '_messages.html')
        self.update['messages_html'] = template.render(path, template_values).decode('utf-8')

      peer_idle_time = common.get_user_idle_time(peer_status)
      self.update['status_class'] = common.get_status_class(peer_idle_time)

    self._get_client_update()
    return self.update

  def get(self):
    self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
    self.response.out.write(simplejson.dumps(self.get_update()))
  def post(self):
    self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
    self.response.out.write(simplejson.dumps(self.get_update()))

class UpdateContext(RequestHandler):
  def post(self):
    context = self.request.get("context").strip()
    user_key = common.get_current_user_key()
    common.set_user_context(user_key, context)
    self.response.out.write(context if context else "<click to add a personal message>")

