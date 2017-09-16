import BaseHTTPServer
import time
import sys
import json


HOST_NAME = '127.0.0.1'
PORT_NUMBER = 8950 

class ActionHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        print "GET request recieved"
    def do_POST(s):
        print "POST request recieved"
        content_length = int(s.headers.getheader('content-length',0))
        content = s.rfile.read(content_length)
        body = json.loads(content)
        print "Query : " +  body['result']['resolvedQuery']
        print "Intent : " + body['result']['metadata']['intentName']

        ## deal with response
        sample = "there are many news today"
        s.send_response(200)
        s.send_header("Content-type", "application/json")
        s.end_headers()

        speech = "this is a test"
        displayText = speech
        s.wfile.write(json.dumps({"speech": speech, "displayText": displayText}))

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
