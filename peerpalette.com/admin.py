from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

import models
import common
import search

class Reindex(webapp.RequestHandler):
  def get(self):
    items_per_request = 50
    cur = self.request.get('cur')

    queries_query = models.Query.all()
    if cur:
      queries_query.with_cursor(cur)

    queries = queries_query.fetch(items_per_request)

    toput = []
    for q in queries:
      clean_string = search.clean_query_string(q.query_string)
      q.keyword_hashes = search.get_keyword_hashes(clean_string)

    db.put(queries)

    if len(queries) >= items_per_request:
      self.response.out.write("<a href='/admin/reindex?cur=%s'>continue</a>" % queries_query.cursor())
    else:
      self.response.out.write("done")

application = webapp.WSGIApplication(
                                     [('/admin/reindex', Reindex)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
