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
import random

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
    query = models.Query(key_name = key_name, user = user, query_string = q, num_keywords = len(keyword_hashes))
    query.put()
    query_index = models.QueryIndex(parent = user, key_name = key_name, keyword_hashes = keyword_hashes, date_time = query.date_time)
    query_index.rating = common.calc_query_rating(0, len(keyword_hashes), query.date_time)
    query_index.put()

    step = config.RATING_STEPS - 1
    cur = self.request.get('cursor')
    cursor = None
    if cur:
      cursor = cur[1:]
      step = int(cur[0:1])
      with_cursor = True
    else:
      with_cursor = False

    search_query = search.get_search_query(user, keyword_hashes, step)
    if cursor:
      search_query.with_cursor(start_cursor = cursor)

    results_counter = 0
    result_keys = []
    cursor = None

    random.seed()
    while results_counter <= config.ITEMS_PER_PAGE:
      keys = []
      for r in search_query:
        user_key = r.parent()
        if user_key == user.key():
          continue
        results_counter += 1
        keys.append(db.Key.from_path('Query', r.id_or_name()))
        if results_counter >= config.ITEMS_PER_PAGE:
          cursor = str(step) + search_query.cursor()
          break

      random.shuffle(keys)
      result_keys.extend(keys)

      if step <= 0:
        break

      step -= 1
      search_query = search.get_search_query(user, keyword_hashes, step)

    results = models.Query.get(result_keys)
    result_values = [{'query': r.query_string, 'key': r.key().id_or_name(), 'user_key': common.get_ref_key(r, 'user')} for r in results]

    existing_chat_keys = [common.get_chat_key_name(user.key().id(), r.key().id_or_name()) for r in results]
    existing_chats = models.UserChat.get_by_key_name(existing_chat_keys)

    user_keys = [r['user_key'] for r in result_values]
    users_status = common.get_user_status(user_keys)

    for i in range(len(result_values)):
      result = result_values[i]
      idle_time = common.get_user_idle_time(users_status[i])
      status_class = common.get_status_class(idle_time)
      result['status_class'] = status_class
      if existing_chats[i]:
        result['existing_chat'] = existing_chats[i].key().id_or_name()

    unread = common.get_unread(user)

    template_values = {
      "results" : result_values,
      "key" : query.key().id_or_name(),
      "query" : q,
      "unread_count" : unread[0],
      "unread_alert" : unread[1],
      "cursor" : cursor,
      "with_cursor" : with_cursor,
    }

    path = os.path.join(os.path.dirname(__file__), 'SearchPage.html')
    self.response.out.write(template.render(path, template_values))
