from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache
from django.utils import simplejson
from google.appengine.api import datastore_errors

import datetime
import time

import config
import models
import common
import os
import cgi

def random_chat(user):
  def hookup(user, queue_key):
    q = db.get(queue_key)
    timediff = datetime.datetime.now() - q.timestamp
    if q is not None:
      if q.timestamp < (datetime.datetime.now() - datetime.timedelta(seconds = config.RANDOM_CHAT_WAIT)):
        db.delete(q)
        return False
      if common.get_ref_key(q, 'peer') is None:
        q.peer = user
        q.put()
        return True
    return False

  peer_key = None
  q = models.RandomChatQueue.get_by_key_name(str(user.key().id()))
  if q:
    peer_key = common.get_ref_key(q, 'peer')
  else:
    peers = db.Query(models.RandomChatQueue, keys_only = True).filter('peer =', None)
    for p in peers:
      if db.run_in_transaction(hookup, user, p):
        peer_key = db.Key.from_path('User', long(p.name()))
        break
    if not peer_key:
      q = models.RandomChatQueue(key_name = str(user.key().id_or_name()))
      q.put()

  if peer_key is None:
    return None

  userchat_key_name = models.User.get_username(peer_key)
  peer_userchat_key_name = models.User.get_username(user.key())

  if q:
    db.delete(q)
    time.sleep(0.1) # wait for peer to finish creating UserChat instances
  else:
    existing_userchat = models.UserChat.get_by_key_name(userchat_key_name, parent = user)
    if existing_userchat is None:
      chat = models.Chat()
      chat.put()

      my_title = peer_title = "random"

      my_userchat_key = db.Key.from_path('User', user.key().id_or_name(), 'UserChat', userchat_key_name)
      peer_userchat_key = db.Key.from_path('User', peer_key.id_or_name(), 'UserChat', peer_userchat_key_name)

      my_userchat = models.UserChat(key_name = userchat_key_name, parent = user.key(), peer_userchat = peer_userchat_key, chat = chat.key(), title = my_title)
      peer_userchat = models.UserChat(key_name = peer_userchat_key_name, parent = peer_key, peer_userchat = my_userchat_key, chat = chat.key(), title = peer_title)

      db.put([my_userchat, peer_userchat])

  return userchat_key_name

class RandomChat(webapp.RequestHandler):
  def get(self):
    user = common.get_current_user_info()
    chat_key_name = random_chat(user)
    if chat_key_name:
      self.redirect('/chat/%s' % chat_key_name)
      return
    path = os.path.join(os.path.dirname(__file__), 'RandomChat.html')
    self.response.out.write(template.render(path, None))

  def post(self):
    user = common.get_current_user_info()
    chat_key_name = random_chat(user)
    if chat_key_name:
      self.response.set_status(201)
      self.response.out.write('/chat/%s' % chat_key_name)
      return
    self.response.set_status(204)

