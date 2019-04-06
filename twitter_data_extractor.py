from selenium import webdriver
from bs4 import BeautifulSoup
import time

classes = {
    'tweet': 'tweet',
    'text': 'tweet-text',
    'date': '_timestamp',
    'replies': 'js-actionReply',
    'retweeted': 'js-actionRetweet',
    'favorited': 'js-actionFavorite',
    'action_count': 'ProfileTweet-actionCountForPresentation'
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

def download_data(search_term, from_date, to_date, limit=0):
    results = []
    driver = webdriver.Chrome()
    driver.get(base_url + get_query_string(search_term, from_date, to_date))
    time.sleep(2)

    tweets = driver.find_elements_by_class_name(classes['tweet'])
    if limit > 0:
        while len(tweets) < limit:
            driver.execute_script("window.scrollBy(0, 10000)")
            time.sleep(3)
            tweets = driver.find_elements_by_class_name(classes['tweet'])
    else:
        driver.execute_script("window.scrollBy(0, 10000)")
        while len(tweets) < len(driver.find_elements_by_class_name(classes['tweet'])):
            driver.execute_script("window.scrollBy(0, 10000)")
            time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    append_results(soup, results)

    driver.close()
    return results


def append_results(soup, result_list):
    tweets = soup.find_all('div', {'class': 'tweet'})
    for tweet in tweets:
        result_list.append(tweet.find('p', {'class': 'tweet-text'}).text)

    # for tweet in tweets:
    #     text = tweet.find_element_by_class_name('tweet-text').text
    #     timestamp = tweet.find_element_by_class_name('_timestamp').get_attribute('data-time')
    #     tmp = {}
    #     result = {'text': text, 'created_at': timestamp}

    #     for action in ['js-actionReply', 'js-actionRetweet', 'js-actionFavorite']:
    #         action_object = tweet.find_element_by_class_name(action)
    #         count = action_object.find_element_by_class_name('ProfileTweet-actionCountForPresentation').text
    #         tmp[action] = count
    #     result.update(tmp)

    #     result_list.append(result)