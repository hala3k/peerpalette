from google.appengine.api import memcache
from google.appengine.ext import db

import common
import models
from RequestHandler import RequestHandler

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

    recent_searches_query = db.Query(models.RecentSearch).order('-online_count')

    recent_searches = []
    for r in recent_searches_query.fetch(10):
      recent_searches.append({'query_string' : r.query_string, 'online_count' : r.online_count})

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
      context = "<click to type a public message>"

    self.template_values['context'] = context
    self.template_values['recent_searches'] = recent_searches
    self.template_values['conversations'] = conversations_value
    self.template_values['num_online_users'] = get_num_online_users()

    self.render_page('HomePage.html')

