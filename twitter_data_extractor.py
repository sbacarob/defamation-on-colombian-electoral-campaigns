from selenium import webdriver
from bs4 import BeautifulSoup
import time
import dateutil.parser
from datetime import timedelta
from selenium.webdriver.common.proxy import *

classes = {
    'tweet': 'tweet',
    'text': 'tweet-text',
    'date': '_timestamp',
    'replies': 'js-actionReply',
    'retweeted': 'js-actionRetweet',
    'favorited': 'js-actionFavorite',
    'action_count': 'ProfileTweet-actionCount'
}

base_url = "https://twitter.com/search"

base_params = {
    'q': '-filter:retweet',
    'src': 'typd'
}

def get_query_string(term, from_date, to_date):
    q = '{} since:{} until:{}'.format(term, from_date, to_date)
    params = base_params.copy()
    params['q'] = '{} {}'.format(q, params['q'])
    encoded = ['{}={}'.format(k, v) for k, v in params.items()]
    return '?' + '&'.join(encoded)

def scroll_and_sleep(dr, secs=3):
    dr.execute_script("window.scrollBy(0, 10000)")
    time.sleep(secs)

def download_data(search_term, from_date, to_date, limit=0):
    results = {}
    proxy_host = '80.211.234.193'

    proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy': proxy_host,
        'ftpProxy': proxy_host,
        'sslProxy': proxy_host,
        'noProxy': ''
    })

    driver = webdriver.Firefox(proxy=proxy)
    driver.get(base_url + get_query_string(search_term, from_date, to_date))
    time.sleep(2)

    tweets = driver.find_elements_by_class_name(classes['tweet'])
    if limit > 0:
        while len(tweets) < limit:
            scroll_and_sleep(driver, 5)
            if len(driver.find_elements_by_class_name(classes['tweet'])) == len(tweets):
                break

            tweets = driver.find_elements_by_class_name(classes['tweet'])
    else:
        scroll_and_sleep(driver)
        while len(tweets) < len(driver.find_elements_by_class_name(classes['tweet'])):
            tweets = driver.find_elements_by_class_name(classes['tweet'])
            scroll_and_sleep(driver, 5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    append_results(soup, results)

    driver.close()
    return results


def append_results(soup, result_list):
    tweets = soup.find_all('div', {'class': 'tweet'})
    for tweet in tweets:
        id = tweet.attrs['data-tweet-id']
        text_div = tweet.find('p', {'class': 'tweet-text'})

        if text_div is None:
            continue

        lang = text_div.attrs['lang']
        text = text_div.text
        timestamp_box = tweet.find('span', {'class': '_timestamp'})
        timestamp = timestamp_box.attrs['data-time']
        tmp = {}
        result = {'text': text, 'created_at': timestamp, 'lang': lang}

        for action in ['replies', 'retweeted', 'favorited']:
            action_object = tweet.find('button', {'class': classes[action]})
            count_box = action_object.find('span', {'class': classes['action_count']})
            if count_box is not None:
                if 'data-tweet-stat-count' in count_box.attrs:
                    count = count_box.attrs['data-tweet-stat-count']
                else:
                    count = count_box.text.replace('\n', '')
            else:
                count = '0'
            if count == '': count = '0'
            tmp[action] = count

        result.update(tmp)

        result_list[id] = result

def download_data_for_period(search_term, from_date, to_date, daily_limit=0):
    complete_results = {}
    begin_date = dateutil.parser.parse(from_date)
    end_date = dateutil.parser.parse(to_date)

    while begin_date <= end_date:
        complete_results.update(
            download_data(
                search_term,
                begin_date.strftime("%Y-%m-%d"),
                (begin_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                daily_limit
                ))
        begin_date += timedelta(days=1)
    return list(complete_results.values())
