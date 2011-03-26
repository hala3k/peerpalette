from google.appengine.ext import db
import config
import datetime

class User(db.Model):
  join_date = db.DateTimeProperty(auto_now_add = True)
  unread_chat = db.StringListProperty(indexed = False)
  unread_first_timestamp = db.ListProperty(datetime.datetime, indexed = False)
  unread_last_timestamp = db.ListProperty(datetime.datetime, indexed = False)
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

class UserStatus(db.Model):
  last_been_online = db.DateTimeProperty(auto_now = True, indexed = False)

class UserContext(db.Model):
  context = db.TextProperty()

class OnlineUser(db.Model):
  pass

class GoogleLogin(db.Model):
  google_user = db.UserProperty()
  user = db.ReferenceProperty(User)

class Query(db.Model):
  user = db.ReferenceProperty(User)
  query_string = db.StringProperty(required = True, indexed = False)
  context = db.TextProperty()
  date_time = db.DateTimeProperty(auto_now_add = True)
  keyword_hashes = db.ListProperty(item_type = long)
  age_index = db.IntegerProperty(default = 0)

class Chat(db.Model):
  create_time = db.DateTimeProperty(auto_now = True)

# key_name: hash(peer)
# parent: user
class UserChat(db.Model):
  peer_userchat = db.SelfReferenceProperty()
  chat = db.ReferenceProperty(Chat)
  title = db.StringProperty(required = True, indexed = False)
  excerpt = db.StringProperty(indexed = False)
  last_updated = db.DateTimeProperty()

class Message(db.Model):
  chat = db.ReferenceProperty(Chat)
  sender = db.ReferenceProperty(UserChat)
  message_string = db.TextProperty()
  date_time = db.DateTimeProperty(auto_now_add = True)

class RandomChatQueue(db.Model):
  peer = db.ReferenceProperty(User)
  timestamp = db.DateTimeProperty(auto_now_add = True, indexed = False)

