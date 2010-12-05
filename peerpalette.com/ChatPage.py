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
    query1 = models.Query.get(self.request.get("q1"))
    query2 = models.Query.get(self.request.get("q2"))

    # TODO test if one of the queries is for the user
    if query1.user.key() != user.key() and query2.user.key() != user.key():
      self.response.out.write("error1")
      return

    # TODO test if the two queries match
    if query1.query_string != query2.query_string:
      self.response.out.write("error2")
      return

    # subject_query is the query that the user found
    if query1.user.key() == user.key():
      my_query = query1
      peer_query = query2
    else:
      my_query = query2
      peer_query = query1

    # TODO test if the user has an existing coversation with that query
    existing = db.Query(models.UserChat).filter('user =', user).filter('peer_query =', peer_query).get()
    if existing:
      self.redirect("/chat?cid=" + str(existing.key().id()))
      return

    my_title = peer_query.query_string + " (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + ")"
    peer_title = "incoming: " + my_query.query_string + " (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + ")"

    # TODO create a new chat and chat participant objects and forward to the chat page
    my_chat = models.UserChat(user = user, peer_query = peer_query, my_query = my_query, title = my_title)
    my_chat.put()
    peer_chat = models.UserChat(user = peer_query.user, peer_query = my_query, my_query = peer_query, title = peer_title, peer_chat = my_chat)
    peer_chat.put()
    my_chat.peer_chat = peer_chat
    my_chat.put()

    self.redirect("/chat?cid=" + str(my_chat.key().id()))


class ChatPage(webapp.RequestHandler):
  def get(self):
    user = common.get_user()
    chat_id = int(self.request.get('cid'))
 
    my_chat = models.UserChat.get_by_id(chat_id)
 
    if not my_chat:
      self.response.out.write("error")
      return

    if my_chat.user.key() != user.key():
      self.response.out.write("error")
      return

    my_chat.unread = 0
    my_chat.put()

    messages = db.Query(models.Message).filter('to =', my_chat.peer_chat).order('date_time').fetch(500)
    messages.extend(db.Query(models.Message).filter('to =', my_chat).order('date_time').fetch(500))
    timestamp = my_chat.last_updated

    messages.sort(compare_message_dates)

    # peer status
    peer_status = common.get_user_status(my_chat.peer_chat.user)
    status_class = common.get_status_class(peer_status)
    status_text = common.get_status_text(peer_status)

    template_values = {
      "timestamp" : timestamp,
      "title" : my_chat.title,
      "status_text" : status_text,
      "status_class" : status_class,
      "chat_id" : chat_id,
      "messages" : messages,
      "unread_html" : common.get_unread_count_html(user),
      "link_target" : "_blank",
    }

    path = os.path.join(os.path.dirname(__file__), 'ChatPage.html')
    self.response.out.write(template.render(path, template_values))
