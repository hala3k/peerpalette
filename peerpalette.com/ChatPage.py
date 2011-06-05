from google.appengine.ext.webapp import template
from google.appengine.ext import db

import config
import models
import common
from RequestHandler import RequestHandler
from utils import create_chat

from urllib import unquote_plus

class StartChatPage(RequestHandler):
  def get(self):
    user_key = self.get_current_user_key()
    queries = models.Query.get(self.request.get_all('q')[:2])
    user_key_0 = queries[0].parent_key()
    user_key_1 = queries[1].parent_key()

    if len(queries) != 2 \
      or user_key_0 == user_key_1 \
      or (user_key_0 != user_key and user_key_1 != user_key):
      self.response.set_status(403)
      return

    if user_key_0 == user_key:
      my_query = queries[0]
      peer_query = queries[1]
      peer_key = user_key_1
    else:
      my_query = queries[1]
      peer_query = queries[0]
      peer_key = user_key_0

    title_1 = peer_query.query_string
    title_2 = my_query.query_string

    my_userchat, peer_userchat = create_chat(user_key, peer_key, title_1 = title_1, title_2 = title_2)

    self.redirect('/chat/' + my_userchat.name)

class ChatPage(RequestHandler):
  def get(self, userchat_name):
    userchat_name = unquote_plus(userchat_name)
    userchat = db.Query(models.UserChat).ancestor(self.get_current_user_key()).filter('name =', userchat_name).get()

    if not userchat:
      self.response.set_status(404)
      return

    self.login(chat_id = userchat.key().id_or_name())

    chat_key = db.Key.from_path('Chat', userchat.key().id_or_name())
    messages_query = db.Query(models.Message).ancestor(chat_key).order('-date_time')
    messages = messages_query.fetch(config.CHAT_HISTORY_MESSAGE_COUNT)

    try:
      chat_timestamp = messages[0].date_time
    except IndexError:
      chat_timestamp = self.now

    messages.reverse()

    peer_key = common.get_ref_key(userchat, 'peer_userchat').parent()
    peer_status = self.memcache_fetcher.get(config.MEMCACHE_LAST_BEEN_ONLINE(peer_key.id_or_name()))

    self.template_values["peer_username"] = models.User.get_username(peer_key)
    self.template_values["peer_status_class"] = "offline" if peer_status.get_result() is None else "online"
    self.template_values["title"] = userchat.title
    self.template_values["userchat_key"] = userchat.key()
    self.template_values["messages"] = [{'message_string': msg.message_string, 'username': models.User.get_username(common.get_ref_key(msg, 'sender').parent())} for msg in messages]
    if len(messages) >= config.CHAT_HISTORY_MESSAGE_COUNT:
      self.template_values['more_cursor'] = messages_query.cursor()

    self.client_update['chat_timestamp'] = str(chat_timestamp)

    self.render_page('ChatPage.html')

class LoadMoreMessages(RequestHandler):
  def get(self):
    userchat_key = db.Key(self.request.get('userchat_key', None))
    if self.get_current_user_key() != userchat_key.parent():
      self.response.set_status(403)
      return

    cursor = self.request.get('cursor')
    chat_key = db.Key.from_path('Chat', userchat_key.id_or_name())

    messages_query = db.Query(models.Message).ancestor(chat_key).order('-date_time')
    messages_query.with_cursor(cursor)
    messages = messages_query.fetch(config.CHAT_HISTORY_MESSAGE_COUNT)
    messages.reverse()

    template_values = {'username' : models.User.get_username(userchat_key.parent())}

    if len(messages) >= config.CHAT_HISTORY_MESSAGE_COUNT:
      template_values['more_cursor'] = messages_query.cursor()

    template_values["messages"] = [{'message_string': msg.message_string, 'username': models.User.get_username(common.get_ref_key(msg, 'sender').parent())} for msg in messages]

    import os
    path = os.path.join(os.path.dirname(__file__), '_messages.html')
    self.response.out.write(template.render(path, template_values))

