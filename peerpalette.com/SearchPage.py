from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import models
import common
import search
import config

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
    keyword_hashes = search.get_keyword_hashes(clean_string)
    key_name = common.get_query_key_name(user.key().id(), clean_string)
    query = models.Query(key_name = key_name, user = user, query_string = q, keyword_hashes = keyword_hashes)
    query.put()

    search_query = search.get_search_query(user, keyword_hashes)
    cur = self.request.get('cursor')
    if cur:
      search_query.with_cursor(start_cursor = cur)
      with_cursor = True
    else:
      with_cursor = False

    results_counter = 0
    results = []
    cursor = None
    more = False

    for r in search_query:
      user_key = common.get_ref_key(r, 'user')
      if user_key == user.key():
        continue

      results_counter += 1
      results.append({'query': r.query_string, 'key': r.key().id_or_name(), 'user_key': user_key})
      if results_counter >= config.ITEMS_PER_PAGE:
        cursor = search_query.cursor()
        more = True
        break
      
    user_keys = [r['user_key'] for r in results]
    users_status = common.get_user_status(user_keys)

    for i in range(len(results)):
      result = results[i]
      idle_time = common.get_user_idle_time(users_status[i])
      status_text = common.get_status_text(idle_time)
      status_class = common.get_status_class(idle_time)
      result['status_text'] = status_text
      result['status_class'] = status_class

    template_values = {
      "results" : results,
      "key" : query.key().id_or_name(),
      "query" : q,
      "unread_html" : common.get_unread_count_html(user),
      "cursor" : cursor,
      "with_cursor" : with_cursor,
    }

    path = os.path.join(os.path.dirname(__file__), 'SearchPage.html')
    self.response.out.write(template.render(path, template_values))
