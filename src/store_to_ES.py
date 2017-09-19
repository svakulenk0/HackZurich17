#!/usr/bin/env python
'''
16 Sep 2017
#HackZurich
svakulenko
'''

from elasticsearch import Elasticsearch

from browse_reuters_json import *

TR_INDEX = 'thomson'
# TR_INDEX = 'thomson2'

mapping = {
      'settings': {
        # just one shard, no replicas for testing
        'number_of_shards': 1,
        'number_of_replicas': 0,
      },
      'mappings': {
        'articles': {
          'properties': {
            'headline': {'type': 'text', 'analyzer': 'english'},
            'annotations.entities.name': {'type': 'keyword'},
            'tags': {'type': 'keyword'},
          }
        },
      }
    }


def load_articles_in_ES(reset=False, limit=100):
    es = Elasticsearch()

    # reset index
    if reset:
        try:
            es.indices.delete(index=TR_INDEX)
            es.indices.create(index=TR_INDEX, body=mapping)
        except Exception as e:
            print (e)

    articles = fetch_articles(n=limit)
    print len(articles)
    for article in articles:
        doc = article
        # print article
        annotations = fetch_annotations(article['id'])
        # print annotations
        # entities.name
        # annotations['tags'] = [tag.lower() ]
        doc['annotations'] = annotations
        # lowercase tags
        tags = [tag['name'].lower() for annotation in annotations for tag in annotation['tags']]
        doc['tags'] = tags
        es.index(index=TR_INDEX, doc_type='articles',
                 body=doc)


def check_n_docs():
    es = Elasticsearch()
    res = es.search(index=TR_INDEX, body={"query": {"match_all": {}}})
    print("Total: %d articles" % res['hits']['total'])


def show_one():
    es = Elasticsearch()
    result = es.search(index=TR_INDEX, body={"query": {"match_all": {}}})['hits']['hits'][0]
    print json.dumps(result, indent=4, sort_keys=True)

class ESClient():

    def __init__(self, index):
        self.es = Elasticsearch()
        self.index = index

    def aggregate(self):
        '''
        returns the most popular keywords
        '''
        result = self.es.search(index=self.index, body={"query": {"match_all": {}}, "aggs": {"tags": {"terms": {"field": "tags"}}, "entities": {"terms": {"field": "annotations.entities.name"}}}})
        # return json.dumps(result, indent=4, sort_keys=True)
        return result['aggregations']
        # return result['aggregations']['popular_terms']['buckets']

    def get_top_keywords(self, keyword):
        result = self.es.search(index=self.index, body={"query": {"match": {"annotations.entities.name": keyword}}, "aggs": {"tags": {"terms": {"field": "tags"}}, "entities": {"terms": {"field": "annotations.entities.name"}}}})
        return result['aggregations']
        # ['popular_terms']['buckets']
        # print result['hits']['hits']
        # articles = [article['_id'] for article in result['hits']['hits']]
        # print len(articles)

    def explore_trend(keyword, db):
        popular_keywords = self.get_top_keywords(keyword)
        # print json.dumps(popular_keywords, indent=4, sort_keys=True)
        popular_tags = [tag['key'] for tag in popular_keywords['tags']['buckets']]
        return popular_tags

    def search(self, keyword):
        '''
        search for a sample of articles mentioning a custom keyword
        '''
        result = self.es.search(index=self.index, q=keyword)
        headlines = [article['_source']['headline'] for article in result['hits']['hits']]
        return set(headlines)

    def search_photo(self, keyword):
        '''
        search for photos with captions mentioning a custom keyword
        ['_source']['mediaType']: u'V', 'G', 'C', 'T', 'P'
        '''
        multi = {
                  "query": { 
                    "bool": { 
                      "must": [
                        { "match": { "headline" : keyword }},
                        { "match":  { "mediaType": 'P' }} 
                      ],
                    }
                  }
                }
        result = self.es.search(index=self.index, body=multi,)
        return result['hits']['hits'][0]['_source']['previewUrl']

    def find_sample_articles_by_keywords(self, topic, entity):
        '''
        search intent: find articles covering both entity and topic
        '''
        multi = {
                    "query": {
                        "bool" : {
                          "must" : [
                            {"term" : { "annotations.entities.name" : entity }},
                            {"term" : { "annotations.tags.name" : topic }}
                          ]
                        }
                    }
                 }
        result = self.es.search(index=self.index, body=multi)
        # headlines = [article['_source']['headline'] for article in result['hits']['hits']]
        random_article = result['hits']['hits'][0]
        # print random_article
        headline = result['hits']['hits'][0]['_source']['headline']
        source = result['hits']['hits'][0]['_source']['source']
        # print json.dumps(source, indent=4, sort_keys=True)
        return(headline, source)

    def get_category_context(self, topic):
        '''
        filter only the related organizations
        '''
        # "tags": {"terms": {"field": "annotations.tags.name"}}
        # query = {"query": {"match": {"annotations.tags.name": topic}}, "aggs": {"tags": {"filter" : { "term" : { "annotations.entities.type" :  "http://s.opencalais.com/1/type/em/e/Organization" }}, "aggs" : {"tags_stats" : {"terms": {"field": "annotations.entities.name"}}}}}}
        result = self.es.search(index=self.index, body={"query": {"match": {"tags": topic}}, "aggs": {"tags": {"terms": {"field": "tags"}}, "entities": {"terms": {"field": "annotations.entities.name"}}}})
        return result['hits']['hits'], result['aggregations']

    def find_sample_article_by_entity(self, entity):
        result = self.es.search(index=self.index, body={"query": {"match": {"annotations.entities.name": entity}}})
        print(result['hits']['hits'][0]['_source']['headline'])


def get_top_trends(index=TR_INDEX):
    '''
    default welcome
    '''
    db = ESClient(index)
    popular_keywords = db.aggregate()
    # print json.dumps(popular_keywords, indent=4, sort_keys=True)
    # most_popular_keyword = popular_keywords[0]['key']
    # print 'Do you want to learn more about %s or %s news?' % (most_popular_keyword, popular_keywords[1]['key'])

    # entities
    popular_entities = [entity['key'].split(',')[0] for entity in popular_keywords['entities']['buckets']]
    # print 'News about %s and %s are trending right now!' % (popular_entities[0], popular_entities[1])
    trending_entity = popular_entities[0]
    # tagstrending_entity
    # print trending_entity
    popular_entity_tags = db.get_top_keywords(trending_entity)['tags']['buckets']
    # print popular_entity_tags
    # make tags readable for presentation
    tags = [tag['key'].replace('_', '/') for tag in popular_entity_tags]


    response_string = '%s is all over the news in relation to %s and %s:' % (trending_entity, tags[0], tags[1])
    # print topic.replace('_', ', '), keyword

    # sample article about the tranding entity in the topic context
    random_headline, source = db.find_sample_articles_by_keywords(popular_entity_tags[0]['key'], entity=trending_entity)
    response_string += ' "%s" reports %s.' % (random_headline, source)

    # get a picture
    rd = ReutersDatasource()
    photo_url = db.search_photo(random_headline)
    photo_url = '%s?token=%s' % (photo_url, rd.authToken)

    # response_string += " Do you want to watch a video?"
    return (response_string, photo_url)


def test_get_top_trends(index=TR_INDEX):
    print get_top_trends(index=TR_INDEX)


def get_trending_topics(index=TR_INDEX):
    db = ESClient(index)
    popular_keywords = db.aggregate()
    popular_tags = [tag['key'].replace('_', ' & ') for tag in popular_keywords['tags']['buckets']]
    top_tag = popular_tags[0]
    return '%s is the most trending topic now. Are you interested in %s?' % (top_tag, top_tag)


def search(keyword='London bombing', index=TR_INDEX):
    '''
    testing search intent
    '''
    db = ESClient(index)
    return db.search(keyword)


def test_search_photo(keyword='London bombing', index=TR_INDEX):
    db = ESClient(index)
    print db.search_photo(keyword)


def test_explore_trend(keyword='United States', index=TR_INDEX):
    db = ESClient(index)
    popular_entity_tags = explore_trend(keyword, db)
    topic = popular_entity_tags[0]
    # print topic.replace('_', ', '), keyword
    db.find_sample_articles_by_keywords(topic, entity=keyword)


def request_topic(topic, index=TR_INDEX):
    '''
    handles topic-specific articles search or topic overview intent, e.g.
    'what's new in sports?'
    '''
    db = ESClient(index)
    categorized_articles, category_context = db.get_category_context(topic)
    response_string = "I have %d articles about %s:" % (len(categorized_articles), topic.replace('_', '&'))
    headlines = list(set([article['_source']['headline'] for article in categorized_articles]))
    return (response_string, headlines)


def test_request_topic(topic='sports'):
    print request_topic(topic)

    # print category_context

    # print json.dumps(categorized_articles, indent=4, sort_keys=True)
    # key1 = popular_keywords[1]['key']
    # print '%s and %s in %s' % (key1, popular_keywords[2]['key'], keyword)
    # db.find_sample_article_by_keyword(key1)

    # print json.dumps(subtrends, indent=4, sort_keys=True)


# def explore_top_trends(index=TR_INDEX):
#     db = ESClient(index)
#     popular_keywords = db.aggregate()
#     trends = (popular_keywords[0]['key'], popular_keywords[1]['key'])


def intents_test_set():
    # 1. default welcome current trends overview
    test_get_top_trends()
    # test_explore_trend(keyword='United Kingdom')
    print '\n'
    # 2. search more info
    print search()
    print '\n'
    # 3. show trending topics suggestions
    print get_trending_topics()
    print '\n'
    # 4. request news on a specific topic
    test_request_topic()


if __name__ == '__main__':
    # load_articles_in_ES(reset=True, limit=300)
    # check_n_docs()
    # show_one()
    # test_search_photo()

    intents_test_set()
