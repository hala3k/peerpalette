from google.appengine.ext import webapp
from google.appengine.ext import db

import models

import datetime

class CleanupTopSearches(webapp.RequestHandler):
  def get(self):
    threshold = datetime.datetime.now() - datetime.timedelta(seconds = 60)
    query = db.Query(models.TopSearch, keys_only = True).filter('time <', threshold)
    keys = query.fetch(60)
    db.delete(keys)

