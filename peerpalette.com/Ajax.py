from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache
from django.utils import simplejson

import config
import models
import common
from RequestHandler import RequestHandler

import os
import time

class GetUpdate(RequestHandler):
  def get_update(self):
    update_id = self.request.get('update_id', None)
    if update_id is not None:
      update_id = int(update_id)

    chat_update_id = self.request.get('chat_update_id', None)
    if chat_update_id is not None:
      chat_update_id = int(chat_update_id)

    userchat_key = db.Key(self.request.get("userchat_key", None))

    chat_id = userchat_key.id_or_name()
    if chat_id:
      peer_id_holder = self.memcache_fetcher.get(config.MEMCACHE_PEER_ID(userchat_key.parent().id_or_name(), chat_id))
    self.login(prev_update_id = update_id, chat_id = chat_id, prev_chat_update_id = chat_update_id)

    message = None
    if chat_id:
      if userchat_key.parent() != self.user_key:
        self.response.set_status(404)
        return
      chat_key = db.Key.from_path('Chat', chat_id)
      chat_timestamp = common.str2datetime(self.request.get('chat_timestamp'))

      message = self.request.get("message", None)

      peer_id = peer_id_holder.get_result()
      if peer_id is None:
        userchat = self.datastore_fetcher.get(userchat_key)
        peer_userchat_key = common.get_ref_key(userchat.get_result(), 'peer_userchat')
        peer_id = peer_userchat_key.parent().id_or_name()
        memcache.set(peer_id_holder.get_key(), peer_id, time = 600)

      peer_status = self.memcache_fetcher.get(config.MEMCACHE_LAST_BEEN_ONLINE(peer_id))
      message_entity = None
      if message:
        message = common.htmlize_string(common.sanitize_string(message))
        message_entity = models.Message(parent = chat_key, message_string = message, sender = userchat_key)

        peer_chat_open = self.memcache_fetcher.get(config.MEMCACHE_USER_OPEN_CHAT(peer_id, chat_id))
        if peer_chat_open.get_result() is None:
          peer_unreadchat_key = db.Key.from_path('User', peer_id, 'UnreadChat', chat_id)
          peer_unreadchat = models.UnreadChat(key = peer_unreadchat_key)

          userchat_holder = self.datastore_fetcher.get(userchat_key)
          peer_userchat_holder = self.datastore_fetcher.get(db.Key.from_path('User', peer_id, 'UserChat', chat_id))
          userchat = userchat_holder.get_result()
          peer_userchat = peer_userchat_holder.get_result()
          userchat.last_updated = self.now
          peer_userchat.last_updated = self.now
          db.put([message_entity, peer_unreadchat, peer_userchat, userchat])

          peer_update_id = memcache.incr(config.MEMCACHE_USER_UPDATE_ID(peer_id), initial_value = 0)
          memcache.set(
            config.MEMCACHE_USER_NOTIFICATION(peer_id, peer_update_id),
            {
              'username' : models.User.get_username(self.user_key),
              'chat_id' : chat_id,
              'message' : message,
              'link' : '/chat/%s' % models.User.get_username(self.user_key),
              'timestamp' : message_entity.date_time,
            },
            time = config.NOTIFICATION_DURATION,
          )
        else:
          db.put(message_entity)

      if self.chat_update_id:
        new_messages = db.Query(models.Message).ancestor(chat_key).filter('date_time >', chat_timestamp).order('-date_time').fetch(10)
        self.client_update['chat_timestamp'] = str(new_messages[0].date_time)
        new_messages.reverse()

        template_values = {
          "username" : models.User.get_username(self.user_key),
          "messages" : [{'message_string': msg.message_string, 'username': models.User.get_username(common.get_ref_key(msg, 'sender').parent())} for msg in new_messages],
        }
        path = os.path.join(os.path.dirname(__file__), '_messages.html')
        self.client_update['messages_html'] = template.render(path, template_values).decode('utf-8')
      elif message_entity is not None:
        self.client_update['chat_timestamp'] = str(message_entity.date_time)
        template_values = {
          "username" : models.User.get_username(self.user_key),
          "messages" : [{'message_string': message_entity.message_string, 'username': models.User.get_username(common.get_ref_key(message_entity, 'sender').parent())}],
        }
        path = os.path.join(os.path.dirname(__file__), '_messages.html')
        self.client_update['messages_html'] = template.render(path, template_values).decode('utf-8')

      if chat_id and message_entity:
        self.chat_update_id = memcache.incr(config.MEMCACHE_CHAT_UPDATE_ID(chat_id), delta = 1, initial_value = 0)

      self.client_update['status_class'] = "offline" if peer_status.get_result() is None else "online"

    self._get_client_update()
    return self.client_update

  def get(self):
    self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
    self.response.out.write(simplejson.dumps(self.get_update()))
  def post(self):
    self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
    self.response.out.write(simplejson.dumps(self.get_update()))

class UpdateContext(RequestHandler):
  def post(self):
    from utils import set_user_context
    context = common.sanitize_string(self.request.get("context").strip())    
    user_key = self.get_current_user_key()
    set_user_context(user_key, context)
    self.response.out.write(context)

