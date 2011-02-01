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
    user = common.get_user()
    queries_query = db.Query(models.Query).filter('user =', user).order('-date_time')
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

    unread = common.get_unread(user)

    template_values = {
      "queries" : queries,
      "unread_count" : unread[0],
      "unread_alert" : unread[1],
      "cursor" : cursor,
      "with_cursor" : with_cursor,
    }
    path = os.path.join(os.path.dirname(__file__), 'HistoryPage.html')
    self.response.out.write(template.render(path, template_values))
