
#!/usr/bin/env python
'''
16 Sep 2017
#HackZurich
skurikhin, vakulenko
'''

import urllib2
import urllib
import time
import json

from xml.etree.ElementTree import ElementTree, fromstring

from settings import *


AUTH_URL = "https://commerce.reuters.com/rmd/rest/xml/"
SERVICE_URL = "http://rmb.reuters.com/rmd/rest/xml/"


class ReutersDatasource:

    def __init__(self, username=USERNAME, password=PASSWORD):
        self.authToken = None
        # get a new auth token every time, expires after a week
        tree = self._call('login',{'username':username,'password':password},True)
        if tree.tag == 'authToken':
            self.authToken = tree.text
        else:
            raise Exception('unable to obtain authToken')

    def _call(self, method, args={}, auth=False):
        if auth:
            root_url = AUTH_URL
        else:
            root_url = SERVICE_URL
            args['token'] = self.authToken
        url = root_url + method + '?' + urllib.urlencode(args)
        resp = urllib2.urlopen(url, timeout=10)
        rawd = resp.read()
        return fromstring(rawd)  # parse xml    

    def call(self, method, args={}):
        return self._call(method, args, False)


def fetch_channels():
    # fetch a list of all available channels
    rd = ReutersDatasource()
    tree = rd.call('channels')
    channels = [ {'alias':c.findtext('alias'),
                  'description':c.findtext('description')}
                 for c in tree.findall('channelInformation') ]
    print ("List of channels:\n\talias\tdescription")
    print ("\n".join(["\t%(alias)s\t%(description)s"%x for x in channels]))
        
    # fetch id's and headlines for a channel
    rd = ReutersDatasource()
    tree = rd.call('items',
                   {'channel':'AdG977',
                    'channelCategory':'OLR',
                    'limit':'10'})
    items = [ {'id':c.findtext('id'),
               'headline':c.findtext('headline')}
              for c in tree.findall('result') ]
    return items


def test_fetch_channels():
    items = fetch_channels()
    print ("\n\nList of items:\n\tid\theadline")
    print ("\n".join(["\t%(id)s\t%(headline)s"%x for x in items]))


def fetch_item_tags(identity):
    rd = ReutersDatasource()
    item = rd.call('itemEntities',{'id': identity,})
    entities = item.find('item').find('entity')
    attributes = entities.findall('attribute')
    
    themes = []
    theme_names = []
    for attribute in attributes:
        value = attribute.find('value')
        name = attribute.find('name')
        themes.append(value.text)
        theme_names.append(name.text)
        
    return themes, theme_names


def test_fetch_item_tags():
    print fetch_item_tags('tag:reuters.com,2017:newsml_L2N1LW2CE:708688512')

if __name__=='__main__':
    test_fetch_channels()
