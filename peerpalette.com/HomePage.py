from google.appengine.api import memcache
from google.appengine.ext import db

import config
import common
import models
from RequestHandler import RequestHandler
from utils import get_user_context
from utils import get_top_searches

def get_num_online_users():
  num = memcache.get('num_online_users')
  if num is None:
    from google.appengine.ext import db
    num = models.OnlineUser.all(keys_only = True).count(1000)
    if num > 20:
      memcache.set('num_online_users', num, 30)
  return num

class HomePage(RequestHandler):
  def get(self):
    self.login()

    conversations = [self.datastore_fetcher.get(db.Key.from_path('User', self.user_key.id_or_name(), 'UserChat', c.id_or_name()))
      for c in db.Query(models.UnreadChat, keys_only = True).ancestor(self.user_key).fetch(5)]

    peer_keys = [common.get_ref_key(c.get_result(), 'peer_userchat').parent() for c in conversations]
    peers_status = [self.memcache_fetcher.get(config.MEMCACHE_LAST_BEEN_ONLINE(pk.id_or_name())) for pk in peer_keys]

    conversations_value = []
    for i in range(len(conversations)):
      conv = conversations[i].get_result()
      status_class = "online" if peers_status[i].get_result() is not None else "offline"
      username = models.User.get_username(peer_keys[i])
      c = {'username' : username, 'title' : conv.title, 'name' : conv.name, 'status_class' : status_class}
      conversations_value.append(c)

    context = get_user_context(self.user_key)
    if context:
      self.template_values['context'] = context

    self.template_values['top_searches'] = get_top_searches()
    self.template_values['conversations'] = conversations_value
    self.template_values['num_online_users'] = get_num_online_users()

    self.render_page('HomePage.html')

