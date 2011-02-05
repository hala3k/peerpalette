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

    random.seed()

    clean_string = search.clean_query_string(q)
    keyword_hashes = search.get_keyword_hashes(clean_string)
    key_name = common.get_query_key_name(user.key().id(), clean_string)
    query = models.Query(key_name = key_name, user = user, query_string = q, keyword_hashes = keyword_hashes, age_index = 0)
    query.put()

    age_index = 0
    search_query = search.get_search_query(user, keyword_hashes, age_index)

    results = []
    user_keys = []
    while len(results) < 100:
      num_fetch = config.TOTAL_RESULTS - len(results)
      res = []
      while len(res) == 0:
        if age_index >= config.AGE_INDEX_STEPS - 1:
          break
        res = search_query.fetch(num_fetch + 4)
        age_index += 1
        search_query = search.get_search_query(user, keyword_hashes, age_index)

      if len(res) == 0:
        break;

      for r in res:
        user_key = common.get_ref_key(r, 'user')
        if user_key == user.key():
          continue
        user_keys.append(user_key)
        results.append(r)

    users_status = common.get_user_status(user_keys)
    for i in range(len(results)):
      st = users_status[i]
      r = results[i]
      r.idle_time = common.get_user_idle_time(st)
      r.rating = common.calc_query_rating(r.idle_time, len(r.keyword_hashes), r.date_time)
      # randomize results slightly
      r.rating += random.random() * 0.1
 
    results.sort(key=lambda r: r.rating, reverse = True)

    existing_chat_keys = [common.get_chat_key_name(str(user.key().id_or_name()), str(r.key().id_or_name())) for r in results]
    existing_chats = models.UserChat.get_by_key_name(existing_chat_keys)

    result_values = []
    for i in range(len(results[:config.ITEMS_PER_PAGE])):
      r = results[i]
      status_class = common.get_status_class(r.idle_time)
      v = {'query': r.query_string, 'key': r.key().id_or_name(), 'user_key': common.get_ref_key(r, 'user')}
      v['status_class'] = status_class
      if existing_chats[i]:
        v['existing_chat'] = existing_chats[i].key().id_or_name()
        if existing_chats[i].key().id_or_name() in user.unread_chat:
          v['existing_chat_unread'] = True
        if existing_chats[i].excerpt:
          v['excerpt'] = existing_chats[i].excerpt
      result_values.append(v)

    unread = common.get_unread(user)

    template_values = {
      "results" : result_values,
      "key" : query.key().id_or_name(),
      "query" : q,
      "unread_count" : unread[0],
      "unread_alert" : unread[1],
    }

    path = os.path.join(os.path.dirname(__file__), 'SearchPage.html')
    self.response.out.write(template.render(path, template_values))
