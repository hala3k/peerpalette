from google.appengine.ext import db
import config
import datetime

class User(db.Model):
  join_date = db.DateTimeProperty(auto_now_add = True)
  unread_chat = db.StringListProperty(indexed = False)
  unread_timestamp = db.ListProperty(datetime.datetime, indexed = False)

class UserStatus(db.Model):
  last_been_online = db.DateTimeProperty(auto_now = True, indexed = False)

class OnlineUser(db.Model):
  pass

class Query(db.Model):
  user = db.ReferenceProperty(User)
  query_string = db.StringProperty(required = True, indexed = False)
  date_time = db.DateTimeProperty(auto_now_add = True)
  keyword_hashes = db.ListProperty(item_type = long)
  age_index = db.IntegerProperty(default = 0)

class UserChat(db.Model):
  user = db.ReferenceProperty(User)
  query = db.ReferenceProperty(Query, collection_name = "userchat_my_set")
  peer = db.ReferenceProperty(User, required = True, collection_name = "userchat_peer_set")
  peer_chat = db.SelfReferenceProperty()
  peer_query = db.ReferenceProperty(Query, collection_name = "userchat_peer_set")
  title = db.StringProperty(required = True, indexed = False)
  excerpt = db.StringProperty(indexed = False)
  date_time = db.DateTimeProperty(auto_now_add = True)
  last_updated = db.DateTimeProperty()

class Message(db.Model):
  to = db.ReferenceProperty(UserChat)
  message_string = db.TextProperty()
  date_time = db.DateTimeProperty(auto_now_add = True)

class RandomChatQueue(db.Model):
  peer = db.ReferenceProperty(User)
  timestamp = db.DateTimeProperty(auto_now_add = True, indexed = False)

