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
    convs = db.Query(models.UserChat).filter('user =', user).order('-last_updated').fetch(config.ITEMS_PER_PAGE);
    
    conversations = []

    peer_keys = [conv.peer.key() for conv in convs]
    peers = dict(zip(peer_keys, db.get(peer_keys)))

    for conv in convs:
      if not conv.last_updated:
        continue

      status = common.get_user_status(peers[conv.peer.key()])
      status_class = common.get_status_class(status)

      try:
        i = user.unread_chat.index(conv.key())
        conversations.append({"title" : conv.title, "id" : conv.key().id(), "read" : False, "status_class" : status_class})
      except:
        conversations.append({"title" : conv.title, "id" : conv.key().id(), "read" : True, "status_class" : status_class})

    template_values = {
      "conversations" : conversations,
      "unread_html" : common.get_unread_count_html(user),
    }
    path = os.path.join(os.path.dirname(__file__), 'InboxPage.html')
    self.response.out.write(template.render(path, template_values))
