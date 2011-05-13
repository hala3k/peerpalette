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

    cursor = self.request.get('cursor')

    self.init()

    clean_string = search.clean_query_string(q)
    query_hash = common.get_query_hash(clean_string)

    query_key = db.Key.from_path('Query', query_hash, parent = self.user.key())
    existing_query = self.fetcher.get(db.Key.from_path('User', self.user.key().id_or_name(), 'Query', query_hash)).get_model()

    if existing_query is not None:
      # TODO delete using transaction
      existing_index = db.Query(models.QueryIndex, keys_only = True).filter('query =', existing_query).get()
      db.delete([existing_query, existing_index])

    keyword_hashes = search.get_keyword_hashes(clean_string)
    search_hashes = keyword_hashes[:config.MAX_SEARCH_KEYWORDS]

    context = self.fetcher.get(db.Key.from_path('UserContext', self.user.key().id_or_name()))

    search_query = search.get_search_query(search_hashes)
    if cursor is not None:
      search_query.with_cursor(cursor)

    result_keys = []
    existing_chats = {}
    users_status = {}

    for k in search_query:
      q_key = common.decode_query_index_key_name(k.name())
      user_key = q_key.parent()
      if user_key != self.user.key():
        result_keys.append(q_key)
        chat_key_name = common.get_chat_key_name(self.user.key(), user_key)
        existing_chats[user_key] = self.fetcher.get(db.Key.from_path('User', self.user.key().id_or_name(), 'UserChat', chat_key_name))
        users_status[user_key] = self.fetcher.get(db.Key.from_path('UserStatus', user_key.id_or_name()))
        if len(result_keys) >= config.ITEMS_PER_PAGE:
          break

    results = self.fetcher.get(result_keys)

    result_values = []
    online_count = 1
    for r in results:
      user_key = r.parent_key()
      idle_time = common.get_user_idle_time(users_status[user_key].get_model())
      status_class = common.get_status_class(idle_time)
      if status_class == 'online':
        online_count += 1

      v = {
        'query' : r.query_string,
        'key' : r.key(),
        'username' : models.User.get_username(user_key),
        'status_class' : status_class,
        'context' : r.context,
      }

      if existing_chats[user_key].get_model() is not None:
        v['existing_chat'] = existing_chats[user_key].name
        if self.is_unread(common.get_chat_key_name(self.user.key(), user_key)):
          v['existing_chat_unread'] = True

      result_values.append(v)

    context_text = ""
    if context:
      context_text = context.context
      keyword_hashes = list(keyword_hashes + search.get_keyword_hashes(search.clean_query_string(context_text)))[:config.MAX_KEYWORDS]

    query = models.Query(key = query_key, query_string = q, context = context_text)
    index = models.QueryIndex(key_name = common.encode_query_index_key_name(query_key), query = query_key, keyword_hashes = keyword_hashes)

    recent_query = models.RecentSearch(key_name = query_key.name(), query_string = q, online_count = online_count)

    db.put([query, index, recent_query])

    self.template_values["results"] = result_values
    self.template_values["key"] = query.key()
    self.template_values["query"] = q
    if len(result_values) >= config.ITEMS_PER_PAGE:
      self.template_values["cursor"] = search_query.cursor()

    self.render_page('SearchPage.html')

