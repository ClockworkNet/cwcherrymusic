"""This class provides the api to talk to the client.
It will then call the cherrymodel, to get the 
requested information"""

import os #shouldn't have to list any folder in the future!
import json
import cherrypy

from cherrymusic import renderjson
from cherrymusic import userdb

debug = True


class HTTPHandler(object):
    def __init__(self, config, model):
        self.model = model
        self.config = config
        self.jsonrenderer = renderjson.JSON(config)
        self.mainpage = open('res/main.html').read()
        self.loginpage = open('res/login.html').read()
        self.userdb = userdb.UserDB(config)

    def index(self, action='', value='', filter='', login=None, username=None, password=None):
        if debug:
            #reload pages everytime in debig mode
            self.mainpage = open('res/main.html').read()
            self.loginpage = open('res/login.html').read()
        if login == 'login':
            authuser, isadmin = self.userdb.auth(username,password)
            cherrypy.session['username'] = authuser
            cherrypy.session['admin'] = isadmin
            if authuser:
                print('user '+authuser+' just logged in.')
        if cherrypy.session.get('username', None):
            return self.mainpage
        else:
            return self.loginpage
    index.exposed = True

    def api(self, action='', value='', filter=''):
        return self.handle(self.jsonrenderer, action, value, filter)
    api.exposed = True
    
    def handle(self, renderer, action, value, filter):
        if action=='search':
            if not value.strip():
                return """<span style="width:100%; text-align: center; float: left;">if you're looking for nothing, you'll be getting nothing.</span>"""
            return renderer.render(self.model.search(value.strip()))
        elif action == 'getmotd':
            return self.model.motd()
        elif action == 'saveplaylist':
            pl = json.loads(value)
            return self.model.savePlaylist(pl['playlist'],pl['playlistname']);
        elif action == 'loadplaylist':
            return json.dumps(self.model.loadPlaylist(playlistname=value));
        elif action == 'showplaylists':
            return json.dumps(self.model.showPlaylists());
        elif action == 'logout':
            cherrypy.lib.sessions.expire()
        elif action == 'getuserlist':
            if cherrypy.session['admin']:
                return json.dumps(self.userdb.getUserList())
            else:
                return {'id':'-1','username':'nobody','admin':0}
        elif action == 'adduser':
            if cherrypy.session['admin']:
                new = json.loads(value)
                return self.userdb.addUser(new['username'],new['password'],new['isadmin'])
            else:
                return "You didn't think that would work, did you?"
        else:
            dirtorender = value
            dirtorenderabspath = os.path.join(self.config.config[self.config.BASEDIR],value)
            if os.path.isdir(dirtorenderabspath):
                if action=='compactlistdir':
                    return renderer.render(self.model.listdir(dirtorender,filter))
                else: #if action=='listdir':
                    return renderer.render(self.model.listdir(dirtorender))
            else:
                return 'Error rendering dir [action: "'+action+'", value: "'+value+'"]'