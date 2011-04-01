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

class CleanupOnlineUsers(webapp.RequestHandler):
  def get(self):
    online_users = models.OnlineUser.all(keys_only = True).fetch(5000)
    users_status = common.get_user_status([db.Key.from_path('User', o.id_or_name()) for o in online_users])

    todel = []
    for st in users_status:
      threshold = datetime.datetime.now() - datetime.timedelta(seconds = config.OFFLINE_THRESHOLD)
      if st.last_been_online < threshold:
        todel.append(db.Key.from_path('OnlineUser', st.key().id_or_name()))

    db.delete(todel)

