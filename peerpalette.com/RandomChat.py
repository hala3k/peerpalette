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
    if q.peer is None:
      q.peer = user
      q.put()
      return db.Key.from_path('User', long(q.key().name()))

  r = models.RandomChatQueue(key_name = str(user.key().id()))
  r.put()
  return None

class RandomChat(webapp.RequestHandler):
  def get(self):
    user = common.get_user()
    queue = db.Query(models.RandomChatQueue, keys_only = True).filter('peer =', None).fetch(10)
    peer_key = db.run_in_transaction(_random_chat, user, queue)

    tries = 0
    while peer_key is None:
      if tries > 5:
        db.delete(db.Key.from_path('RandomChatQueue', str(user.key().id_or_name())))
        break
      tries += 1
      time.sleep(1)
      q = models.RandomChatQueue.get(db.Key.from_path('RandomChatQueue', str(user.key().id_or_name())))
      peer_key = common.get_ref_key(q, 'peer')
      if peer_key:
        db.delete(q)

    if peer_key is None:
      self.redirect('/?error=random_peer_not_found')
      return

    chat_key_name = common.get_random_chat_key_name(user.key().id(), peer_key.id())
    peer_chat_key_name = common.get_random_chat_key_name(peer_key.id(), user.key().id())

    my_title = "random chat (" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + ")"

    my_chat = models.UserChat(key_name = chat_key_name, user = user, peer = peer_key, peer_query = None, query = None, title = my_title, peer_chat = db.Key.from_path('UserChat', peer_chat_key_name))
    my_chat.put()

    self.redirect('/chat/' + chat_key_name)

