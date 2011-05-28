import config
import models

import datetime
import os
import hashlib
import base64

# Source: http://stackoverflow.com/questions/561486/how-to-convert-an-integer-to-the-shortest-url-safe-string-in-python
import string
ALPHABET = '-' + string.digits + string.ascii_uppercase + '_' + string.ascii_lowercase
ALPHABET_REVERSE = dict((c, i) for (i, c) in enumerate(ALPHABET))
BASE = len(ALPHABET)
SIGN_CHARACTER = '$'
def num_encode(n, digits = None):
  if n < 0:
    return SIGN_CHARACTER + num_encode(-n, digits)
  s = []
  while True:
    n, r = divmod(n, BASE)
    s.append(ALPHABET[r])
    if n == 0: break
  if digits is not None:
    if len(s) > digits:
      s = s[0-digits:]
    elif len(s) < digits:
      s.extend([ALPHABET[0]] * (digits-len(s)))
  return ''.join(reversed(s))
def num_decode(s):
  if s[0] == SIGN_CHARACTER:
    return -num_decode(s[1:])
  n = 0
  for c in s:
    n = n * BASE + ALPHABET_REVERSE[c]
  return n

# source: http://stackoverflow.com/questions/531157/parsing-datetime-strings-with-microseconds
def str2datetime(s):
    parts = s.split('.')
    dt = datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
    if len(parts) > 1:
      return dt.replace(microsecond=int(parts[1]))
    return dt

def get_hash(string):
  hsh = base64.urlsafe_b64encode(hashlib.md5(string.encode('utf-8')).digest())
  return hsh.rstrip('=')

def get_query_hash(clean_string):
  return get_hash(clean_string)

def xor(hash1, hash2):
  r = ''
  for i in range(len(hash1)):
    r += chr(ord(hash1[i]) ^ ord(hash2[i]))
  return r

def get_chat_key_name(user_key_1, user_key_2):
  return base64.urlsafe_b64encode(xor(hashlib.md5(str(user_key_1)).digest(), hashlib.md5(str(user_key_2)).digest()))

def get_ref_key(inst, prop_name):
  return getattr(inst.__class__, prop_name).get_value_for_datastore(inst)

def sanitize_string(string, num_characters = 400, num_lines = 4):
  return "\n".join(string[:num_characters].split("\n")[:num_lines])

def htmlize_string(string):
  from cgi import escape
  return escape(string).replace("\n", "<br/>")

