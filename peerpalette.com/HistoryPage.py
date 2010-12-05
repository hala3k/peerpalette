from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import models
import common
import os
import cgi

import datetime

class HistoryPage(webapp.RequestHandler):
  def get(self):
    user = common.get_user()
    qQueries = db.Query(models.Query).filter('user =', user).order('-date_time')

    queries = []
    for query in qQueries:
      queries.append({"text" : query.query_string, "id" : query.key().id()})

    template_values = {
      "queries" : queries,
      "unread_html" : common.get_unread_count_html(user),
    }
    path = os.path.join(os.path.dirname(__file__), 'HistoryPage.html')
    self.response.out.write(template.render(path, template_values))
