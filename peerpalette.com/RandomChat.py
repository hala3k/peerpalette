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

def _random_chat(user, queue_keys):
  queue = db.get(queue_keys)
  for q in queue:
    if q is not None and common.get_ref_key(q, 'peer') is None:
      q.peer = user
      q.put()
      return db.Key.from_path('User', long(q.key().name()))

  r = models.RandomChatQueue(key_name = str(user.key().id()))
  r.put()
  return None

def random_chat(user):
  queue = db.Query(models.RandomChatQueue, keys_only = True).filter('peer =', None).fetch(10)
  peer_key = db.run_in_transaction(_random_chat, user, queue)

  if peer_key is None:
    time.sleep(1)
    q = models.RandomChatQueue.get(db.Key.from_path('RandomChatQueue', str(user.key().id_or_name())))
    peer_key = common.get_ref_key(q, 'peer')
    if peer_key:
      db.delete(q)

  if peer_key is None:
    db.delete(db.Key.from_path('RandomChatQueue', str(user.key().id_or_name())))
    return None

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
    self.redirect('/random')

  def post(self):
    user = common.get_user()
    chat_key_name = random_chat(user)
    if chat_key_name:
      self.response.set_status(201)
      self.response.out.write('/chat/%s' % chat_key_name)
      return
    self.response.set_status(204)

