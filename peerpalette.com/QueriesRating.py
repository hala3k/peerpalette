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

class UpdateUserQueriesRating(webapp.RequestHandler):
  def get(self):
    uid = self.request.get('uid')
    cur = self.request.get('cursor')
    if not uid:
      return

    user_key = db.Key.from_path('User', long(uid))
    idle_time = common.get_user_idle_time(common.get_user_status(user_key))
    queries_query = db.Query(models.Query).filter('user =', user_key).order('-date_time')

    if cur:
      queries_query.with_cursor(cur)
    queries = queries_query.fetch(10)

    indexes = []
    for q in queries:
      clean_string = search.clean_query_string(q.query_string)
      keyword_hashes = search.get_keyword_hashes(clean_string)
      query_index = models.QueryIndex(key_name = str(q.key().id_or_name()), keyword_hashes = keyword_hashes, rating = common.calc_query_rating(0, len(keyword_hashes), q.date_time))
      indexes.append(query_index)

    db.put(indexes)

    if len(queries) < 10:
      index_key = db.Key.from_path('UserIndexStatus', uid)
      if idle_time < config.OFFLINE_THRESHOLD:
        index_status = models.UserIndexStatus(key_name = uid, index_status = config.STATUS_ONLINE)
        index_status.put()
      elif idle_time < config.INACTIVE_THRESHOLD:
        index_status = models.UserIndexStatus(key_name = uid, index_status = config.STATUS_OFFLINE)
        index_status.put()
      else:
        db.delete(db.Key.from_path('UserIndexStatus', uid))
    else:
      taskqueue.add(url='/update_user_queries_rating', params={'uid': uid, 'cursor' : queries_query.cursor()},  method = 'GET')

class UpdateQueriesRating(webapp.RequestHandler):
  def get(self, index_status):
    index_status = int(index_status)
    if index_status == config.STATUS_ONLINE:
      threshold = config.OFFLINE_THRESHOLD
    elif index_status == config.STATUS_OFFLINE:
      threshold = config.INACTIVE_THRESHOLD
    else:
      return
    index_status_keys = db.Query(models.UserIndexStatus, keys_only = True).filter('index_status =', index_status).fetch(1000)
    users_status = common.get_user_status([db.Key.from_path('UserStatus', long(k.name())) for k in index_status_keys])

    for user_status in users_status:
      idle_time = common.get_user_idle_time(user_status)
      if idle_time >= threshold:
        taskqueue.add(url='/update_user_queries_rating', params={'uid': user_status.key().name()}, method = 'GET')

