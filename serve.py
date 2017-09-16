import BaseHTTPServer
import time
import sys
import json

# for deploting automatically
import git
import os

# our files
from store_to_ES import *

## get a local port
#  nginx forwards traffic, ensures ssl
HOST_NAME = '127.0.0.1'
PORT_NUMBER = 8950 

# handle the requests
class ActionHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        #print "GET request recieved"
        deploy()

        s.send_response(200)
        s.send_header("Content-type", "application/json")
        s.end_headers()

        s.wfile.write("<html><body><h1>Deployed !</h1></body></html>")

    def do_POST(s):
        ## debug
        print "POST request recieved"
        
        content_length = int(s.headers.getheader('content-length',0))
        content = s.rfile.read(content_length)
        body = json.loads(content)
       
        query = body['result']['resolvedQuery']
        try:
            intent = body['result']['metadata']['intentName']
        except KeyError:
            intent = "None"

        ## debug
        print "Query : " + query
        print "Intent : " + intent

        ## deal with response
        s.send_response(200)
        s.send_header("Content-type", "application/json")
        s.end_headers()

        # set response
        sample =  "news not available" 
        speech = get_response(intent)
        displayText = speech
        s.wfile.write(json.dumps({"speech": speech, "displayText": displayText}))

def get_response(intentName):
    print "1" + intentName + "1"
    if intentName == "Default Welcome Intent":
        return get_top_trends()
    elif intentName == "Propose categories":
        print "get top trends"
        return get_trending_topics()
    elif intentName == "Search":
        return "the search function will soon be available"
        #return test_search()
    elif intentName == "None":
        return "always food to hear from you, friend"
    else: 
        return "I'm sorry, we are busy right now"

def deploy():
    path = os.path.dirname(os.path.abspath(__file__))
    g = git.Repo(path)
    origin = g.remotes[0]
    origin.pull()

if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), ActionHandler)
    print time.asctime(), "Google Action Server Started - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stoped - %s:%s" % (HOST_NAME, PORT_NUMBER)
