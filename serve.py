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

        if intent == "Category request":
            topic =  body['result']['parameters']['topic']
            list_headlines(request_topic(topic), s)
        elif intent == "Search":
            keyword = body['result']['parameters']['any']
            list_headlines(search(keyword), s)

            #title = "here are some related articles I found"
            #subtitle = "I hope you like them"
            #headlines = test_search()
            #msg_type = 1 # is a card
            
            #buttons = "{ "
            #for headline in headlines:
                #buttons += "{ \"text\" : "
                #buttons += headline
                #buttons += " , \"postback\" : www.reuters.com }, "
            #      
            #buttons += "{ \"text\" : more, \"postback\" : www.reuters.com }"
            #
            #s.wfile.write(json.dumps({"type": msg_type, "title": title, "buttons": buttons}))
            #s.wfile.write(response)
        elif intent == "Default Welcome Intent":
            intro = get_top_trends()
            speech = intro[0]
            url = intro[1]

            url = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/U.S._Marines_in_Operation_Allen_Brook_%28Vietnam_War%29_001.jpg/220px-U.S._Marines_in_Operation_Allen_Brook_%28Vietnam_War%29_001.jpg" 
            msg_type = 3
            s.wfile.write(json.dumps({"type": msg_type,"speech": speech,"imageUrl": url}))
            print url    
        else:
            speech = get_response(intent)
            msg_type = 0 # is text
            displayText = speech
            
            # set response
            sample =  "news not available" 
            s.wfile.write(json.dumps({"type": msg_type, "speech": speech, "displayText": displayText}))



def get_response(intentName):
    print intentName
    if intentName == "Default Welcome Intent":
        return get_top_trends()
    elif intentName == "Propose categories":
        return get_trending_topics()
    elif intentName == "None":
        return "always food to hear from you, friend"
    else: 
        return "I'm sorry, we are busy right now"

def list_headlines(headline_seti, s):
    #speech = "you are searching for " + keyword 
    if len(headline_set) == 0:
        headlines = "nothing about " + keyword
        display = headlines
    else:
        headlines = ""
        display = ""
        i = 0
        for headline in headline_set:
            i += 1
            if i < 5:
                display += str(i) + ". "
                headlines += headline
                display += headline
                headlines += ".\n"
                display += ".\n"
    
    s.wfile.write(json.dumps({"type" : 0, "speech": headlines, "displayText": display}))

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
