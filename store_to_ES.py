#!/usr/bin/env python
'''
16 Sep 2017
#HackZurich
svakulenko
'''

from elasticsearch import Elasticsearch

from browse_reuters_json import *

TR_INDEX = 'thomson'

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
            'annotations.tags.name': {'type': 'keyword'},
          }
        },
      }
    }


def load_articles_in_ES():
    es = Elasticsearch()

    # reset index
    try:
        es.indices.delete(index=TR_INDEX)
        es.indices.create(index=TR_INDEX, body=mapping)
    except Exception as e:
        print (e)

    articles = fetch_articles(n=100)
    print len(articles)
    for article in articles:
        doc = article
        # print article
        annotations = fetch_annotations(article['id'])
        # print annotations
        doc['annotations'] = annotations
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
        result = self.es.search(index=self.index, body={"query": {"match_all": {}}, "aggs": {"tags": {"terms": {"field": "annotations.tags.name"}}, "entities": {"terms": {"field": "annotations.entities.name"}}}})
        # return json.dumps(result, indent=4, sort_keys=True)
        return result['aggregations']
        # return result['aggregations']['popular_terms']['buckets']

    def explore_trend(self, keyword):
        result = self.es.search(index=self.index, body={"query": {"match": {"annotations.entities.name": keyword}}, "aggs": {"popular_entities": {"terms": {"field": "annotations.entities.name"}}}})
        return result['aggregations']['popular_terms']['buckets']
        # print result['hits']['hits']
        # articles = [article['_id'] for article in result['hits']['hits']]
        # print len(articles)

    def find_sample_article_by_keyword(self, keyword):
        result = self.es.search(index=self.index, body={"query": {"match": {"annotations.entities.name": keyword}}})
        print(result['hits']['hits'][0]['_source']['headline'])


def get_top_trends(index=TR_INDEX):
    db = ESClient(index)
    popular_keywords = db.aggregate()
    print json.dumps(popular_keywords, indent=4, sort_keys=True)
    # most_popular_keyword = popular_keywords[0]['key']
    # print 'Do you want to learn more about %s or %s news?' % (most_popular_keyword, popular_keywords[1]['key'])

    # entities
    popular_entities = [entity['key'].split(',')[0] for entity in popular_keywords['entities']['buckets']]
    print 'News about %s and %s are trending right now!' % (popular_entities[0], popular_entities[1])
    # tags
    popular_tags = [tag['key'].replace('_', ' & ') for tag in popular_keywords['tags']['buckets']]
    print 'Are you interested in %s or %s news?' % (popular_tags[0], popular_tags[1])


def test_explore_trend(keyword='United States', index=TR_INDEX):
    db = ESClient(index)
    popular_keywords = db.explore_trend(keyword)
    print json.dumps(popular_keywords[1:], indent=4, sort_keys=True)
    key1 = popular_keywords[1]['key']
    # print '%s and %s in %s' % (key1, popular_keywords[2]['key'], keyword)
    # db.find_sample_article_by_keyword(key1)

    # print json.dumps(subtrends, indent=4, sort_keys=True)


# def explore_top_trends(index=TR_INDEX):
#     db = ESClient(index)
#     popular_keywords = db.aggregate()
#     trends = (popular_keywords[0]['key'], popular_keywords[1]['key'])


if __name__ == '__main__':
    # load_articles_in_ES()
    # check_n_docs()
    get_top_trends()
    # test_explore_trend()
    # show_one()