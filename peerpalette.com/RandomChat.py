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

  if q:
    db.delete(q)

  chat_key_name = common.get_random_chat_key_name(user.key().id(), peer_key.id())
  peer_chat_key_name = common.get_random_chat_key_name(peer_key.id(), user.key().id())

  my_title = "random chat"

  my_chat = models.UserChat(key_name = chat_key_name, user = user, peer = peer_key, peer_query = None, query = None, title = my_title, peer_chat = db.Key.from_path('UserChat', peer_chat_key_name))
  my_chat.put()
  return chat_key_name

class RandomChat(webapp.RequestHandler):
  def get(self):
    user = common.get_user()
    chat_key_name = random_chat(user)
    if chat_key_name:
      self.redirect('/chat/%s' % chat_key_name)
      return
    time.sleep(1)
    self.redirect('/random')

  def post(self):
    user = common.get_user()
    chat_key_name = random_chat(user)
    if chat_key_name:
      self.response.set_status(201)
      self.response.out.write('/chat/%s' % chat_key_name)
      return
    self.response.set_status(204)

