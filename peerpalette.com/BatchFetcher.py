import types
from google.appengine.ext import db
from google.appengine.api import memcache

class ResultWrapper(object):
  def __init__(self, key, fetcher):
    self._key = key
    self._fetcher = fetcher

  def get_key(self):
    return self._key

  def get_result(self):
    return self._fetcher.get_result(self._key)

  def __nonzero__(self):
    if self._fetcher.get_result(self._key):
      return True
    return False

  def __getattr__(self, attr):
    result = self._fetcher.get_result(self._key)
    if hasattr(result, attr):
      attr_value = getattr(result, attr)
      if isinstance(attr_value, types.MethodType):
        def callable(*args, **kwargs):
          return attr_value(*args, **kwargs)
        return callable
      else:
        return attr_value
    else:
      raise AttributeError

class DatastoreFetcher:
  keys = []
  models = {}
  def get(self, key):
    if type(key) == list:
      r = []
      for k in key:
        if k not in self.keys:
          self.keys.append(k)
        r.append(ResultWrapper(k, self))
      return r
    else:
      if key not in self.keys:
        self.keys.append(key)
      return ResultWrapper(key, self)

  def fetch_all(self):
    values = db.get(self.keys)
    for i in range(len(self.keys)):
      self.models[self.keys[i]] = values[i]
    self.keys = []

  def get_result(self, key):
    if key in self.keys:
      self.fetch_all()
    return self.models[key]

class MemcacheFetcher:
  keys = []
  results = {}
  def get(self, key):
    if type(key) == list:
      r = []
      for k in key:
        if k not in self.keys:
          self.keys.append(k)
        r.append(ResultWrapper(k, self))
      return r
    else:
      if key not in self.keys:
        self.keys.append(key)
      return ResultWrapper(key, self)

  def fetch_all(self):
    res = memcache.get_multi(self.keys)
    for k in self.keys:
      if k in res:
        self.results[k] = res[k]
      else:
        self.results[k] = None
    self.keys = []

  def get_result(self, key):
    if key in self.keys:
      self.fetch_all()
    return self.results[key]


