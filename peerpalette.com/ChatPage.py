from google.appengine.ext.webapp import template
from google.appengine.ext import db

import models
import common
from RequestHandler import RequestHandler

class StartChatPage(RequestHandler):
  def get(self):
    user_key = common.get_current_user_key()
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

    my_userchat, peer_userchat = common.create_chat(query_1 = my_query, query_2 = peer_query)

    self.redirect('/chat/' + my_userchat.name)

class ChatPage(RequestHandler):
  def get(self, userchat_name):
    from urllib import unquote_plus

    userchat_name = unquote_plus(userchat_name)
    userchat = db.Query(models.UserChat).ancestor(common.get_current_user_key()).filter('name =', userchat_name).get()

    if not userchat:
      self.response.set_status(404)
      return

    self.init(userchat.key().id_or_name())

    chat_key = db.Key.from_path('Chat', userchat.key().id_or_name())
    q = db.Query(models.Message).filter('chat =', chat_key).order('date_time')
    messages = q.fetch(500)

    peer_key = common.get_ref_key(userchat, 'peer_userchat').parent()
    peer_status = self.fetcher.get(db.Key.from_path('UserStatus', peer_key.id_or_name()))

    self.update['cursor'] = str(q.cursor())

    idle_time = common.get_user_idle_time(peer_status)

    self.template_values["peer_username"] = models.User.get_username(peer_key)
    self.template_values["peer_status_class"] = common.get_status_class(idle_time)
    self.template_values["title"] = userchat.title
    self.template_values["userchat_key"] = userchat.key()
    self.template_values["messages"] = [{'message_string': msg.message_string, 'username': models.User.get_username(common.get_ref_key(msg, 'sender').parent())} for msg in messages]

    self.render_page('ChatPage.html')

