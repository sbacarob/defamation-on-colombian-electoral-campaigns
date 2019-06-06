"""Script to extract data from Twitter"""

import time
from datetime import timedelta
import json
import dateutil.parser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType

CLASSES = {
    'tweet': 'tweet',
    'text': 'tweet-text',
    'date': '_timestamp',
    'replies': 'js-actionReply',
    'retweeted': 'js-actionRetweet',
    'favorited': 'js-actionFavorite',
    'action_count': 'ProfileTweet-actionCount',
    'user': 'js-user-profile-link'
}

BASE_URL = "https://twitter.com/search"

BASE_PARAMS = {
    'q': '-filter:retweet',
    'src': 'typd'
}

def get_query_string(term, from_date, to_date):
    """
    Generate a query string based on the args received.

    Args:

    * term - The term to search for. e.g. '@IvanDuque'
    * from_date - The date from which to start including results.
    * to_date - The date until which to include results
    """
    query = '{} since:{} until:{}'.format(term, from_date, to_date)
    params = BASE_PARAMS.copy()
    params['q'] = '{} {}'.format(query, params['q'])
    encoded = ['{}={}'.format(k, v) for k, v in params.items()]
    return '?' + '&'.join(encoded)

def scroll_and_sleep(current_driver, secs=3):
    """Makes the driver scroll to the bottom of the page and sleep 10 seconds."""
    current_driver.execute_script("window.scrollBy(0, 10000)")
    time.sleep(secs)

def download_data(search_term, from_date, to_date, limit=0):
    """
    Download data from Twitter.

    Args:

    * search_term - The term to search for in Twitter. e.g. '@IvanDuque'.
    * from_date - The date from which to start including results.
    * to_date - The date until which to include results.
    * limit - Limit the number of tweets to take from the results. Defaults to 0, including all.
    """
    results = {}
    proxy_host = '' # Add a proxy host here. You can easily find available proxies online

    proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy': proxy_host,
        'ftpProxy': proxy_host,
        'sslProxy': proxy_host,
        'noProxy': ''
    })

    driver = webdriver.Firefox(proxy=proxy)
    driver.get(BASE_URL + get_query_string(search_term, from_date, to_date))
    time.sleep(2)

    tweets = driver.find_elements_by_class_name(CLASSES['tweet'])
    if limit > 0:
        while len(tweets) < limit:
            scroll_and_sleep(driver, 5)
            if len(driver.find_elements_by_class_name(CLASSES['tweet'])) == len(tweets):
                break

            tweets = driver.find_elements_by_class_name(CLASSES['tweet'])
    else:
        scroll_and_sleep(driver)
        while len(tweets) < len(driver.find_elements_by_class_name(CLASSES['tweet'])):
            tweets = driver.find_elements_by_class_name(CLASSES['tweet'])
            scroll_and_sleep(driver, 5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    append_results(soup, results)

    driver.close()
    return results


def append_results(soup, result_list):
    """
    Appends the parsed results from a day to the result list.

    Args:

    * soup - The BeautifulSoup object containing the daily results.
    * result_list - The list of results to add the daily results to.
    """
    tweets = soup.find_all('div', {'class': 'tweet'})
    for tweet in tweets:
        text_div = tweet.find('p', {'class': 'tweet-text'})
        tweet_text = text_div.text

        if text_div is None:
            continue

        timestamp_box = tweet.find('span', {'class': '_timestamp'})
        user_link = tweet.find('a', {'class': CLASSES['user']})

        if 'data-is-reply-to' in tweet.attrs and tweet.attrs['data-is-reply-to'] == "true":
            in_reply_to = json.loads(tweet.attrs['data-reply-to-users-json'])[-1]["id_str"]
            if in_reply_to == "77653794":
                tweet_text = "@IvanDuque " + tweet_text
            elif in_reply_to == "49849732":
                tweet_text = "@petrogustavo " + tweet_text

        tmp = {}
        result = {
            'text': tweet_text,
            'created_at': timestamp_box.attrs['data-time'],
            'lang': text_div.attrs['lang'],
            'user': user_link.attrs['data-user-id']
        }

        for action in ['replies', 'retweeted', 'favorited']:
            action_object = tweet.find('button', {'class': CLASSES[action]})
            count_box = action_object.find('span', {'class': CLASSES['action_count']})
            if count_box is not None:
                if 'data-tweet-stat-count' in count_box.attrs:
                    count = count_box.attrs['data-tweet-stat-count']
                else:
                    count = count_box.text.replace('\n', '')
            else:
                count = '0'
            if count == '':
                count = '0'
            tmp[action] = count

        result.update(tmp)

        result_list[tweet.attrs['data-tweet-id']] = result

def download_data_for_period(search_term, from_date, to_date, daily_limit=0):
    """
    Download all of the results in a given date range.

    Args:

    * search_term - The term to search for. e.g. '@IvanDuque'.
    * from_date - The date from which to start including results.
    * to_date - The date until which to include results.
    * daily_limit - A number to limit amount of daily results to.
    """
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
