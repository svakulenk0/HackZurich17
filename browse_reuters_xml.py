
#!/usr/bin/env python
'''
16 Sep 2017
#HackZurich
skurikhin, svakulenko
'''

import urllib2
import urllib
import time
from collections import Counter

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
    '''
    fetch a list of all available channels
    '''
    rd = ReutersDatasource()
    tree = rd.call('channels')
    channels = [ {'alias':c.findtext('alias'),
                  'description':c.findtext('description')}
                 for c in tree.findall('channelInformation') ]
    print ("List of channels:\n\talias\tdescription")
    print ("\n".join(["\t%(alias)s\t%(description)s"%x for x in channels]))


def fetch_channel(channel_id='Wbz248', n=2):
    # fetch id's and headlines for a channel
    rd = ReutersDatasource()
    tree = rd.call('items',
                   {'channel': channel_id,
                    'channelCategory':'OLR',
                    'limit': str(n)})
    items = [ {'id':c.findtext('id'),
               'headline':c.findtext('headline')}
              for c in tree.findall('result') ]
    return items


def test_fetch_channel():
    items = fetch_channel()
    print ("\n\nList of items:\n\tid\theadline")
    print ("\n".join(["\t%(id)s\t%(headline)s"%x for x in items]))


def get_entity_attrs(entity):
    attributes = entity.findall('attribute')
    
    themes = []
    theme_names = []
    for attribute in attributes:
        value = attribute.find('value')
        name = attribute.find('name')
        themes.append(value.text)
        theme_names.append(name.text)
        
    return themes, theme_names


def fetch_annotations(article_id):
    categories = []
    article_entities = []

    rd = ReutersDatasource()
    item = rd.call('itemEntities',{'id': article_id,})
    
    tags = item.find('item').findall('tag')
    
    if tags:
        for tag in tags:
            categories.append(tag.find('name').text)

    entities = item.find('item').findall('entity')
    
    if entities:
        for entity in entities:
            attribute = entity.find('attribute')
            if attribute is not None:
                attribute_text = attribute.find('value').text
                article_entities.append(attribute_text)

    return categories, article_entities


def fetch_item_tags(article_id):
    rd = ReutersDatasource()
    item = rd.call('itemEntities',{'id': article_id,})
    tags = item.find('item').findall('tag')
    if tags:
        categories = []
        for tag in tags:
            categories.append(tag.find('name').text)
        return categories


def test_fetch_item_tags():
    print fetch_item_tags('tag:reuters.com,2017:newsml_L2N1LW2CE:708688512')


def fetch_item_entity(article_id):
    rd = ReutersDatasource()
    item = rd.call('itemEntities',{'id': article_id,})
    entity = item.find('item').find('entity')
    if entity:
        return get_entity_attrs(entity)


def test_fetch_item_entity():
    print fetch_item_entity('tag:reuters.com,2017:newsml_L2N1LW2CE:708688512')


def fetch_item_entities(article_id):
    rd = ReutersDatasource()
    item = rd.call('itemEntities',{'id': article_id,})
    entities = item.find('item').findall('entity')
    if entities:
        for entity in entities:
            print get_entity_attrs(entity)


def test_fetch_item_entities():
    fetch_item_entities('tag:reuters.com,2017:newsml_L2N1LW2CE:708688512')


def lookup_tags():
    headlines = set()
    tags = []
    entities = []
    articles = fetch_channel(channel_id='STK567', n=100)
    for article in articles:
        article_title = article['headline']
        if article_title not in headlines:
            headlines.add(article_title)
            article_id = article['id']
            # print article_id, article_title
            article_tags, article_entities = fetch_annotations(article_id)
            if article_tags:
                tags.extend(article_tags)
            if article_entities:
                entities.extend(article_entities)

    # aggregate annotations summary
    tags = Counter(tags)
    entities = Counter(entities)

    print tags
    print entities
    #     tags = article.find('item').findall('tag')
    #     if tags:
    #         categories = []
    #         for tag in tags:
    #             categories.append(tag.find('name').text)
    #         print categories


if __name__=='__main__':
    # lookup_tags()
    # fetch_channels()
    # test_fetch_channel()
    # test_fetch_item_tags()
    lookup_tags()
