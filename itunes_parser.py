# -*- encoding: utf-8 -*-
import re
from lxml import etree
from BeautifulSoup import BeautifulSoup


ITUNES_NS_KEY = 'ns0'

ITUNES_NS_VALUE = 'http://www.apple.com/itms/'

NS_DATA = {}

NS_DATA[ITUNES_NS_KEY] = ITUNES_NS_VALUE

STORES = {
    'Argentina': 143505,
    'Australia': 143460,
    'Belgium': 143446,
    'Brazil': 143503,
    'Canada': 143455,
    'Chile': 143483,
    'China': 143465,
    'Colombia': 143501,
    'Costa Rica': 143495,
    'Croatia': 143494,
    'Czech Republic': 143489,
    'Denmark': 143458,
    'Deutschland': 143443,
    'El Salvador': 143506,
    'Espana': 143454,
    'Finland': 143447,
    'France': 143442,
    'Greece': 143448,
    'Guatemala': 143504,
    'Hong Kong': 143463,
    'Hungary': 143482,
    'India': 143467,
    'Indonesia': 143476,
    'Ireland': 143449,
    'Israel': 143491,
    'Italia': 143450,
    'Korea': 143466,
    'Kuwait': 143493,
    'Lebanon': 143497,
    'Luxembourg': 143451,
    'Malaysia': 143473,
    'Mexico': 143468,
    'Nederland': 143452,
    'New Zealand': 143461,
    'Norway': 143457,
    'Osterreich': 143445,
    'Pakistan': 143477,
    'Panama': 143485,
    'Peru': 143507,
    'Phillipines': 143474,
    'Poland': 143478,
    'Portugal': 143453,
    'Qatar': 143498,
    'Romania': 143487,
    'Russia': 143469,
    'Saudi Arabia': 143479,
    'Schweiz/Suisse': 143459,
    'Singapore': 143464,
    'Slovakia': 143496,
    'Slovenia': 143499,
    'South Africa': 143472,
    'Sri Lanka': 143486,
    'Sweden': 143456,
    'Taiwan': 143470,
    'Thailand': 143475,
    'Turkey': 143480,
    'United Arab Emirates': 143481,
    'United Kingdom': 143444,
    'United States': 143441,
    'Venezuela': 143502,
    'Vietnam': 143471,
    'Japan': 143462,
    'Dominican Republic': 143508,
    'Ecuador': 143509,
    'Egypt': 143516,
    'Estonia': 143518,
    'Honduras': 143510,
    'Jamaica': 143511,
    'Kazakhstan': 143517,
    'Latvia': 143519,
    'Lithuania': 143520,
    'Macau': 143515,
    'Malta': 143521,
    'Moldova': 143523,
    'Nicaragua': 143512,
    'Paraguay': 143513,
    'Uruguay': 143514,
}


def find(node, path):
    ns_path = '/'.join(['%s:%s' % (ITUNES_NS_KEY, path_node) for path_node in path.split('/')])
    return node.find(ns_path, namespaces=NS_DATA)


def findall(node, path):
    ns_path = '/'.join(['%s:%s' % (ITUNES_NS_KEY, path_node) for path_node in path.split('/')])
    return node.findall(ns_path, namespaces=NS_DATA)


def parse_reviews_page_count(page):
    page_xml = etree.fromstring(page)
    nodes = findall(page_xml, 'View/ScrollView/VBoxView/View/MatrixView/VBoxView/'
                              'VBoxView/HBoxView/TextView/SetFontStyle/b')
    page_count = 1
    try:
        pages_info = nodes[1].text
        page_count = int(pages_info.split('of')[1].strip())
    except IndexError:
        pass
    except AttributeError:
        pass
    except TypeError:
        pass
    return page_count


def parse_reviews(page):
    page_xml = etree.fromstring(page)
    reviews = []
    review_nodes = findall(page_xml, 'View/ScrollView/VBoxView/View/MatrixView/'
                                     'VBoxView/VBoxView/VBoxView')
    for review_node in review_nodes:
        review = {
            'title': None,
            'description': None,
            'user_id': None,
            'user_name': None,
            'version': None,
            'rank': None,
        }
        title = find(review_node, 'HBoxView/TextView/SetFontStyle/b')
        if title is not None:
            review['title'] = title.text
        description = find(review_node, 'TextView/SetFontStyle')
        if description is not None:
            review['description'] = description.text.strip()
        user_url = find(review_node, 'HBoxView/TextView/SetFontStyle/GotoURL')
        if user_url is not None:
            review['user_id'] = user_url.attrib['url'].split('=')[1]
        user_name = find(review_node, 'HBoxView/TextView/SetFontStyle/GotoURL/b')
        if user_name is not None:
            review['user_name'] = user_name.text.strip()
        version = find(review_node, 'HBoxView/TextView/SetFontStyle/GotoURL')
        if version is not None:
            review['version'] = re.search('Version [^\n^\ ]+', version.tail).group()
        rank = find(review_node, 'HBoxView/HBoxView/HBoxView')
        try:
            review['rank'] = int(rank.attrib['alt'].strip(' stars'))
        except KeyError:
            pass
        reviews.append(review)
    return reviews


def parse_user_reviews(page):
    page_html = BeautifulSoup(page)
    user_id = None
    try:
        user_href = page_html.find('div', **{'class': 'lockup-container paginate'})
        user_href = user_href['goto-page-href']
        user_id = user_href.split('?')[1].split('&')[0].split('=')[1]
    except KeyError:
        pass
    except IndexError:
        pass
    review_nodes = page_html.findAll('div', **{'class': 'customer-review'})
    reviews = []
    for review_node in review_nodes:
        try:
            game_title_block = review_node \
                .find('div', **{'class': 'content-lockup'}) \
                .find('li', **{'class': 'name'}) \
                .find('a')
            game_url = game_title_block['href']
            game_title = game_title_block.string
            stars = review_node \
                .find('div', **{'class': 'review-block'}) \
                .findAll('span', **{'class': 'rating-star'})
        except AttributeError:
            continue
        stars = len(stars)
        reviews.append({
            'user_id': user_id,
            'game_title': game_title,
            'game_url': game_url,
            'stars': stars
        })
    return reviews
