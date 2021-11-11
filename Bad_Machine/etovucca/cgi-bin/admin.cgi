#!/usr/bin/env python3

import cgi
import subprocess
import json
import hashlib
from os import environ
from http.cookies import SimpleCookie

PATH_TO_MACHINE = "./etovucca"
PATH_TO_SQLITE = "./sqlite3"
PATH_TO_DB = "rtbb.sqlite3"
PATH_TO_PASSWD = "./machine_passwd"
ID_SQL = 'SELECT id FROM Election WHERE deadline_day={} AND deadline_mon={} AND deadline_year={}'
PW_SQL = "UPDATE AdminUser SET passwd ='{}' WHERE id={}"
GPW_SQL = 'SELECT passwd FROM AdminUser WHERE id={}'
redirectURL = "./login.cgi"

def convert_date_to_id(date):
    # Please don't ever actually do this.
    date_positions = date.split("-")
    try:
        day_int = int(date_positions[2])
        mon_int = int(date_positions[1])
        year_int = int(date_positions[0])
        sql = ID_SQL.format(day_int, mon_int, year_int - 1900)
        election_id = int(subprocess.check_output([PATH_TO_SQLITE, PATH_TO_DB, sql]))
    except ValueError as e:
        election_id = ''
    return election_id

def render_elections(elections, status):
    elections_category = []
    elections_category.append('<ul>')
    for date in elections:
        if elections[date]['status'] == status:
            eid = convert_date_to_id(date)
            if status == 'open':
                elections_category.append('<li>Election ID {}: {} <a href="admin.cgi?action=closed&id={}">Close</a>'.format(eid, date, eid))
            elif status == 'closed':
                elections_category.append('<li>Election ID {}: {} <a href="admin.cgi?action=open&id={}">Open</a> <a href="admin.cgi?action=published&id={}">Publish</a>'.format(eid, date, eid, eid))
            else:
                elections_category.append('<li>Election ID {}: {} <a href="admin.cgi?action=deleted&id={}">Delete</a>'.format(eid, date, eid))

            elections_category.append('<ul>')
            for oid in range(0, len(elections[date]['offices'])):
                office = elections[date]['offices'][oid]
                elections_category.append('<li>Office ID {}: {}'.format(office['id'], office['name']))
                elections_category.append('<ul>')
                zips = "<li>Eligible ZIP Codes:"
                for zipC in office['zips']:
                    zips += ' {},'.format(zipC)
                if len(office['zips']) == 0:
                    zips += " (all) "
                elections_category.append(zips[:-1])
                for cid in range(0, len(office['candidates'])):
                    candidate = office['candidates'][cid]
                    if status == 'published':
                        elections_category.append('<li>Candidate ID {}: {} ({} votes)'.format(candidate['id'], candidate['name'], candidate['votes']))
                    else:
                        elections_category.append('<li>Candidate ID {}: {}'.format(candidate['id'], candidate['name']))
                elections_category.append('</ul>')
            elections_category.append('</ul>')

    elections_category.append('</ul>')
    return elections_category

def str_compare(a, b):
    if len(a) != len(b):
        return False
    result = 0
    for c1, c2 in zip(a, b):
        result |= ord(c1) ^ ord(c2)
    return result == 0

print("Content-Type: text/html") 
print("Cache-Control: no-store, must-revalidate")
print()
print('<link rel="stylesheet" href="https://spar.isi.jhu.edu/teaching/443/main.css">')
print('<h2 id="dlobeid-etovucca-voting-machine">DLOBEID EtovUcca Voting Machine</h2>')
print('<h1 id="admin">Admin Interface</h1>')
form = cgi.FieldStorage()


try:
    if 'HTTP_COOKIE' not in environ:
        raise ValueError("Unauthorized.")
    C = SimpleCookie()
    C.load(environ['HTTP_COOKIE'])
    # Please don't ever actually do this.
    id = "1";
    sql = GPW_SQL.format(id)
    stored_hash = subprocess.check_output([PATH_TO_SQLITE, PATH_TO_DB, sql])
    stored_hash = stored_hash.strip()
    #with open(PATH_TO_PASSWD) as f:
    #stored_hash = f.read(32)
    if 'user' not in C:
        raise ValueError("Unauthorized.")
    if not str_compare(stored_hash.decode("utf-8"), C['user'].value):
        raise ValueError("Unauthorized: " + C['user'].value)
    #if stored_hash.decode("utf-8") != C['user'].value:
      #	raise ValueError("Unauthorized: " + C['user'].value )

    print('<a href="login.cgi?logout=true">Logout</a><br>')
    
    if len(form) != 0:
        # print('<b>{}</b><br>'.format(form))
        if 'action' in form:
            action = cgi.escape(form.getvalue('action'))
            if action == 'open':
                subprocess.check_output([PATH_TO_MACHINE, 'open-election', form.getvalue('id')])
            if action == 'closed':
                subprocess.check_output([PATH_TO_MACHINE, 'close-election', form.getvalue('id')])
            if action == 'published':
                subprocess.check_output([PATH_TO_MACHINE, 'publish-election', form.getvalue('id')])
            if action == 'deleted':
                subprocess.check_output([PATH_TO_MACHINE, 'delete-election', form.getvalue('id')])
                print('<b>Successfully set election {} to "{}".</b>'.format(form.getvalue('id'), action))
        elif 'addElection' in form:
             subprocess.check_output('{} {} {}'.format(PATH_TO_MACHINE, 'add-election', form.getvalue('addElection')), shell=True)
             print('<b>Successfully added election {}</b>'.format(form.getvalue('addElection')))
        elif 'addOffice' in form:
            election_id = convert_date_to_id(form.getvalue('election'))
            office_name = cgi.escape(form.getvalue('addOffice'))
            subprocess.check_output([PATH_TO_MACHINE, 'add-office', str(election_id), office_name])
            print('<b>Successfully added {} to election {}</b>'.format(office_name, form.getvalue('election')))
        elif 'addCandidate' in form:
            candiate_name = cgi.escape(form.getvalue('addCandidate'))
            office_name = cgi.escape(form.getvalue('office'))
            subprocess.check_output([PATH_TO_MACHINE, 'add-candidate', office_name, candiate_name])
            print('<b>Successfully added candidate {} to office {}</b>'.format(candiate_name, office_name))
        elif 'addZip' in form:
            office_name = cgi.escape(form.getvalue('office'))
            zip = cgi.escape(form.getvalue('addZip'))
            subprocess.check_output([PATH_TO_MACHINE, 'add-zip', office_name, zip])
            print('<b>Successfully added ZIP {} to office {}</b>'.format(zip, office_name))
        elif 'newpasswd' in form:

            h = hashlib.new('md5')
            id = "1"
            h.update(form.getvalue('newpasswd').encode('utf-8'))
            nepw = h.hexdigest()
            sql = PW_SQL.format(nepw, id)
            subprocess.check_output([PATH_TO_SQLITE, PATH_TO_DB, sql])
            print('Content-Type: text/html')
            print('Location: %s' % redirectURL)
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

    json_elections = subprocess.check_output([PATH_TO_MACHINE, "get-elections"]).decode('utf-8')
    elections = json.loads(json_elections)

    open_elections = []
    closed_elections = []
    published_elections = []

    for status in ['Open', 'Closed', 'Published']:
        print('<h3>{} Elections</h3>'.format(status))
        for line in render_elections(elections, status.lower()):
            print(line)

    print('<hr>')

    print('<h3>Add Election</h3>')
    print('<form>')
    print('<label for="addElection">New Election Date:</label>')
    print('<input type="date" id="addElection" name="addElection"><br>')
    print('<input type="submit" value="Add Election">')
    print('</form>')

    print('<h3>Add Office to Election</h3>')
    print('<form>')
    print('<label for="election">Election:</label>')
    print('<select name="election" id="election">')
    for date in elections:
        print('<option value="{}">{}</option>'.format(date, date))
    print('</select><br>')
    print('<label for="addOffice">New Office Name:</label>')
    print('<input type="text" id="addOffice" name="addOffice"><br>')
    print('<input type="submit" value="Add Office">')
    print('</form>') 

    print('<h3>Add ZIP to Election for an Office</h3>')
    print('<form>')
    print('<label for="office">Office:</label>')
    print('<select name="office" id="office">')
    for date in elections:
        print('<optgroup label="{}">'.format(date))
        for oid in range(0, len(elections[date]['offices'])):
            office = elections[date]['offices'][oid]
            print('<option value="{}">{}</option>'.format(office['id'], office['name']))
        print('</optgroup>')
    print('</select><br>')
    print('<label for="addZip">New ZIP Code:</label>')
    print('<input type="number" id="addZip" name="addZip"><br>')
    print('<input type="submit" value="Add ZIP Code">')
    print('</form>') 

    print('<h3>Add Candidate to Election for an Office</h3>')
    print('<form>')
    print('<label for="office">Office:</label>')
    print('<select name="office" id="office">')
    for date in elections:
        print('<optgroup label="{}">'.format(date))
        for oid in range(0, len(elections[date]['offices'])):
            office = elections[date]['offices'][oid]
            print('<option value="{}">{}</option>'.format(office['id'], office['name']))
        print('</optgroup>')
    print('</select><br>')
    print('<label for="addCandidate">New Candidate Name:</label>')
    print('<input type="text" id="addCandidate" name="addCandidate"><br>')
    print('<input type="submit" value="Add Candidate">')
    print('</form>') 

    # reset password
    print('<h3>Reset Password</h3>')
    print('<form method="post">')
    print('<label for="newpasswd">Admin New Password:</label>')
    print('<input type="password" id="newpasswd" name="newpasswd"><br>')
    print('<input type="submit" value="Reset">')
    print('</form>')

    print('<hr>')

    print('<h3>Voter Rolls</h3>')
    json_voters = subprocess.check_output([PATH_TO_MACHINE, "get-voters"]).decode('utf-8')
    voters = json.loads(json_voters)
    print('<ul>')
    for voter in voters:
        print('<li>{} ({}): {}, {}'.format(voter['name'], voter['dob'], voter['county'], voter['zip']))
    print('</ul>')
except subprocess.CalledProcessError as e:
    print('<br><b>Error rendering interface:</b>')
    print('<code>')
    print(e.output.decode('utf-8'), end="")
    print('</code>')
    print('<br><a href="admin.cgi">Reload Interface</a>')
    print('<br><a href="home.cgi">Return to Homepage</a>')
except Exception as e:
    print('<br><b>Error rendering interface:</b>')
    print('<code>')
    print(e)
    print('</code>')
    print('<br><a href="admin.cgi">Reload Interface</a>')
    print('<br><a href="home.cgi">Return to Homepage</a>')
    raise e



