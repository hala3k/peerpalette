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

def compare_message_dates(message1, message2):
  return cmp(message1.date_time, message2.date_time)

class StartChatPage(webapp.RequestHandler):
  def get(self):
    user = common.get_user()
    queries = models.Query.get_by_key_name(self.request.get_all('q'))

    if len(queries) != 2 \
      or queries[0].user.key() == queries[1].user.key() \
      or (queries[0].user.key() != user.key() and queries.user.key() != user.key()):
      self.response.out.write('error')

    # TODO test if the two queries match (one is a subset of the other)

    # subject_query is the query that the user found
    if queries[0].user.key() == user.key():
      my_query = queries[0]
      peer_query = queries[1]
    else:
      my_query = queries[1]
      peer_query = queries[0]

    # TODO test if the user has an existing coversation with that query
    chat_key_name = common.get_chat_key_name(user.key().id(), peer_query.key().id_or_name())
    existing_chat = models.Query.get_by_key_name(chat_key_name)
    if existing_chat:
      self.redirect('/chat/' + chat_key_name)
      return

    peer = peer_query.user
    peer_chat_key_name = common.get_chat_key_name(peer.key().id(), my_query.key().id_or_name())

    my_title = peer_query.query_string

    my_chat = models.UserChat(key_name = chat_key_name, user = user, peer = peer, peer_query = peer_query, query = my_query, title = my_title, peer_chat = db.Key.from_path('UserChat', peer_chat_key_name))
    my_chat.put()

    self.redirect('/chat/' + chat_key_name)


class ChatPage(webapp.RequestHandler):
  def get(self, chat_key_name):
    my_chat = db.get(db.Key.from_path('UserChat', chat_key_name))
    user = common.get_user(chat_key_name)
 
    if not my_chat or my_chat.user.key() != user.key():
      self.response.out.write("error")
      return

    q = db.Query(models.Message).filter('to =', my_chat.key()).order('date_time')
    messages = q.fetch(500)
    cur = q.cursor()

    peer_chat_key = common.get_ref_key(my_chat, 'peer_chat')
    messages.extend(db.Query(models.Message).filter('to =', peer_chat_key).order('date_time').fetch(500))
    messages.sort(compare_message_dates)

    # peer status
    idle_time = common.get_user_idle_time(common.get_user_status(my_chat.peer.key()))
    status_class = common.get_status_class(idle_time)

    unread = common.get_unread(user)

    template_values = {
      "cursor" : cur,
      "title" : my_chat.title,
      "status_class" : status_class,
      "chat_key_name" : chat_key_name,
      "messages" : [{'message_string': msg.message_string, 'chat_key_name': common.get_ref_key(msg, 'to').id_or_name()} for msg in messages],
      "unread_count" : unread[0],
      "unread_alert" : unread[1],
      "link_target" : "_blank",
    }

    path = os.path.join(os.path.dirname(__file__), 'ChatPage.html')
    self.response.out.write(template.render(path, template_values))
