from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from django.utils import simplejson

import models
import common
import os
import cgi

import datetime
import time

class StartChatPage(webapp.RequestHandler):
  def get(self):
    user = common.get_current_user_info()
    queries = models.Query.get(self.request.get_all('q')[:2])
    user_key_0 = queries[0].parent_key()
    user_key_1 = queries[1].parent_key()

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

    my_userchat, peer_userchat = common.create_chat(query_1 = my_query, query_2 = peer_query)

    self.redirect('/chat/' + my_userchat.name)


class ChatPage(webapp.RequestHandler):
  def get(self, userchat_name):
    from urllib import unquote_plus
    userchat_name = unquote_plus(userchat_name)
    userchat = db.Query(models.UserChat).ancestor(common.get_current_user_key()).filter('name =', userchat_name).get()

    if not userchat:
      self.response.set_status(404)
      return

    user = common.get_current_user_info(clear_unread = userchat.key().id_or_name())
 
    chat_key = db.Key.from_path('Chat', userchat.key().id_or_name())
    q = db.Query(models.Message).filter('chat =', chat_key).order('date_time')
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
      "userchat_key" : userchat.key(),
      "messages" : [{'message_string': msg.message_string, 'username': models.User.get_username(common.get_ref_key(msg, 'sender').parent())} for msg in messages],
    }

    path = os.path.join(os.path.dirname(__file__), 'ChatPage.html')
    self.response.out.write(template.render(path, template_values))
