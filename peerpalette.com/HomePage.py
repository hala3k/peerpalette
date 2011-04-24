from google.appengine.api import memcache
from google.appengine.ext import db

import common
import models
from RequestHandler import RequestHandler

import random

def get_num_online_users():
  num = memcache.get('num_online_users')
  if num is None:
    from google.appengine.ext import db
    num = models.OnlineUser.all(keys_only = True).count()
    memcache.set('num_online_users', num, 60)
  return num

class HomePage(RequestHandler):
  def get(self):
    self.init()
    topics = ['Photography', 'Art', 'Music', 'Politics', 'Humor', 'Fashion', 'Writing', 'Travel', 'Food', 'Technology', 'Culture', 'Social Media', 'Books', 'Business', 'Health', 'Love', 'Religion', 'Parenting', 'Entertainment', 'Life', 'Comics']

    random.shuffle(topics)

    conversations = []
    for i in self.user.unread:
      if self.is_unread(i):
        conversations.append(self.fetcher.get(db.Key.from_path('User', self.user.key().id_or_name(), 'UserChat', i)))

    peer_keys = [common.get_ref_key(c.get_model(), 'peer_userchat').parent() for c in conversations]
    peers_status = common.get_user_status(peer_keys)

    conversations_value = []
    for i in range(len(conversations)):
      conv = conversations[i]
      idle_time = common.get_user_idle_time(peers_status[i])
      status_class = common.get_status_class(idle_time)
      username = models.User.get_username(peer_keys[i])
      c = {'username' : username, 'title' : conv.title, 'name' : conv.name, 'status_class' : status_class}
      conversations_value.append(c)

    context = common.get_user_context(self.user.key())
    if not context:
      context = "<click to add a personal message>"

    self.template_values['context'] = context
    self.template_values['topics'] = topics
    self.template_values['conversations'] = conversations_value
    self.template_values['num_online_users'] = get_num_online_users()

    self.render_page('HomePage.html')

