#!/usr/bin/env python
'''
16 Sep 2017
#HackZurich
skurikhin, svakulenko
'''
import urllib
import urllib2

# parsers
import json
from xml.etree.ElementTree import ElementTree, fromstring


from settings import *


AUTH_URL = "https://commerce.reuters.com/rmd/rest/xml/"
SERVICE_URL = "http://rmb.reuters.com/rmd/rest/json/"


class ReutersDatasource:

    def __init__(self, username=USERNAME, password=PASSWORD):
        self.authToken = None
        # get a new auth token every time, expires after a week
        tree = self._call_auth('login', {'username': username, 'password': password},True)
        if tree.tag == 'authToken':
            self.authToken = tree.text
        else:
            raise Exception('unable to obtain authToken')

    def _call_auth(self, method, args={}, auth=False):
        root_url = AUTH_URL
        url = root_url + method + '?' + urllib.urlencode(args)
        resp = urllib2.urlopen(url, timeout=10)
        rawd = resp.read()
        return fromstring(rawd)  # parse xml     

    def call(self, method, args={}):
        root_url = SERVICE_URL
        args['token'] = self.authToken
        url = root_url + method + '?' + urllib.urlencode(args)
        resp = urllib2.urlopen(url, timeout=10)
        rawd = resp.read()
        return json.loads(rawd)  # parse json 


def fetch_channels():
    '''
    fetch a list of all available channels
    '''
    rd = ReutersDatasource()
    print rd.call('channels')


if __name__=='__main__':
    fetch_channels()
