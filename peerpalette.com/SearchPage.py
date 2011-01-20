from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import models
import common
import search

import os
import cgi
import datetime

class SearchPage(webapp.RequestHandler):
  def get(self):
    user = common.get_user()
    q = self.request.get('q')

    if not q:
      self.redirect("/")
      return

    if q == "prplt.com":
      user.beta = q
      user.put()

#    if user.beta == None:
#      self.response.out.write(common.show_error(user, "Sorry. The service is in private beta testing. Please check back later or enter your invitation code in the search box if you have one."))
#      return

    clean_string = search.clean_query_string(q)
    query_hash = search.get_query_hash(clean_string)
    keyword_hashes = search.get_keyword_hashes(clean_string)

    # TODO use get_or_insert
    query = db.Query(models.Query).filter('user =', user).filter('query_hash =', query_hash).get()
    if not query:
      query = models.Query(user = user, query_string = q, query_hash = query_hash)
      query.put()
      query_index = models.QueryIndex(query = query, keyword_hashes = keyword_hashes, user = user)
      query_index.put()

    result_keys = search.do_search(user, keyword_hashes)
    results = db.get(result_keys)

    user_keys = [r.user.key() for r in results]
    users_status = common.get_user_status(user_keys)

    result_values = []
    for i in range(len(results)):
      result = results[i]
      if result.user.key() == user.key():
        continue

      idle_time = common.get_user_idle_time(users_status[i])
      status_text = common.get_status_text(idle_time)
      status_class = common.get_status_class(idle_time)

      result_values.append({"query" : result.query_string, "key" : result.key(), "status_text" : status_text, "status_class" : status_class})

    template_values = {
      "results" : result_values,
      "key" : query.key(),
      "query" : q,
      "unread_html" : common.get_unread_count_html(user),
    }

    path = os.path.join(os.path.dirname(__file__), 'SearchPage.html')
    self.response.out.write(template.render(path, template_values))
