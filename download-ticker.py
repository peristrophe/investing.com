#!/usr/bin/env python

__all__ = [
    'fetch',
    'inspect',
]

import os
import re
import requests
import subprocess
import lxml.html

from collections import namedtuple
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
FETCH_PRG = os.path.join(HERE, 'download-coded.zsh')

jst = timezone(timedelta(hours=9), 'JST')
DEFAULT_END_DATE = datetime.now(jst)
DEFAULT_ST_DATE = DEFAULT_END_DATE.replace(year=DEFAULT_END_DATE.year-5)

PAIR = {
    'EUR/USD': 1,
    'GBP/USD': 2,
    'USD/JPY': 3,
    'EUR/JPY': 9,
    'CHF/JPY': 13,
    'AUD/JPY': 49,
    'BRL/JPY': 1513,
}

Interval = namedtuple('Interval', ('D', 'W', 'M'))
INTERVAL = Interval('Daily', 'Weekly', 'Monthly')

url = 'https://jp.investing.com/instruments/HistoricalDataAjax'

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://jp.investing.com/currencies/usd-jpy-historical-data',
    'Accept': 'text/plain, */*; q=0.01',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/603.2.5 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.5',
    'Origin': 'https://jp.investing.com',
    'X-Requested-With': 'XMLHttpRequest',
}

payload = {
    'action': 'historical_data',
    'curr_id': PAIR['USD/JPY'],
    'st_date': DEFAULT_ST_DATE.strftime('%Y/%m/%d'),
    'end_date': DEFAULT_END_DATE.strftime('%Y/%m/%d'),
    'interval_sec': INTERVAL.D,
}

### this function does not get the results i expected. why...
#def fetch():
#    res = requests.get(url, headers=headers, params=payload, allow_redirects=False)
#    res.raise_for_status()
#    return res.text

def fetch():
    pair = next(filter(lambda x: x[1] == payload.get('curr_id'), PAIR.items()))[0]
    st_date = payload.get('st_date')
    end_date = payload.get('end_date')
    interval_sec = payload.get('interval_sec')

    assert re.search('^\d{4}/\d{2}/\d{2}$', st_date) is not None, 'st_date: {}'.format(st_date)
    assert re.search('^\d{4}/\d{2}/\d{2}$', end_date) is not None, 'end_date: {}'.format(end_date)
    assert pair in PAIR.keys(), 'pair: {}'.format(pair)

    cmdline = [
        '/usr/bin/env',
        'zsh',
        FETCH_PRG,
    ]

    cmdline.extend(['-p', pair])
    cmdline.extend(['-b', st_date])
    cmdline.extend(['-e', end_date])
    try:
        interval_opt = next(filter(lambda x: x[1] == interval_sec, INTERVAL._asdict().items()))
        cmdline.append('-{}'.format(interval_opt[0].lower()))
    except StopIteration:
        pass

    print('RUNNING COMMAND: {}'.format(' '.join(cmdline)))
    with subprocess.Popen(cmdline, stdout=subprocess.PIPE) as proc:
        res = proc.stdout.read()

    return res.decode()

def inspect(html):
    tree = lxml.html.fragment_fromstring(html)
    trlist = tree.xpath('/html/body/div/table/tbody/tr')
    
    if len(trlist):
        ticker = [ [ td for td in tr.xpath('td/@data-real-value') ] for tr in trlist ]
    else:
        raise ValueError('Invalid HTML Document.')
    
    return ticker[:-1]

if __name__ == '__main__':
    import sys
    import csv
    import argparse

    parser = argparse.ArgumentParser(
                 prog=os.path.basename(__file__),
                 description='Listing up the active/inactive users from treasure-data'
             )

    unit_types = [
        INTERVAL.D,
        INTERVAL.W,
        INTERVAL.M,
    ]

    parser.add_argument('-p', '--pair', type=str, default='USD/JPY', help='currencies rate label.')
    parser.add_argument('-u', '--tick-unit', type=str, choices=unit_types, default=unit_types[0], help='unit of ticker.')
    parser.add_argument('-b', '--begin-date', type=str, default=DEFAULT_ST_DATE.strftime('%Y/%m/%d'), help='begin date of history. format YYYY/MM/DD.')
    parser.add_argument('-e', '--end-date', type=str, default=DEFAULT_END_DATE.strftime('%Y/%m/%d'), help='end date of history. format YYYY/MM/DD.')
    parser.add_argument('-i', '--iso-date', action='store_true', default=False, help='transform unixtime to iso format.')
    args = parser.parse_args()

    payload['curr_id'] = PAIR.get(args.pair, payload.get('curr_id'))
    payload['st_date'] = args.begin_date
    payload['end_date'] = args.end_date
    payload['interval_sec'] = args.tick_unit

    ticks = inspect(fetch())
    if args.iso_date:
        ticks = list(map(lambda x: [ datetime.fromtimestamp(int(v)).isoformat() if i == 0 else v for i, v in enumerate(x) ], ticks))

    writer = csv.writer(sys.stdout)
    writer.writerow(['date', 'close', 'open', 'high', 'low'])
    writer.writerows(ticks)
