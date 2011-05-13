from google.appengine.ext import webapp
from google.appengine.ext import db

import models

import datetime

class CleanupRecentSearches(webapp.RequestHandler):
  def get(self):
    threshold = datetime.datetime.now() - datetime.timedelta(seconds = 60)
    query = db.Query(models.RecentSearch, keys_only = True).filter('time <', threshold)
    keys = query.fetch(60)
    db.delete(keys)

