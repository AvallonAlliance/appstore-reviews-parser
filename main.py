# -*- encoding: utf-8 -*-
from gevent import monkey
monkey.patch_all(httplib=False)

import os
import unicodecsv
import argparse
import json
import urllib2
from gevent.pool import Pool
import itunes_parser


DEFAULT_STORE = itunes_parser.STORES['United States']


def get_reviews(app_id, store_id=DEFAULT_STORE,
                review_pages=-1, pool_size=100):
    pool = Pool(pool_size)
    first_page_content = pool.map(download, [(_get_reviews_url(app_id), store_id)])[0]
    pages_count = itunes_parser.parse_reviews_page_count(first_page_content)
    if review_pages > 0 and pages_count > review_pages:
        pages_count = review_pages
    page_requests = []
    for i in range(pages_count):
        if i == 0:
            continue
        page_requests.append((_get_reviews_url(app_id, i), store_id))
    page_responses = pool.map(download, page_requests)
    page_responses = [first_page_content] + page_responses
    reviews = []
    for page in page_responses:
        reviews += itunes_parser.parse_reviews(page)
    return reviews


def get_user_reviews_summary(app_id, review_pages=-1, rank_in_filter=None,
                             rank_out_filter=None, store_id=DEFAULT_STORE,
                             pool_size=100):
    print 'Get reviews'
    reviews = get_reviews(app_id, store_id, review_pages)
    print 'Reviews count: %d' % len(reviews)

    user_ids = set()
    for review in reviews:
        if 'user_id' not in review:
            continue
        if rank_in_filter is not None:
            if 'rank' in review and review['rank'] < rank_in_filter:
                continue
        user_ids.add(review['user_id'])
    reviews = None

    print 'Get user reviews'
    page_requests = []
    for user_id in user_ids:
        request = (_get_user_reviews_url(user_id), store_id)
        page_requests.append(request)

    user_reviews = []
    i_start = 0
    i_end = pool_size
    n = len(page_requests)
    pool = Pool(pool_size)
    while True:
        if i_start >= n:
            break
        print i_start
        responses = pool.map(download, page_requests[i_start:i_end])
        for el in responses:
            user_reviews += json.loads(itunes_parser.parse_user_reviews(el))
        i_start += pool_size
        i_end += pool_size
    print 'User reviews count: %d' % len(user_reviews)

    user_reviews_summary = {}
    for review in user_reviews:
        if rank_out_filter is not None:
            if review['stars'] < rank_out_filter:
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
    m.add_argument('--review_pages', '-p', default=25, type=int, help='Count of parsed review pages')
    m.add_argument('--out', '-o', default='', type=str, help='Count of parsed review pages')
    m.add_argument('--pool', '-ps', default=100, type=int, help='Concurrent urls count')
    options = vars(m.parse_args())
    if options['app_id'] is None:
        print 'App id is required.'
        exit()
    pool_size = options['pool']
    if pool_size < 1:
        pool_size = 1
    if pool_size > 1000:
        pool_size = 1000
    result = get_user_reviews_summary(
        options['app_id'],
        review_pages=options['review_pages'],
        store_id=options['store_id'],
        pool_size=pool_size)
    fpath = os.path.join(options['out'], '%d.csv' % options['app_id'])
    f = open(fpath, 'wb')
    writer = unicodecsv.writer(f)
    writer.writerow(['App Name', 'Reviews Count'])
    for el in result:
        writer.writerow([el[0], el[1]])
    f.close()
