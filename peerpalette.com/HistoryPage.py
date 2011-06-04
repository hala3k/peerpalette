from google.appengine.ext import db

import config
import models
from RequestHandler import RequestHandler

class HistoryPage(RequestHandler):
  def get(self):
    self.login()

    queries_query = db.Query(models.Query).ancestor(self.user_key).order('-date_time')
    cur = self.request.get('cursor')
    if cur:
      queries_query.with_cursor(start_cursor = cur)
      with_cursor = True
    else:
      with_cursor = False

    queries = []
    counter = 0
    cursor = None
    for query in queries_query:
      queries.append({"text" : query.query_string.encode('utf-8')})
      counter += 1

      if counter >= config.ITEMS_PER_PAGE:
        cursor = queries_query.cursor()
        break

    self.template_values["queries"] = queries
    self.template_values["cursor"] = cursor
    self.template_values["with_cursor"] = with_cursor

    if not queries:
      from utils import get_top_searches
      self.template_values['top_searches'] = get_top_searches()

    self.render_page('HistoryPage.html')

