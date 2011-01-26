from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import config
import models
import common
import os
import cgi

import datetime

class InboxPage(webapp.RequestHandler):
  def get(self):
    user = common.get_user()
    convs = db.Query(models.UserChat).filter('user =', user).order('-last_updated').fetch(config.ITEMS_PER_PAGE)
    
    conversations = []

    peer_keys = [conv.peer.key() for conv in convs]
    peers_status = common.get_user_status(peer_keys)

    for i in range(len(convs)):
      conv = convs[i]
      if not conv.last_updated:
        continue

      idle_time = common.get_user_idle_time(peers_status[i])
      status_class = common.get_status_class(idle_time)

      try:
        i = user.unread_chat.index(conv.key().id_or_name())
        conversations.append({"title" : conv.title, "key_name" : conv.key().id_or_name(), "read" : False, "status_class" : status_class})
      except:
        conversations.append({"title" : conv.title, "key_name" : conv.key().id_or_name(), "read" : True, "status_class" : status_class})

    template_values = {
      "conversations" : conversations,
      "unread_html" : common.get_unread_count_html(user),
    }
    path = os.path.join(os.path.dirname(__file__), 'InboxPage.html')
    self.response.out.write(template.render(path, template_values))
