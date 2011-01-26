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
    convs_query = db.Query(models.UserChat).filter('user =', user).order('-last_updated')
    cur = self.request.get('cursor')
    if cur:
      convs_query.with_cursor(start_cursor = cur)
      with_cursor = True
    else:
      with_cursor = False
    
    conversations = []
    counter = 0
    cursor = None
    for conv in convs_query:
      if not conv.last_updated:
        continue
      counter += 1

      try:
        i = user.unread_chat.index(conv.key().id_or_name())
        conversations.append({"title" : conv.title, "key_name" : conv.key().id_or_name(), "read" : False, "peer_key" : common.get_ref_key(conv, 'peer')})
      except:
        conversations.append({"title" : conv.title, "key_name" : conv.key().id_or_name(), "read" : True, "peer_key" : common.get_ref_key(conv, 'peer')})

      if counter >= config.ITEMS_PER_PAGE:
        cursor = convs_query.cursor()
        break

    peer_keys = [c['peer_key'] for c in conversations]
    peers_status = common.get_user_status(peer_keys)

    for i in range(len(conversations)):
      conv = conversations[i]
      idle_time = common.get_user_idle_time(peers_status[i])
      status_class = common.get_status_class(idle_time)
      conv['status_class'] = status_class

    template_values = {
      "conversations" : conversations,
      "unread_html" : common.get_unread_count_html(user),
      "cursor" : cursor,
      "with_cursor" : with_cursor,
    }
    path = os.path.join(os.path.dirname(__file__), 'InboxPage.html')
    self.response.out.write(template.render(path, template_values))
