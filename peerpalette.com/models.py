from google.appengine.ext import db

class User(db.Model):
  beta = db.StringProperty()
  join_date = db.DateTimeProperty(auto_now_add = True)
  last_been_online = db.DateTimeProperty()


class Query(db.Model):
  user = db.ReferenceProperty(User)
  query_string = db.StringProperty(required = True)
  date_time = db.DateTimeProperty(auto_now_add = True)


class UserChat(db.Model):
  user = db.ReferenceProperty(User)
  peer_chat = db.SelfReferenceProperty()
  peer_query = db.ReferenceProperty(Query, collection_name = "userchat_my_set")
  my_query = db.ReferenceProperty(Query, collection_name = "userchat_peer_set")
  title = db.StringProperty(required = True)
  date_time = db.DateTimeProperty(auto_now_add = True)
  last_updated = db.DateTimeProperty(auto_now_add = True)
  unread = db.IntegerProperty(default = -1)

class Message(db.Model):
  to = db.ReferenceProperty(UserChat)
  message_string = db.TextProperty()
  date_time = db.DateTimeProperty(auto_now_add = True)

