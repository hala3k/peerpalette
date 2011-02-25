from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

import config
import common
import models

import os
import random

import datetime

def get_num_online_users():
  num = memcache.get('num_online_users')
  if num is None:
    from google.appengine.ext import db
    num = models.OnlineUser.all(keys_only = True).count()
    memcache.set('num_online_users', num, 60)
  return num

class HomePage(webapp.RequestHandler):
  def get(self):
    twitter_trends = memcache.get("twitter_trends")
    if not twitter_trends:
      from google.appengine.api import urlfetch
      from django.utils import simplejson

      result = urlfetch.fetch(url = "http://api.twitter.com/1/trends/daily.json")
      if result.status_code == 200:
        twitter_trends = set()
        time_groups = simplejson.loads(result.content)['trends']
        for tg in time_groups:
          trends = time_groups[tg]
          for t in trends:
            q = t['query'].encode('utf-8')
            if not q.startswith('#'):
              twitter_trends.add(q)
        twitter_trends = list(twitter_trends)
        memcache.set("twitter_trends", twitter_trends, time = 7200)

    random.shuffle(twitter_trends)
    topics = twitter_trends[:10]

    user = common.get_current_user_info()

    conversations = models.UserChat.get_by_key_name(user.unread_chat)
    peer_keys = [common.get_ref_key(c, 'peer') for c in conversations]
    peers_status = common.get_user_status(peer_keys)

    conversations_value = []
    for i in range(len(conversations)):
      conv = conversations[i]
      idle_time = common.get_user_idle_time(peers_status[i])
      status_class = common.get_status_class(idle_time)
      c = {'title' : conv.title, 'key_name' : conv.key().id_or_name(), 'status_class' : status_class}
      if conv.excerpt:
        c['excerpt'] = conv.excerpt
      conversations_value.append(c)

    template_values = {
      "unread_count" : user._unread_count,
      "unread_alert" : True if len(user._new_chats) > 0 else False,
      "timestamp" : user._new_timestamp,
      "topics" : topics,
      "conversations" : conversations_value,
      "num_online_users" : get_num_online_users(),
    }

    path = os.path.join(os.path.dirname(__file__), 'HomePage.html')
    self.response.out.write(template.render(path, template_values))
