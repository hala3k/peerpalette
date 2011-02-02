from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

import config
import common
import os
import random

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

    user = common.get_user()

    unread = common.get_unread(user)

    template_values = {
      "unread_count" : unread[0],
      "unread_alert" : unread[1],
      "topics" : topics,
    }

    path = os.path.join(os.path.dirname(__file__), 'HomePage.html')
    self.response.out.write(template.render(path, template_values))
