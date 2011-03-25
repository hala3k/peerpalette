from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import models
import common
import os
import cgi

import datetime
import time

class StartChatPage(webapp.RequestHandler):
  def get(self):
    user = common.get_current_user_info()
    queries = models.Query.get_by_key_name(self.request.get_all('q'))
    user_key_0 = common.get_ref_key(queries[0], 'user')
    user_key_1 = common.get_ref_key(queries[1], 'user')

    if len(queries) != 2 \
      or user_key_0 == user_key_1 \
      or (user_key_0 != user.key() and user_key_1 != user.key()):
      self.response.set_status(403)
      return

    if user_key_0 == user.key():
      my_query = queries[0]
      peer_query = queries[1]
      peer_key = user_key_1
    else:
      my_query = queries[1]
      peer_query = queries[0]
      peer_key = user_key_0

    userchat_key_name = common.get_userchat_key_name(peer_query)
    peer_userchat_key_name = common.get_userchat_key_name(my_query)

    existing_userchat = models.UserChat.get_by_key_name(userchat_key_name, parent = user)
    if existing_userchat:
      self.redirect('/chat/' + userchat_key_name)
      return

    chat = models.Chat()
    chat.put()

    my_title = peer_query.query_string
    peer_title = my_query.query_string

    my_userchat_key = db.Key.from_path('User', user.key().id_or_name(), 'UserChat', userchat_key_name)
    peer_userchat_key = db.Key.from_path('User', peer_key.id_or_name(), 'UserChat', peer_userchat_key_name)

    my_userchat = models.UserChat(key_name = userchat_key_name, parent = user.key(), peer_userchat = peer_userchat_key, chat = chat.key(), title = my_title)
    peer_userchat = models.UserChat(key_name = peer_userchat_key_name, parent = peer_key, peer_userchat = my_userchat_key, chat = chat.key(), title = peer_title)

    db.put([my_userchat, peer_userchat])
    self.redirect('/chat/' + userchat_key_name)


class ChatPage(webapp.RequestHandler):
  def get(self, userchat_key_name):
    from urllib import unquote_plus
    userchat_key_name = unquote_plus(userchat_key_name)
    user = common.get_current_user_info(clear_unread = userchat_key_name)
    userchat = models.UserChat.get_by_key_name(userchat_key_name, parent = user)
 
    if not userchat:
      self.response.set_status(404)
      return

    q = db.Query(models.Message).filter('chat =', common.get_ref_key(userchat, 'chat')).order('date_time')
    messages = q.fetch(500)
    cur = q.cursor()

    # peer status
    peer_userchat_key = common.get_ref_key(userchat, 'peer_userchat')
    idle_time = common.get_user_idle_time(common.get_user_status(peer_userchat_key.parent()))
    status_class = common.get_status_class(idle_time)

    template_values = {
      "unread_count" : user._unread_count,
      "unread_alert" : True if len(user._new_chats) > 0 else False,
      "timestamp" : user._new_timestamp,
      "username" : user.username(),
      "anonymous" : user.anonymous(),
      "cursor" : cur,
      "peer_username" : models.User.get_username(peer_userchat_key.parent()),
      "title" : userchat.title,
      "status_class" : status_class,
      "userchat_key_name" : userchat_key_name,
      "messages" : [{'message_string': msg.message_string, 'username': models.User.get_username(common.get_ref_key(msg, 'sender').parent())} for msg in messages],
    }

    path = os.path.join(os.path.dirname(__file__), 'ChatPage.html')
    self.response.out.write(template.render(path, template_values))
