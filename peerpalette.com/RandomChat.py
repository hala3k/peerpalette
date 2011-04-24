from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache

import datetime
import time

import config
import models
import common
import os

def random_chat(user_key):
  def hookup(user_key, queue_key):
    now = datetime.datetime.now()
    q = db.get(queue_key)
    timediff = now - q.timestamp
    if q is not None:
      if q.timestamp < (now - datetime.timedelta(seconds = config.RANDOM_CHAT_WAIT)):
        db.delete(q)
        return False
      if common.get_ref_key(q, 'peer') is None:
        q.peer = user_key
        q.put()
        return True
    return False

  peer_key = None
  q_key = db.Key.from_path('RandomChatQueue', user_key.id_or_name())
  q = models.RandomChatQueue.get(q_key)
  if q:
    peer_key = common.get_ref_key(q, 'peer')
  else:
    peers = db.Query(models.RandomChatQueue, keys_only = True).filter('peer =', None)
    for p in peers:
      if db.run_in_transaction(hookup, user_key, p):
        peer_key = db.Key.from_path('User', p.id_or_name())
        break
    if not peer_key:
      q = models.RandomChatQueue(key = q_key)
      q.put()

  if peer_key is None:
    return None

  if q:
    db.delete(q)
    time.sleep(0.05) # wait for peer to finish creating UserChat instances

  my_userchat, peer_userchat = common.create_chat(user_key_1 = user_key, user_key_2 = peer_key, title_1 = "random", title_2 = "random")

  return my_userchat.name

class RandomChat(webapp.RequestHandler):
  def get(self):
    user_key = common.get_current_user_key()
    userchat_name = random_chat(user_key)
    if userchat_name:
      self.redirect('/chat/%s' % userchat_name)
      return
    path = os.path.join(os.path.dirname(__file__), 'RandomChat.html')
    self.response.out.write(template.render(path, None))

  def post(self):
    user_key = common.get_current_user_key()
    userchat_name = random_chat(user_key)
    if userchat_name:
      self.response.set_status(201)
      self.response.out.write('/chat/%s' % userchat_name)
      return
    self.response.set_status(204)

