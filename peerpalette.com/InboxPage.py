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
    user = common.get_current_user_info()
    convs_query = db.Query(models.UserChat).ancestor(user).order('-last_updated')
    cur = self.request.get('cursor')
    if cur:
      convs_query.with_cursor(start_cursor = cur)
      with_cursor = True
    else:
      with_cursor = False
    
    conversations = []
    peer_keys = []
    counter = 0
    cursor = None
    for conv in convs_query:
      if not conv.last_updated:
        continue
      counter += 1
      c = {'title' : conv.title, 'key_name' : conv.key().id_or_name()}
      peer_key = common.get_ref_key(conv, 'peer_userchat').parent()
      c['username'] = models.User.get_username(peer_key)

      try:
        i = user.unread_chat.index(conv.key().id_or_name())
        c['read'] = False
      except:
        c['read'] = True

      if conv.excerpt:
        c['excerpt'] = conv.excerpt

      conversations.append(c)
      peer_keys.append(peer_key)

      if counter >= config.ITEMS_PER_PAGE:
        cursor = convs_query.cursor()
        break

    peers_status = common.get_user_status(peer_keys)

    for i in range(len(conversations)):
      conv = conversations[i]
      idle_time = common.get_user_idle_time(peers_status[i])
      status_class = common.get_status_class(idle_time)
      conv['status_class'] = status_class

    template_values = {
      "unread_count" : user._unread_count,
      "unread_alert" : True if len(user._new_chats) > 0 else False,
      "timestamp" : user._new_timestamp,
      "username" : user.username(),
      "anonymous" : user.anonymous(),
      "conversations" : conversations,
      "cursor" : cursor,
      "with_cursor" : with_cursor,
    }
    path = os.path.join(os.path.dirname(__file__), 'InboxPage.html')
    self.response.out.write(template.render(path, template_values))
