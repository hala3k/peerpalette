from google.appengine.ext import db
import config
import string
import models


# srouce: http://stackoverflow.com/questions/4162603/python-and-character-normalization
import unicodedata
def remove_nonspacing_marks(s):
  "Decompose the unicode string s and remove non-spacing marks."
  return ''.join(c for c in unicodedata.normalize('NFKD', s)
                 if unicodedata.category(c) != 'Mn')

def get_keyword_hashes(clean_string):
  keywords = string.split(clean_string)[:config.MAX_KEYWORDS]
  return [hash(k) for k in keywords]

def clean_query_string(q):
  return remove_nonspacing_marks(q).lower()

def get_search_query(user, keyword_hashes, step):
  results = db.Query(models.QueryIndex, keys_only = True)
  results.filter('rating =', step)
  for k in keyword_hashes:
    results.filter('keyword_hashes =', k)

  return results

