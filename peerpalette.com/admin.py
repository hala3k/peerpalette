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

    for q in queries:
      clean_string = search.clean_query_string(q.query_string)
      q.keyword_hashes = search.get_keyword_hashes(clean_string)

    db.put(queries)

    if len(queries) >= items_per_request:
      self.response.out.write("<a href='/admin/reindex?cur=%s'>continue</a>" % queries_query.cursor())
    else:
      self.response.out.write("done")

class UpdateUserModel(webapp.RequestHandler):
  def get(self):
    items_per_request = 50
    cur = self.request.get("cur")

    users_query = models.User.all()
    if cur:
      users_query.with_cursor(cur)

    users = users_query.fetch(items_per_request)

    toput = []
    for u in users:
      try:
        t = u.unread_timestamp
        u.unread_first_timestamp = t
        u.unread_last_timestamp = t
        toput.append(u)
        self.response.out.write(str(u.key().id_or_name()) + "<br/>")
      except Exception, e:
        self.response.out.write(str(u.key().id_or_name()) + " NOT UPDATED<br/>")
        self.response.out.write(e)
        self.response.out.write("<br/>")

    db.put(toput)
      
    if len(users) >= items_per_request:
      self.response.out.write("<a href='/admin/update_user_model?cur=%s'>continue</a>" % users.cursor())
    else:
      self.response.out.write("done")


application = webapp.WSGIApplication(
                                     [('/admin/reindex', Reindex),
                                     ('/admin/update_user_model', UpdateUserModel)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
