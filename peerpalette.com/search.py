from google.appengine.ext import db

import string
import models

def get_keyword_hashes(clean_string):
  keywords = string.split(clean_string)
  return [hash(k) for k in keywords]

def clean_query_string(q):
  return q.lower()

def get_query_hash(clean_string):
  return hash(clean_string)

def index_query(query, keyword_hashes):
  query_index = models.QueryIndex(query = query, keyword_hashes = keyword_hashes)
  query_index.put()
  return keyword_hashes

def do_search(user, keyword_hashes):
  results = db.Query(models.Query)
  for k in keyword_hashes:
    results.filter('keyword_hashes =', k)
  results.order('rating')

  return results.fetch(100)

