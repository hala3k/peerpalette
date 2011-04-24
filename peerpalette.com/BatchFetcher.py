import types
from google.appengine.ext import db

class BatchFetcher:
  keys = []
  models = {}
  def get(self, key):
    if type(key) == list:
      r = []
      for k in key:
        if k not in self.keys:
          self.keys.append(k)
        r.append(ModelWrapper(k, self))
      return r
    else:
      if key not in self.keys:
        self.keys.append(key)
      return ModelWrapper(key, self)

  def fetch(self):
    values = db.get(self.keys)
    for i in range(len(self.keys)):
      self.models[self.keys[i]] = values[i]
    self.keys = []

  def get_model(self, key):
    if key in self.keys:
      self.fetch()
    return self.models[key]

class ModelWrapper(object):
  def __init__(self, key, fetcher):
    self._key = key
    self._fetcher = fetcher

  def get_key(self):
    return self._key

  def get_model(self):
    return self._fetcher.get_model(self._key)

  def __nonzero__(self):
    if self._fetcher.get_model(self._key):
      return True
    return False

  def __getattr__(self, attr):
    model = self._fetcher.get_model(self._key)
    if hasattr(model, attr):
      attr_value = getattr(model, attr)
      if isinstance(attr_value, types.MethodType):
        def callable(*args, **kwargs):
          return attr_value(*args, **kwargs)
        return callable
      else:
        return attr_value
    else:
      raise AttributeError

