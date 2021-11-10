#!/usr/bin/env python3

import cgi
import subprocess
import json
from os import environ
import re

PATH_TO_MACHINE = "./etovucca"

def render_header():
    print('Content-Type: text/html')
    print()
    print('<link rel="stylesheet" href="https://spar.isi.jhu.edu/teaching/443/main.css">')
    print('<h2 id="dlobeid-etovucca-voting-machine">DLOBEID EtovUcca Voting Machine</h2>')
    print('<h1 id="voter-registration">Voter Registration</h1><br>')

def render_footer():
    print('<a href="./home.cgi">Return to Homepage</a><br>')

def render_voting_page(invalid=False):
    render_header()
    if invalid:
        print('<b>Invalid Arguments Passed!</b>')
    print('<form method="get">')
    print('<label for="name">Voter Name</label><br>')
    print('<input type="text" id="name" name="name"><br>')
    print('<label for="county">County</label><br>')
    print('<input type="text" id="county" name="county"><br>')
    print('<label for="zipc">ZIP Code</label><br>')
    print('<input type="number" id="zipc" name="zipc"><br>')
    print('<label for="dob">Date of Birth</label><br>')
    print('<input type="date" id="dob" name="dob"><br>')
    print('<input type="submit" value="Submit">')
    print('</form>')
    render_footer()

def sanitize_input(str):
    restricted_tags = ['script', 'img', 'href', 'svg', 'iframe', 'div']
    for tag in restricted_tags:
        ci = re.compile(re.escape(tag), re.IGNORECASE)
        str = ci.sub('', str)
    return str


query_string = cgi.parse_qs(environ['QUERY_STRING'])

if query_string:
    voter_name = query_string.get('name',[''])[0]
    county = query_string.get('county', [''])[0]
    zipc = query_string.get('zipc', [''])[0]
    dob = query_string.get('dob', [''])[0]
    voter_name = sanitize_input(voter_name)
    country = sanitize_input(county)
    zipc = sanitize_input(zipc)
    dob = sanitize_input(dob)
    if voter_name and county and zipc and dob:
        voter_id = subprocess.check_output([PATH_TO_MACHINE, 'add-voter', voter_name, county, zipc, dob]).decode('utf-8').rstrip()
        if voter_id is not "0":
            render_voting_page()
            print('<b>Voter registered. ID: {} </b>'.format(voter_id))
        else:
            render_voting_page()
            print('<b>Error in registering voter. Please try again.</b>')
    else:
        render_voting_page(invalid=True)
else:
    render_voting_page()
