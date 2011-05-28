from google.appengine.ext import db

import config
import models
from common import num_encode

import string
import datetime

def encode_if_num(s):
  if isinstance(s, (int, long)):
    return "#%d" % s
  return s

def decode_if_num(s):
  if s[0] == '#':
    return long(s[1:])
  return s

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

def get_search_query(keyword_hashes):
  results = db.Query(models.QueryIndex, keys_only = True)
  for k in keyword_hashes:
    results.filter('keyword_hashes =', k)

  return results

def encode_query_index_key_name(query_key):
  td = datetime.datetime(2040, 1, 1) - datetime.datetime.now()
  timestamp = num_encode(td.seconds + (td.days * 24 * 3600), 5)
  query_id = encode_if_num(query_key.id_or_name())
  username = encode_if_num(query_key.parent().id_or_name())
  return "%s %s %s" % (timestamp, username, query_id)

def decode_query_index_key_name(key_name):
  timestamp, username, query_id = key_name.split()
  return db.Key.from_path('User', decode_if_num(username), 'Query', decode_if_num(query_id))

