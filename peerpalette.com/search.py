from google.appengine.ext import db
import config
import string
import models

def get_keyword_hashes(clean_string):
  keywords = string.split(clean_string)[:config.MAX_KEYWORDS]
  return [hash(k) for k in keywords]

def clean_query_string(q):
  return q.lower()

def get_search_query(user, keyword_hashes, step):
  results = db.Query(models.QueryIndex, keys_only = True)
  results.filter('rating =', step)
  for k in keyword_hashes:
    results.filter('keyword_hashes =', k)

  return results

