import aiohttp
import asyncio
import base64
import os
import shelve
import signal

from urllib.parse import quote

from .parse import parse


crawled_tweets = {}


@asyncio.coroutine
def login():
    CONSUMER_KEY = quote(os.environ['CONSUMER_KEY'])
    CONSUMER_SECRET = quote(os.environ['CONSUMER_SECRET'])

    encoded_string = '{}:{}'.format(CONSUMER_KEY, CONSUMER_SECRET)
    encoded_bytes = base64.b64encode(encoded_string.encode('utf-8'))

    headers = {
        'Authorization': 'Basic {}'.format(encoded_bytes.decode('utf-8')),
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }

    token_endpoint = 'https://api.twitter.com/oauth2/token'
    post_data = b'grant_type=client_credentials'

    response = yield from aiohttp.request(
        'POST', token_endpoint,
        headers=headers,
        data=post_data
    )
    if response.status != 200:
        print('Error [{}]'.format(response.status))
        response.close()
        return None
    else:
        data = yield from response.json()
        response.close()

        headers = {
            'Authorization': 'Bearer {}'.format(data['access_token'])
        }

        return aiohttp.ClientSession(headers=headers)


@asyncio.coroutine
def run():
    global crawled_tweets
    loop = asyncio.get_event_loop()

    session = yield from login()
    if session is None:
        print('Couldn\'t log in')
        return

    since_id = 0
    for twitter_id, tweet in crawled_tweets.items():
        when = parse(tweet)
        if when:
            loop.call_at(when, remind)
            print('remind: "{}" @ {}'.format(tweet['text'], when))
        since_id = max(since_id, twitter_id)

    while True:
        search_endpoint = 'https://api.twitter.com/1.1/search/tweets.json'
        params = {'q': '"remind me in"', 'result_type': 'recent', 'count': 100}
        if since_id != 0:
            params['since_id'] = since_id
        response = yield from session.get(search_endpoint, params=params)

        data = yield from response.json()

        for tweet in data['statuses']:
            if tweet['id'] in crawled_tweets:
                continue

            when = parse(tweet)
            if when:
                loop.call_at(when, remind)
                print('remind: "{}" @ {}'.format(tweet['text'], when))

            crawled_tweets[tweet['id']] = tweet

            since_id = max(since_id, tweet['id'])

        yield from asyncio.sleep(60 * 5)


def remind(tweet):
    print('reminding "{}"'.format(tweet['text']))


def stop(loop):
    global crawled_tweets

    with shelve.open('remindmein.db') as db:
        db['tweets'] = crawled_tweets
    loop.stop()


def main():
    global crawled_tweets

    with shelve.open('remindmein.db') as db:
        crawled_tweets = db.get('tweets', {})

    loop = asyncio.get_event_loop()
    try:
        loop.add_signal_handler(signal.SIGINT, stop, loop)
    except RuntimeError:
        pass

    loop.run_until_complete(run())

    loop.run_forever()


if __name__ == '__main__':
    main()
