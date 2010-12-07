from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import models
import common
import search

import os
import cgi
import datetime

def update_user_indeces(uid):
  query = db.Query(models.Query).filter('user =', user).filter('query_hash =', query_hash).get()
  

class UpdateIndexWorker(webapp.RequestHandler):
  def get(self):
    uids = self.request.get_all('')
    for uid in uids:
      
      self.response.out.write(uid)
      self.response.out.write('<br/>')

