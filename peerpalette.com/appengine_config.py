from gaesessions import SessionMiddleware
import os
from datetime import timedelta

def webapp_add_wsgi_middleware(app):
  app = SessionMiddleware(app, cookie_key='\x13p\xc5\x00\xb2\xccq\xffo\xf5\x99\xbd\x99\x19\xa9o\x8d+\xe2\xb9\x01\xbb\x9en\x0eP=\x01:\xcf\xae\xf3\x07\xd6h\x15\x1d\xe8wF\xeeZX\xb4`\x91\x92\x97s\x80.>|E\xd5\x8c\xd8\xde\xc1r&j\x1c\xff', lifetime=timedelta(100), no_datastore=True)
  return app

