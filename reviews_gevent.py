# -*- encoding: utf-8 -*-
import grequests
import itunes_parser


DEFAULT_STORE = itunes_parser.STORES['United States']


def get_reviews_url(app_id, page=0):
    url = 'http://ax.phobos.apple.com.edgesuite.net/WebObjects/MZStore.woa/wa/viewContentsUserReviews' \
          '?id=%s' \
          '&pageNumber=%d' \
          '&sortOrdering=4' \
          '&onlyLatestVersion=false' \
          '&type=Purple+Software' % (app_id, page)
    return url


def get_user_reviews_url(user_id):
    url = 'http://itunes.apple.com/WebObjects/MZStore.woa/wa/viewUsersUserReviews' \
          '?userProfileId=%s' % user_id
    return url


def get_itunes_request(url, store_id=DEFAULT_STORE):
    headers = {
        'X-Apple-Store-Front': '%d-1' % store_id,
        'User-Agent': 'iTunes/9.2 (Macintosh; U; Mac OS X 10.6)'
    }
    request = grequests.get(url, headers=headers)
    return request


def make_itunes_request(async_requests):
    responses = grequests.map(async_requests)
    return responses


def get_reviews(app_id, store_id=DEFAULT_STORE):
    first_page = make_itunes_request([get_itunes_request(get_reviews_url(app_id), store_id)])[0]
    first_page_content = first_page.content
    pages_count = itunes_parser.parse_reviews_page_count(first_page_content)
    page_requests = []
    for i in range(pages_count):
        page_requests.append(get_itunes_request(get_reviews_url(app_id, i), store_id))
    page_responses = grequests.map(page_requests)
    reviews = []
    for page in page_responses:
        reviews += itunes_parser.parse_reviews(page.content)
    return reviews


def get_user_reviews_summary(app_id, rank_in_filter=None,
                             rank_out_filter=None, store_id=DEFAULT_STORE):
    reviews = get_reviews(app_id, store_id)
    user_ids = set()
    for review in reviews:
        if 'user_id' not in review:
            continue
        if rank_in_filter is not None:
            if 'rank' in review and review['rank'] < rank_in_filter:
                continue
        user_ids.add(review['user_id'])
    page_requests = []
    for user_id in user_ids:
        page_requests.append(get_itunes_request(get_user_reviews_url(user_id), store_id))
    page_responses = grequests.map(page_requests)
    user_reviews = []
    for page in page_responses:
        user_reviews += itunes_parser.parse_user_reviews(page.content)
    user_reviews_summary = {}
    for review in user_reviews:
        if rank_out_filter is not None:
            if review['stars'] < rank_out_filter:
                continue
        user_reviews_summary[review['game_title']] = user_reviews_summary.get(review['game_title'], 0) + 1
    user_reviews_summary = sorted(user_reviews_summary.items(), key=lambda x: x[1], reverse=True)
    return user_reviews_summary
