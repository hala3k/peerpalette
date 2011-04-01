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
    user = common.get_current_user_info()
    q = self.request.get('q')

    if not q:
      self.redirect("/")
      return

    random.seed()

    clean_string = search.clean_query_string(q)
    keyword_hashes = search.get_keyword_hashes(clean_string)
    search_hashes = keyword_hashes[:config.MAX_SEARCH_KEYWORDS]

    context = common.get_user_context(user.key())
    if context:
      keyword_hashes = list(keyword_hashes + search.get_keyword_hashes(search.clean_query_string(context)))[:config.MAX_KEYWORDS]

    age_index = 0
    indexes_query = search.get_search_query(search_hashes, age_index)

    result_keys = []
    user_keys = []
    while len(result_keys) < config.TOTAL_RESULTS:
      num_fetch = config.TOTAL_RESULTS - len(result_keys)
      res = []
      while len(res) == 0:
        if age_index >= config.AGE_INDEX_STEPS - 1:
          break
        res = indexes_query.fetch(num_fetch + 4)
        if len(res) < num_fetch + 4:
          age_index += 1
          indexes_query = search.get_search_query(search_hashes, age_index)

      if len(res) == 0:
        break;

      for r in res:
        qk = r.parent_key()
        uk = qk.parent()
        if uk == user.key():
          continue
        user_keys.append(uk)
        result_keys.append(qk)

    results = db.get(result_keys)
    users_status = common.get_user_status(user_keys)
    for i in range(len(results)):
      st = users_status[i]
      r = results[i]
      r.idle_time = common.get_user_idle_time(st)
      r.rating = common.calc_query_rating(r.idle_time, r.date_time)
      # randomize results slightly
      r.rating += random.random() * 0.1
 
    results.sort(key=lambda r: r.rating, reverse = True)
    # TODO store result keys in memcache

    results_page = results[:config.ITEMS_PER_PAGE]
    existing_chat_keys = [common.get_userchat_key_name(r.key()) for r in results_page]
    existing_chats = models.UserChat.get_by_key_name(existing_chat_keys, parent = user.key())

    result_values = []
    for i in range(len(results_page)):
      r = results_page[i]
      status_class = common.get_status_class(r.idle_time)
      user_key = r.parent_key()
      v = {
        'query' : r.query_string,
        'key' : r.key(),
        'user_key' : user_key,
        'username' : models.User.get_username(user_key),
        'status_class' : status_class,
        'context' : r.context,
      }

      if existing_chats[i]:
        v['existing_chat'] = existing_chats[i].key().id_or_name()
        if existing_chats[i].key().id_or_name() in user.unread_chat:
          v['existing_chat_unread'] = True
        if existing_chats[i].excerpt:
          v['excerpt'] = existing_chats[i].excerpt
      result_values.append(v)

    query_key = db.Key.from_path('Query', common.get_query_key_name(clean_string), parent = user.key())
    query = models.Query(key = query_key, query_string = q, context = context)
    index = models.QueryIndex(key_name = query_key.name(), parent = query_key, keyword_hashes = keyword_hashes)
    db.put([query, index])

    template_values = {
      "unread_count" : user._unread_count,
      "unread_alert" : True if len(user._new_chats) > 0 else False,
      "timestamp" : user._new_timestamp,
      "username" : user.username(),
      "anonymous" : user.anonymous(),
      "results" : result_values,
      "key" : query.key(),
      "query" : q,
    }

    path = os.path.join(os.path.dirname(__file__), 'SearchPage.html')
    self.response.out.write(template.render(path, template_values))
