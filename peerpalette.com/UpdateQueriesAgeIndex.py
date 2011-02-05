from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import taskqueue

import models
import common
import search
import config

import os
import cgi
import datetime

class UpdateQueriesAgeIndex(webapp.RequestHandler):
  def get(self, age_index):
    age_index = int(age_index)
    threshold = datetime.datetime.now() - config.AGE_INDEX_THRESHOLDS[age_index]
    queries = db.Query(models.Query).filter('age_index =', age_index).filter('date_time <', threshold).fetch(50)

    for q in queries:
      a = datetime.datetime.now() - q.date_time
      q.age_index = config.AGE_INDEX_STEPS
      for i in range(len(config.AGE_INDEX_THRESHOLDS)):
        thr = datetime.datetime.now() - config.AGE_INDEX_THRESHOLDS[i]
        if q.date_time > thr:
          q.age_index = i
          break

    db.put(queries)

