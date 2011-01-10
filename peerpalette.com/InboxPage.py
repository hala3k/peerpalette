from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import models
import common
import os
import cgi

import datetime

class InboxPage(webapp.RequestHandler):
  def get(self):
    user = common.get_user()
    convs = db.Query(models.UserChat).filter('user =', user).order('-last_updated')
    
    conversations = []
    for conv in convs:
      if not conv.last_updated:
        continue
      try:
        i = user.unread_chat.index(conv.key())
        conversations.append({"title" : conv.title, "id" : conv.key().id(), "read" : False})
      except:
        conversations.append({"title" : conv.title, "id" : conv.key().id(), "read" : True})

    template_values = {
      "conversations" : conversations,
      "unread_html" : common.get_unread_count_html(user),
    }
    path = os.path.join(os.path.dirname(__file__), 'InboxPage.html')
    self.response.out.write(template.render(path, template_values))
