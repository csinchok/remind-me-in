import aiohttp
import asyncio
import base64
import datetime
import pytz
import re
import shelve
import signal

from urllib.parse import quote


CONSUMER_KEY = 'hbOdOcpHGoPPBRb02n85xtmga'
CONSUMER_SECRET = 'LpOa8MPD6yR3uESE3AvuRY7CMjlYyNOJrrrV0foQU0bWJnoAyU'

number_strings = {
    'a': 1,
    'an': 1,
    'a few': 3,
    'a couple': 2,
    'a couple of': 2,
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'fifteen': 15,
    'twenty': 20,
    'thirty': 30,
    'a half': 0.5,
    'forty-five': 45,
    'forty five': 45,
    'ninety': 90
}

UNIT_MAP = {
    'hour': 60 * 60,
    'hours': 60 * 60,
    'minutes': 60,
    'minute': 60,
    'min': 60,
    'mins': 60,
    'days': 60 * 60 * 24,
    'day': 60 * 60 * 24,
    'year': 60 * 60 * 24 * 365,
    'years': 60 * 60 * 24 * 365,
    'month': 31 * 60 * 60 * 24,
    'months': 31 * 60 * 60 * 24,
    'week': 7 * 60 * 60 * 24,
    'weeks': 7 * 60 * 60 * 24,
}

TIMEZONE_MAPPINGS = { 'International Date Line West' : 'Pacific/Midway', 'Midway Island' : 'Pacific/Midway', 'American Samoa' : 'Pacific/Pago_Pago', 'Hawaii' : 'Pacific/Honolulu', 'Alaska' : 'America/Juneau', 'Pacific Time (US & Canada)' : 'America/Los_Angeles', 'Tijuana' : 'America/Tijuana', 'Mountain Time (US & Canada)' : 'America/Denver', 'Arizona' : 'America/Phoenix', 'Chihuahua' : 'America/Chihuahua', 'Mazatlan' : 'America/Mazatlan', 'Central Time (US & Canada)' : 'America/Chicago', 'Saskatchewan' : 'America/Regina', 'Guadalajara' : 'America/Mexico_City', 'Mexico City' : 'America/Mexico_City', 'Monterrey' : 'America/Monterrey', 'Central America' : 'America/Guatemala', 'Eastern Time (US & Canada)' : 'America/New_York', 'Indiana (East)' : 'America/Indiana/Indianapolis', 'Bogota' : 'America/Bogota', 'Lima' : 'America/Lima', 'Quito' : 'America/Lima', 'Atlantic Time (Canada)' : 'America/Halifax', 'Caracas' : 'America/Caracas', 'La Paz' : 'America/La_Paz', 'Santiago' : 'America/Santiago', 'Newfoundland' : 'America/St_Johns', 'Brasilia' : 'America/Sao_Paulo', 'Buenos Aires' : 'America/Argentina/Buenos_Aires', 'Montevideo' : 'America/Montevideo', 'Georgetown' : 'America/Guyana', 'Greenland' : 'America/Godthab', 'Mid-Atlantic' : 'Atlantic/South_Georgia', 'Azores' : 'Atlantic/Azores', 'Cape Verde Is.' : 'Atlantic/Cape_Verde', 'Dublin' : 'Europe/Dublin', 'Edinburgh' : 'Europe/London', 'Lisbon' : 'Europe/Lisbon', 'London' : 'Europe/London', 'Casablanca' : 'Africa/Casablanca', 'Monrovia' : 'Africa/Monrovia', 'UTC' : 'Etc/UTC', 'Belgrade' : 'Europe/Belgrade', 'Bratislava' : 'Europe/Bratislava', 'Budapest' : 'Europe/Budapest', 'Ljubljana' : 'Europe/Ljubljana', 'Prague' : 'Europe/Prague', 'Sarajevo' : 'Europe/Sarajevo', 'Skopje' : 'Europe/Skopje', 'Warsaw' : 'Europe/Warsaw', 'Zagreb' : 'Europe/Zagreb', 'Brussels' : 'Europe/Brussels', 'Copenhagen' : 'Europe/Copenhagen', 'Madrid' : 'Europe/Madrid', 'Paris' : 'Europe/Paris', 'Amsterdam' : 'Europe/Amsterdam', 'Berlin' : 'Europe/Berlin', 'Bern' : 'Europe/Berlin', 'Rome' : 'Europe/Rome', 'Stockholm' : 'Europe/Stockholm', 'Vienna' : 'Europe/Vienna', 'West Central Africa' : 'Africa/Algiers', 'Bucharest' : 'Europe/Bucharest', 'Cairo' : 'Africa/Cairo', 'Helsinki' : 'Europe/Helsinki', 'Kyiv' : 'Europe/Kiev', 'Riga' : 'Europe/Riga', 'Sofia' : 'Europe/Sofia', 'Tallinn' : 'Europe/Tallinn', 'Vilnius' : 'Europe/Vilnius', 'Athens' : 'Europe/Athens', 'Istanbul' : 'Europe/Istanbul', 'Minsk' : 'Europe/Minsk', 'Jerusalem' : 'Asia/Jerusalem', 'Harare' : 'Africa/Harare', 'Pretoria' : 'Africa/Johannesburg', 'Kaliningrad' : 'Europe/Kaliningrad', 'Moscow' : 'Europe/Moscow', 'St. Petersburg' : 'Europe/Moscow', 'Volgograd' : 'Europe/Volgograd', 'Samara' : 'Europe/Samara', 'Kuwait' : 'Asia/Kuwait', 'Riyadh' : 'Asia/Riyadh', 'Nairobi' : 'Africa/Nairobi', 'Baghdad' : 'Asia/Baghdad', 'Tehran' : 'Asia/Tehran', 'Abu Dhabi' : 'Asia/Muscat', 'Muscat' : 'Asia/Muscat', 'Baku' : 'Asia/Baku', 'Tbilisi' : 'Asia/Tbilisi', 'Yerevan' : 'Asia/Yerevan', 'Kabul' : 'Asia/Kabul', 'Ekaterinburg' : 'Asia/Yekaterinburg', 'Islamabad' : 'Asia/Karachi', 'Karachi' : 'Asia/Karachi', 'Tashkent' : 'Asia/Tashkent', 'Chennai' : 'Asia/Kolkata', 'Kolkata' : 'Asia/Kolkata', 'Mumbai' : 'Asia/Kolkata', 'New Delhi' : 'Asia/Kolkata', 'Kathmandu' : 'Asia/Kathmandu', 'Astana' : 'Asia/Dhaka', 'Dhaka' : 'Asia/Dhaka', 'Sri Jayawardenepura' : 'Asia/Colombo', 'Almaty' : 'Asia/Almaty', 'Novosibirsk' : 'Asia/Novosibirsk', 'Rangoon' : 'Asia/Rangoon', 'Bangkok' : 'Asia/Bangkok', 'Hanoi' : 'Asia/Bangkok', 'Jakarta' : 'Asia/Jakarta', 'Krasnoyarsk' : 'Asia/Krasnoyarsk', 'Beijing' : 'Asia/Shanghai', 'Chongqing' : 'Asia/Chongqing', 'Hong Kong' : 'Asia/Hong_Kong', 'Urumqi' : 'Asia/Urumqi', 'Kuala Lumpur' : 'Asia/Kuala_Lumpur', 'Singapore' : 'Asia/Singapore', 'Taipei' : 'Asia/Taipei', 'Perth' : 'Australia/Perth', 'Irkutsk' : 'Asia/Irkutsk', 'Ulaanbaatar' : 'Asia/Ulaanbaatar', 'Seoul' : 'Asia/Seoul', 'Osaka' : 'Asia/Tokyo', 'Sapporo' : 'Asia/Tokyo', 'Tokyo' : 'Asia/Tokyo', 'Yakutsk' : 'Asia/Yakutsk', 'Darwin' : 'Australia/Darwin', 'Adelaide' : 'Australia/Adelaide', 'Canberra' : 'Australia/Melbourne', 'Melbourne' : 'Australia/Melbourne', 'Sydney' : 'Australia/Sydney', 'Brisbane' : 'Australia/Brisbane', 'Hobart' : 'Australia/Hobart', 'Vladivostok' : 'Asia/Vladivostok', 'Guam' : 'Pacific/Guam', 'Port Moresby' : 'Pacific/Port_Moresby', 'Magadan' : 'Asia/Magadan', 'Srednekolymsk' : 'Asia/Srednekolymsk', 'Solomon Is.' : 'Pacific/Guadalcanal', 'New Caledonia' : 'Pacific/Noumea', 'Fiji' : 'Pacific/Fiji', 'Kamchatka' : 'Asia/Kamchatka', 'Marshall Is.' : 'Pacific/Majuro', 'Auckland' : 'Pacific/Auckland', 'Wellington' : 'Pacific/Auckland', 'Nuku\'alofa' : 'Pacific/Tongatapu', 'Tokelau Is.' : 'Pacific/Fakaofo', 'Chatham Is.' : 'Pacific/Chatham', 'Samoa' : 'Pacific/Apia' }


crawled_tweets = {}


@asyncio.coroutine
def login():
    encoded_string = '{}:{}'.format(quote(CONSUMER_KEY), quote(CONSUMER_SECRET))
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


def parse_numbers(text, created_at, timezone):
    match = re.search('(\d+) (minutes?|hours?|days?|weeks?|months?|years?)', text)
    if match:
        quantity, unit = match.groups()

        delta = datetime.timedelta(seconds=float(quantity) * UNIT_MAP[unit])

        return created_at + delta

    for key, value in number_strings.items():
        match = re.search('({}) (minutes?|hours?|days?|weeks?|months?|years?)'.format(key), text)
        if match:
            quantity, unit = match.groups()
            delta = datetime.timedelta(seconds=value * UNIT_MAP[unit])

            return created_at + delta


def parse_morning(text, created_at, timezone):
    match = re.search('(the morning|am|a\.m\.)', text)
    if match:
        tomorrow = created_at + datetime.timedelta(days=1)
        when = datetime.datetime(
            year=tomorrow.year,
            month=tomorrow.month,
            day=tomorrow.day,
            hour=9,
            minute=30,
            tzinfo=timezone
        )
        return when


def parse(tweet):
    text = tweet['text'].lower()
    when = None

    # "Mon Sep 24 03:35:21 +0000 2012"
    date_format = '%a %b %d %H:%M:%S +0000 %Y'
    created_at = datetime.datetime.strptime(tweet['created_at'], date_format)
    created_at = created_at.replace(tzinfo=pytz.utc)
    timezone = pytz.timezone('America/Chicago')
    if tweet['user'].get('time_zone'):
        profile_tz = tweet['user']['time_zone']
        try:
            timezone = pytz.timezone(TIMEZONE_MAPPINGS.get(profile_tz, profile_tz))
        except pytz.exceptions.UnknownTimeZoneError:
            pass

    index = text.find('remind me in')
    if index > -1:
        when_slice = text[index + 12:]
    else:
        print('no match: "{}"'.format(text))
        return

    for test_fn in [parse_numbers, parse_morning]:
        when = test_fn(when_slice, created_at, timezone)
        if when:
            break
    else:
        print('can\'t parse "{}"'.format(text))

    if when and when > datetime.datetime.now(pytz.utc):
        epoch = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
        when_timestamp = int((when - epoch).total_seconds())
        return when_timestamp


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
