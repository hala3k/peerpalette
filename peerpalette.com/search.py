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

def get_keyword_hashes(clean_string, limit = config.MAX_KEYWORDS):
  keywords = string.split(clean_string)[:limit]
  return [hash(k) for k in keywords]

def clean_query_string(q):
  return remove_nonspacing_marks(q).lower()

def get_search_query(user, keyword_hashes, age_index):
  results = db.Query(models.Query)
  results.filter('age_index =', age_index)
  for k in keyword_hashes:
    results.filter('keyword_hashes =', k)

  return results

