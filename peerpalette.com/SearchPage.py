from google.appengine.ext import db

import config
import models
import common
import search
from RequestHandler import RequestHandler

import random

class SearchPage(RequestHandler):
  def get(self):
    q = self.request.get('q')

    if not q:
      self.redirect("/")
      return

    self.init()

    clean_string = search.clean_query_string(q)
    keyword_hashes = search.get_keyword_hashes(clean_string)
    search_hashes = keyword_hashes[:config.MAX_SEARCH_KEYWORDS]

    context = self.fetcher.get(db.Key.from_path('UserContext', self.user.key().id_or_name()))

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
        if uk == self.user.key():
          continue
        user_keys.append(uk)
        result_keys.append(qk)

    results = self.fetcher.get(result_keys)
    users_status = self.fetcher.get([db.Key.from_path('UserStatus', u.id_or_name()) for u in user_keys])
    random.seed()
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
    existing_chats_key_names = [common.get_chat_key_name(self.user.key(), r.parent_key()) for r in results_page]
    existing_chats = self.fetcher.get([db.Key.from_path('UserChat', c, 'User', self.user.key().id_or_name()) for c in existing_chats_key_names])

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
        v['existing_chat'] = existing_chats[i].name
        if existing_chats[i].key().id_or_name() in user.unread:
          v['existing_chat_unread'] = True
      result_values.append(v)

    context_text = ""
    if context:
      context_text = context.context
      keyword_hashes = list(keyword_hashes + search.get_keyword_hashes(search.clean_query_string(context_text)))[:config.MAX_KEYWORDS]

    query_key = db.Key.from_path('Query', common.get_query_key_name(clean_string), parent = self.user.key())
    query = models.Query(key = query_key, query_string = q, context = context_text)
    index = models.QueryIndex(key_name = query_key.name(), parent = query_key, keyword_hashes = keyword_hashes)
    db.put([query, index])

    self.template_values["results"] = result_values
    self.template_values["key"] = query.key()
    self.template_values["query"] = q

    self.render_page('SearchPage.html')

