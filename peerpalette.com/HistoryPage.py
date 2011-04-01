from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import models
import common
import config

import os
import cgi
import datetime

class HistoryPage(webapp.RequestHandler):
  def get(self):
    user = common.get_current_user_info()
    queries_query = db.Query(models.Query).ancestor(user).order('-date_time')
    cur = self.request.get('cursor')
    if cur:
      queries_query.with_cursor(start_cursor = cur)
      with_cursor = True
    else:
      with_cursor = False

    queries = []
    counter = 0
    cursor = None
    for query in queries_query:
      queries.append({"text" : query.query_string.encode('utf-8')})
      counter += 1

      if counter >= config.ITEMS_PER_PAGE:
        cursor = queries_query.cursor()
        break

    template_values = {
      "unread_count" : user._unread_count,
      "unread_alert" : True if len(user._new_chats) > 0 else False,
      "timestamp" : user._new_timestamp,
      "username" : user.username(),
      "anonymous" : user.anonymous(),
      "queries" : queries,
      "cursor" : cursor,
      "with_cursor" : with_cursor,
    }
    path = os.path.join(os.path.dirname(__file__), 'HistoryPage.html')
    self.response.out.write(template.render(path, template_values))
