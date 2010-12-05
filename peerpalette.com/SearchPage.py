from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import models
import common
import os
import cgi

import datetime

def doSearch(q, user):
  return db.Query(models.Query).filter('query_string =', q).order('-date_time')


class SearchPage(webapp.RequestHandler):
  def get(self):
    user = common.get_user()
    q = self.request.get('q').lower()

    if not q:
      self.redirect("/")
      return

    if q == "prplt.com":
      user.beta = q
      user.put()

    if user.beta == None:
      self.response.out.write(common.show_error(user, "Sorry. The service is in private beta testing. Please check back later or enter your invitation code in the search box if you have one."))
      return
   
    results = doSearch(q, user)

    result_values = []
    for result in results:
      if result.user.key() == user.key():
        continue

      user_status = common.get_user_status(result.user)
      status_text = common.get_status_text(user_status)
      status_class = common.get_status_class(user_status)

      result_values.append({"query" : result.query_string, "key" : result.key(), "status_text" : status_text, "status_class" : status_class})

    query = db.Query(models.Query).filter('user =', user).filter('query_string =', q).get()
    if not query:
      query = models.Query(user = user, query_string = q)

    query.date_time = datetime.datetime.now()
    query.put()

    template_values = {
      "results" : result_values,
      "key" : query.key(),
      "query" : q,
      "unread_html" : common.get_unread_count_html(user),
    }

    path = os.path.join(os.path.dirname(__file__), 'SearchPage.html')
    self.response.out.write(template.render(path, template_values))
