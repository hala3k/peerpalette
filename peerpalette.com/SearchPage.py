from google.appengine.ext import db

import config
import models
import common
import search
from RequestHandler import RequestHandler
from utils import get_top_searches

import random

class SearchPage(RequestHandler):
  def get(self):
    q = self.request.get('q').strip()

    if not q:
      self.redirect("/")
      return

    self.login()

    clean_string = search.clean_query_string(q)
    query_hash = common.get_query_hash(clean_string)

    query_key = db.Key.from_path('Query', query_hash, parent = self.user_key)
    existing_query = self.datastore_fetcher.get(query_key)

    keyword_hashes = search.get_keyword_hashes(clean_string)
    search_hashes = keyword_hashes[:config.MAX_SEARCH_KEYWORDS]

    context = self.datastore_fetcher.get(db.Key.from_path('UserContext', self.user_key.id_or_name()))

    search_query = search.get_search_query(search_hashes)
    cur = self.request.get('cursor')
    if cur is not None:
      search_query.with_cursor(cur)

    result_keys = []
    existing_chats = {}
    users_status = {}
    unread_chats = {}
    cursor = None

    res_keys = search_query.fetch(config.ITEMS_PER_PAGE)
    if len(res_keys) >= config.ITEMS_PER_PAGE:
      cursor = search_query.cursor()

    for k in res_keys:
      q_key = search.decode_query_index_key_name(k.name())
      user_key = q_key.parent()
      if user_key != self.user_key:
        result_keys.append(q_key)
        chat_id = common.get_chat_key_name(self.user_key, user_key)
        existing_chats[user_key] = self.datastore_fetcher.get(db.Key.from_path('User', self.user_key.id_or_name(), 'UserChat', chat_id))
        users_status[user_key] = self.memcache_fetcher.get(config.MEMCACHE_LAST_BEEN_ONLINE(user_key.id_or_name()))
        unread_chats[user_key] = self.datastore_fetcher.get(db.Key.from_path('User', self.user_key.id_or_name(), 'UnreadChat', chat_id))

    results = self.datastore_fetcher.get(result_keys)

    result_values = []
    online_count = 1
    for r in results:
      user_key = r.parent_key()
      status_class = "online" if users_status[user_key].get_result() is not None else "offline"
      if status_class == 'online':
        online_count += 1

      v = {
        'query' : r.query_string,
        'key' : r.key(),
        'username' : models.User.get_username(user_key),
        'status_class' : status_class,
        'context' : common.htmlize_string(r.context),
      }

      if existing_chats[user_key].get_result() is not None:
        v['existing_chat'] = existing_chats[user_key].name
        if unread_chats[user_key].get_result() is not None:
          v['existing_chat_unread'] = True

      result_values.append(v)

    if not result_values:
      self.template_values['top_searches'] = get_top_searches()

    if not cursor:
      context_text = ""
      if context:
        context_text = context.context
        keyword_hashes = list(keyword_hashes + search.get_keyword_hashes(search.clean_query_string(context_text)))[:config.MAX_KEYWORDS]
      query = existing_query.get_result()
      if query is not None:
        existing_index = db.Query(models.QueryIndex, keys_only = True).filter('query =', query).get()
        if existing_index is not None:
          db.delete(existing_index)
        query.query_string = q
        query.context = context_text
        query.date_time = self.now
      else:
        query = models.Query(key = query_key, query_string = q, context = context_text, date_time = self.now)

      index = models.QueryIndex(key_name = search.encode_query_index_key_name(query_key), query = query_key, user = self.user_key, keyword_hashes = keyword_hashes)

      top_search = models.TopSearch(key_name = query_key.name(), query_string = q, rating = float(len(search_hashes) * online_count))
      db.put([query, index, top_search])

    self.template_values["results"] = result_values
    self.template_values["key"] = query.key()
    self.template_values["query"] = q
    self.template_values["cursor"] = cursor

    self.render_page('SearchPage.html')

