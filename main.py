# -*- encoding: utf-8 -*-
from gevent import monkey
monkey.patch_all(httplib=False)

import os
import gc
import unicodecsv
import argparse
import json
import urllib2
from gevent.pool import Pool
import itunes_parser


DEFAULT_STORE = itunes_parser.STORES['United States']

ALL_PAGES = -1


def requests_iterator(requests, pool_size=200):
    i = 0
    i_last = len(requests) - 1
    pool = Pool(pool_size)
    while i < i_last:
        print i
        responses = pool.map(download, requests[i:i + pool_size])
        for response in responses:
            yield response
        i += pool_size
        gc.collect()


def get_reviews_page_count(app_id, store_id):
    first_page_content = download((_get_reviews_url(app_id), store_id))
    return itunes_parser.parse_reviews_page_count(first_page_content)


def get_reviews(app_id, store_id=DEFAULT_STORE, review_pages=ALL_PAGES, pool_size=100):
    reviews_page_count = get_reviews_page_count(app_id, store_id)
    if review_pages != ALL_PAGES and reviews_page_count > review_pages:
        reviews_page_count = review_pages

    page_requests = []
    for i in range(reviews_page_count):
        page_requests.append((_get_reviews_url(app_id, i), store_id))

    reviews = []
    for response in requests_iterator(page_requests, pool_size):
        reviews += json.loads(itunes_parser.parse_reviews(response))

    return reviews


def get_user_reviews_summary(app_id, review_pages=-1, filter_rank_in=None, filter_rank_out=None, store_id=DEFAULT_STORE, pool_size=100):
    print 'Fetching reviews...'
    reviews = get_reviews(app_id, store_id, review_pages, pool_size=pool_size)
    print 'Reviews count: %d' % len(reviews)

    user_ids = set()
    for review in reviews:
        if 'user_id' not in review:
            continue
        if filter_rank_in is not None:
            if 'rank' in review and review['rank'] < filter_rank_in:
                continue
        user_ids.add(review['user_id'])

    print 'Fetching user reviews...'
    page_requests = []
    for user_id in user_ids:
        request = (_get_user_reviews_url(user_id), store_id)
        page_requests.append(request)

    user_reviews = []
    for response in requests_iterator(page_requests, pool_size):
        user_reviews += json.loads(itunes_parser.parse_user_reviews(response))
    print 'User reviews count: %d' % len(user_reviews)

    user_reviews_summary = {}
    for review in user_reviews:
        if filter_rank_in is not None:
            if review['stars'] < filter_rank_out:
                continue
        user_reviews_summary[review['game_title']] = user_reviews_summary.get(review['game_title'], 0) + 1
    user_reviews_summary = sorted(user_reviews_summary.items(), key=lambda x: x[1], reverse=True)

    return user_reviews_summary


def download(data):
    headers = {
        'X-Apple-Store-Front': '%d-1' % data[1],
        'User-Agent': 'iTunes/9.2 (Macintosh; U; Mac OS X 10.6)'
    }
    request = urllib2.Request(data[0], headers=headers)
    return urllib2.urlopen(request).read()


def _get_reviews_url(app_id, page=0):
    url = 'http://ax.phobos.apple.com.edgesuite.net/WebObjects/MZStore.woa/wa/viewContentsUserReviews' \
          '?id=%s' \
          '&pageNumber=%d' \
          '&sortOrdering=4' \
          '&onlyLatestVersion=false' \
          '&type=Purple+Software' % (app_id, page)
    return url


def _get_user_reviews_url(user_id):
    url = 'http://itunes.apple.com/reviews?userProfileId=%s' % user_id
    return url


if __name__ == '__main__':
    m = argparse.ArgumentParser()
    m.add_argument('--app_id', '-a', type=int, help='iTunes app id')
    m.add_argument('--store_id', '-s', default=DEFAULT_STORE, type=int, help='iTunes app store id')
    m.add_argument('--review_pages', '-p', default=ALL_PAGES, type=int, help='Count of parsed review pages')
    m.add_argument('--pool', '-ps', default=200, type=int, help='Concurrent urls count')
    m.add_argument('--rank_in', '-ri', default=None, type=int, help='Filter reviews by rating')
    m.add_argument('--rank_out', '-ro', default=None, type=int, help='Filter user reviews by rating')
    m.add_argument('--out', '-o', default='', type=str, help='Count of parsed review pages')
    options = vars(m.parse_args())
    if options['app_id'] is None:
        print 'App id is required.'
        exit()
    rank_in = options['rank_in']
    rank_out = options['rank_out']

    ps = options['pool']
    if ps < 1:
        ps = 1
    if ps > 1000:
        ps = 1000
    result = get_user_reviews_summary(
        options['app_id'],
        review_pages=options['review_pages'],
        store_id=options['store_id'],
        pool_size=ps,
        filter_rank_in=rank_in,
        filter_rank_out=rank_out)

    fpath = os.path.join(options['out'], '%d.csv' % options['app_id'])
    f = open(fpath, 'wb')
    writer = unicodecsv.writer(f)
    writer.writerow(['App Name', 'Reviews Count'])
    for el in result:
        writer.writerow([el[0], el[1]])
    f.close()
