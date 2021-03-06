import webapp2
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache

import models
import common
import config

import datetime

class CleanupOnlineUsers(webapp2.RequestHandler):
  def get(self):
    online_users = models.OnlineUser.all(keys_only = True).fetch(1000)
    users_status = memcache.get_multi([config.MEMCACHE_LAST_BEEN_ONLINE(u.id_or_name()) for u in online_users]).keys()

    todel = []
    for u in online_users:
      if config.MEMCACHE_LAST_BEEN_ONLINE(u.id_or_name()) not in users_status:
        todel.append(u)

    db.delete(todel)

