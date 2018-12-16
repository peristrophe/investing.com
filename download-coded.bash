#!/bin/bash

here=$(dirname $(readlink -f $0))
myself=$(basename $0)

declare -A currencies
currencies['EUR/USD']=1
currencies['GBP/USD']=2       ### (GBP=イギリスポンド)
currencies['USD/JPY']=3
currencies['EUR/JPY']=9
currencies['CHF/JPY']=13      ### (CHF=スイスフラン)
currencies['AUD/JPY']=49      ### (AUD=オーストラリアドル)
currencies['BRL/JPY']=1513    ### (BRL=ブラジルレアル)

function urlEnc() {
    if [ -p /dev/stdin ];
    then
        cat - | nkf -WwMQ | tr '=' '%' | sed -e 's/%$//g' | tr -d '\n'
    else
        echo "$1" | nkf -WwMQ | tr '=' '%' | sed -e 's/%$//g' | tr -d '\n'
    fi
}

function urlDec() {
    if [ -p /dev/stdin ];
    then
        cat - | nkf -w --url-input
    else
        echo "$1" | nkf -w --url-input
    fi
}

function addParam() {
    [ -z $(eval echo '$'${1}) ] && return 1
    sep='&'
    [ -z $params ] && sep=''
    params="${params}${sep}${1}=$(eval echo '$'${1} | urlEnc)"
    unset sep
}

url='https://jp.investing.com/instruments/HistoricalDataAjax'
content='Content-Type: application/x-www-form-urlencoded'
referer='Referer: https://jp.investing.com/currencies/usd-jpy-historical-data'
accept='Accept: text/plain, */*; q=0.01'
useragent='User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/603.2.5 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.5'
origin='Origin: https://jp.investing.com'
reqtype='X-Requested-With: XMLHttpRequest'

action='historical_data'
curr_id=${currencies['USD/JPY']}
st_date=$(date --date '5 years ago' '+%Y/%m/%d')
end_date=$(date '+%Y/%m/%d')
interval_sec='Daily'

msg="${here}/${myself}

Usage:
    ${myself} [-hdwm] [-b <begin>] [-e <end>] [-c <pair>]

Options:
    -h        : print this.

    -d        : select daily ticker. (default)

    -w        : select weekly ticker.

    -m        : select moonthly ticker.

    -b <begin>: begin date of historical data. format YYYY/MM/DD

    -e <end>  : end date of historical data. format YYYY/MM/DD

    -c <pair> : select market for currencies pair. supported below.
                $(echo ${!currencies[@]} | sed -e 's/ /, /g')"

set -- $(getopt hdwmc:b:e: $*)

while [ $# -ne 0 ]
do
    case $1 in
        -h) echo "${msg}" >&2
            exit 0
            ;;
        -d) interval_sec='Daily'
            shift
            ;;
        -w) interval_sec='Weekly'
            shift
            ;;
        -m) interval_sec='Monthly'
            shift
            ;;
        -b) [[ ${2} =~ ^[0-9]{4}/[0-9]{2}/[0-9]{2}$ ]] && st_date=${2}
            shift 2
            ;;
        -e) [[ ${2} =~ ^[0-9]{4}/[0-9]{2}/[0-9]{2}$ ]] && end_date=${2}
            shift 2
            ;;
        -c) curr_id=${currencies[${2}]}
            shift 2
            ;;
        --) shift
            break
            ;;
        *)  shift
            ;;
    esac
done

addParam 'action'
addParam 'curr_id'
addParam 'st_date'
addParam 'end_date'
addParam 'interval_sec'

#echo $params
curl -s ${url} \
    -H "${content}" -H "${referer}" -H "${accept}" \
    -H "${useragent}" -H "${origin}" -H "${reqtype}" \
    --data "${params}"
