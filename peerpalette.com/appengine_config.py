from gaesessions import SessionMiddleware
import os

def webapp_add_wsgi_middleware(app):
  app = SessionMiddleware(app, cookie_key='\xbcjb\x8d[.R\x94\xfaT\x10\x01\x9cJIP`\x0c\x11\xb6\x19\xdao\x8f\xdb_\x7fP\x1f\x1a:\xf15O\xbd\xb1\x8e\r\x84&\xcb\xabM\x0b\xb7\xac\x88\x18\x18B|\xd6\x84\x12\xee\x14\xf3&\x8d"i\x82\x95c')
  return app

#def namespace_manager_default_namespace_for_request():
#  return os.environ['CURRENT_VERSION_ID'].split('.')[0]
