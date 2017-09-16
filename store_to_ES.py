#!/usr/bin/env python
'''
16 Sep 2017
#HackZurich
svakulenko
'''

from elasticsearch import Elasticsearch

from browse_reuters_json import *

index_name='thomson'

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
          }
        },
      }
    }


def load_articles_in_ES():
    es = Elasticsearch()

    # reset index
    try:
        es.indices.delete(index=index_name)
        es.indices.create(index=index_name, body=mapping)
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
        es.index(index=index_name, doc_type='articles',
                 body=doc)


def check_n_docs():
    es = Elasticsearch()
    res = es.search(index=index_name, body={"query": {"match_all": {}}})
    print("Total: %d articles" % res['hits']['total'])


def show_one():
    es = Elasticsearch()
    result = es.search(index=index_name, body={"query": {"match_all": {}}})
    print(result['hits']['hits'][0])


def aggregate():
    '''
    returns the most popular keywords
    '''
    es = Elasticsearch()
    result = es.search(index=index_name, body={"query": {"match_all": {}}, "aggs": {"popular_terms": {"terms": {"field": "annotations.entities.name"}}}})
    # return json.dumps(result, indent=4, sort_keys=True)
    return result['aggregations']['popular_terms']['buckets']


if __name__ == '__main__':
    # load_articles_in_ES()
    check_n_docs()
    popular_keywords = aggregate()
    print popular_keywords[0]
    # show_one()
