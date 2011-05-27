from google.appengine.ext import db
import config
import datetime
import pickle

class User(db.Model):
  join_date = db.DateTimeProperty(auto_now_add = True)
  @staticmethod
  def is_anonymous(key):
    if key.id() is not None:
      return True
    return False
  def anonymous(self):
    return User.is_anonymous(self.key())
  @staticmethod
  def get_username(key):
    if key.id() is not None:
      return "anonymous%d" % key.id()
    return key.name()
  def username(self):
    return User.get_username(self.key())    

class UserContext(db.Model):
  context = db.TextProperty()

class OnlineUser(db.Model):
  # key id or name: User
  pass

class Login(db.Model):
  user = db.ReferenceProperty(User)
  username = db.StringProperty(required = True)
  password_hash = db.StringProperty(required = True)
  email = db.StringProperty()

class GoogleLogin(db.Model):
  google_user = db.UserProperty()
  user = db.ReferenceProperty(User)

class Query(db.Model):
  # parent: User
  # key_name: hash(query)
  query_string = db.StringProperty(required = True, indexed = False)
  context = db.TextProperty()
  date_time = db.DateTimeProperty(auto_now_add = True)

class QueryIndex(db.Model):
  # parent: root
  # key name: timestamp <timestamp> <User id or name> <Query id or name>
  query = db.ReferenceProperty(Query, required = True)
  keyword_hashes = db.ListProperty(item_type = long, required = True)

class Chat(db.Model):
  create_time = db.DateTimeProperty(auto_now_add = True)

class UserChat(db.Model):
  # parent: User
  # id or key_name: Chat id or key_name
  name = db.StringProperty(required = True)
  peer_userchat = db.SelfReferenceProperty()
  title = db.StringProperty(required = True, indexed = False)
  last_updated = db.DateTimeProperty()

class UnreadChat(db.Model):
  # parent: user
  # key id or name: Chat
  pass

class Message(db.Model):
# parent: Chat
  sender = db.ReferenceProperty(UserChat, indexed = False)
  message_string = db.StringProperty(indexed = False)
  date_time = db.DateTimeProperty(auto_now_add = True)

class RandomChatQueue(db.Model):
  peer = db.ReferenceProperty(User)
  timestamp = db.DateTimeProperty(auto_now_add = True, indexed = False)

class RecentSearch(db.Model):
  # key name: query_hash
  query_string = db.StringProperty(required = True, indexed = False)
  online_count = db.IntegerProperty(default = 1)
  time = db.DateTimeProperty(auto_now = True)

