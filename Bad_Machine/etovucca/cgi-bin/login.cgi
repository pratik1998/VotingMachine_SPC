#!/usr/bin/env python3

import subprocess
import cgi
import json
import hashlib
from http.cookies import SimpleCookie


PATH_TO_PASSWD = "./machine_passwd"
PATH_TO_SQLITE = "./sqlite3"
PATH_TO_DB = "rtbb.sqlite3"
redirectURL = "./admin.cgi"
ID_SQL = "SELECT passwd FROM AdminUser WHERE name='{}'"

def render_login(failure=False, logout=False):
    print("Content-Type: text/html")
    if logout:
        print("Set-Cookie: user=LOGGEDOUT; expires=Thu, 01 Jan 1970 00:00:00 GMT")
    print()
    print('<link rel="stylesheet" href="https://spar.isi.jhu.edu/teaching/443/main.css">')
    print('<h2 id="dlobeid-etovucca-voting-machine">DLOBEID EtovUcca Voting Machine</h2>')
    print('<h1 id="admin-interface-login">Admin Interface Login</h1><br>')
    if failure:
        print('<b>Login Failed.</b>')
    print('<form method="post">')
    print('<label for="passwd">Admin Password:</label>')
    print('<input type="password" id="passwd" name="passwd">')
    print('<input type="hidden" id="idname" name="idname" value="admin">')
    print('<input type="submit" value="Login">')
    print('</form>')
    print("<a href='./home.cgi'>Return to Homepage</a>")

form = cgi.FieldStorage()

try:
    if 'passwd' in form:
        # Please don't ever actually do this.
        h = hashlib.new('md5')  # U+1F914
        h.update(form.getvalue('passwd').encode('utf-8'))
        id = "1"

        sql = ID_SQL.format(form.getvalue('idname'))
        stored_hash = subprocess.check_output([PATH_TO_SQLITE, PATH_TO_DB, sql])
        stored_hash = stored_hash.strip()
        if bytes(h.hexdigest(), "utf8") == stored_hash:    
            # CGI Redirect: https://stackoverflow.com/a/6123179
            print('Content-Type: text/html')
            print('Location: %s' % redirectURL)
            C = SimpleCookie()
            C['user'] = h.hexdigest() # U+1F914
            print(C)
            print('')
            print('<html>')
            print('<head>')
            print('<link rel="stylesheet" href="https://spar.isi.jhu.edu/teaching/443/main.css">')
            print('<meta http-equiv="refresh" content="0;url=%s" />' % redirectURL)
            print('<title>You are going to be redirected</title>')
            print('</head>')
            print('<body>')
            print('Redirecting... <a href="%s">Click here if you are not redirected</a>' % redirectURL)
            print('</body>')
            print('</html>')
        else:
            print("test")
            raise ValueError('incorrect hash')
    elif 'logout' in form:
        render_login(logout=True)
    else:
        render_login()

except Exception:
    render_login(failure=True)
