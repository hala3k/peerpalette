from google.appengine.ext import webapp
from google.appengine.ext import db

import models
import common
import config

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

