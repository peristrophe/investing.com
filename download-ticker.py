#!/usr/bin/env python

__all__ = [
]

import requests
import subprocess
import lxml.html

from collections import namedtuple
from datetime import datetime, timedelta

FETCH_PRG = 'download-coded.zsh'

DEFAULT_END_DATE = datetime.now()
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

### this function does not get the results i expected. why ...
def fetch_historical_data1():
    res = requests.get(url, headers=headers, params=payload, allow_redirects=False)
    res.raise_for_status()
    return res.text

def fetch_historical_data2(pair, st_date=None, end_date=None, interval_sec=INTERVAL.D):
    if st_date is None:
        st_date = DEFAULT_ST_DATE

    if end_date is None:
        end_date = DEFAULT_END_DATE

    if not isinstance(st_date, datetime):
        raise ValueError('invalid argument. st_date is not datetime object.')

    if not isinstance(end_date, datetime):
        raise ValueError('invalid argument. end_date is not datetime object.')

    if pair not in PAIR.keys():
        raise ValueError('invalid argument {} as pair. please specify one of the following.\n{}'.format(pair, ', '.join(PAIR.keys())))

    cmdline = [
        '/usr/bin/env',
        'zsh',
        FETCH_PRG,
    ]

    cmdline.extend(['-p', pair])
    cmdline.extend(['-b', st_date.strftime('%Y/%m/%d')])
    cmdline.extend(['-e', end_date.strftime('%Y/%m/%d')])
    try:
        interval_opt = next(filter(lambda x: x[1] == interval_sec, INTERVAL._asdict().items()))
        cmdline.append('-{}'.format(interval_opt[0].lower()))
    except StopIteration:
        pass

    with subprocess.Popen(cmdline, stdout=subprocess.PIPE) as proc:
        res = proc.stdout.read()

    return res.decode()

def inspect_html(html):
    tree = lxml.html.fragment_fromstring(html)
    trlist = tree.xpath('/html/body/div/table/tbody/tr')
    
    if len(trlist):
        ticker = [ [ td for td in tr.xpath('td/@data-real-value') ] for tr in trlist ]
    else:
        raise ValueError('Invalid HTML Document.')
    
    return ticker[:-1]

if __name__ == '__main__':
    import os
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(
                 prog=os.path.basename(__file__),
                 description='Listing up the active/inactive users from treasure-data'
             )

    parser.add_argument('-p', '--pair', type=str, default='USD/JPY', help='currencies rate label.')
    parser.add_argument('-u', '--tick-unit', type=str, choices=['Daily', 'Weekly', 'Monthly'], default='Daily', help='unit of ticker.')
    parser.add_argument('-b', '--begin-date', default=DEFAULT_ST_DATE, help='begin date of history.')
    parser.add_argument('-e', '--end-date', default=DEFAULT_END_DATE, help='end date of history.')
    args = parser.parse_args()

    ticks = inspect_html(fetch_historical_data2(args.pair, args.begin_date, args.end_date, args.tick_unit))
    pprint(ticks)
