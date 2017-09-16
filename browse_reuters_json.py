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
    look up the list of all available channels
    '''
    rd = ReutersDatasource()
    print rd.call('channels')


def fetch_articles(channel_id='Wbz248', n=2):
    # fetch id's and headlines for a channel
    rd = ReutersDatasource()
    articles = rd.call('items',
                   {'channel': channel_id,
                    'channelCategory':'OLR',
                    'limit': str(n)})
    return articles['results']


def test_fetch_articles():
    articles = fetch_articles()
    print articles


def fetch_annotations(article_id):
    rd = ReutersDatasource()
    return rd.call('itemEntities', {'id': article_id,})['items']


def test_fetch_annotations():
    print fetch_annotations('tag:reuters.com,2017:newsml_L2N1LW2CE:708688512')


if __name__=='__main__':
    test_fetch_annotations()
