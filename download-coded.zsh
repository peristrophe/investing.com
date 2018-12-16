#!/usr/bin/env zsh

local -A opthash
zparseopts -D -M -A opthash -- \
    h -help=h \
    d -daily=d \
    w -weekly=w \
    m -monthly=m \
    b: -begin:=b \
    e: -end:=e \
    p: -pair:=p

local -A currencies
currencies[EUR/USD]=1
currencies[GBP/USD]=2      ### GBP=イギリスポンド
currencies[USD/JPY]=3
currencies[EUR/JPY]=9
currencies[CHF/JPY]=13     ### CHF=スイスフラン
currencies[AUD/JPY]=49     ### AUD=オーストラリアドル
currencies[BRL/JPY]=1513   ### BRL=ブラジルレアル

local url='https://jp.investing.com/instruments/HistoricalDataAjax'
local content='Content-Type: application/x-www-form-urlencoded'
local referer='Referer: https://jp.investing.com/currencies/usd-jpy-historical-data'
local accept='Accept: text/plain, */*; q=0.01'
local useragent='User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/603.2.5 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.5'
local origin='Origin: https://jp.investing.com'
local reqtype='X-Requested-With: XMLHttpRequest'

local action='historical_data'
local curr_id=${currencies[USD/JPY]}
local interval_sec='Daily'
case $(uname) in
    "Darwin")
        local st_date=$(date -v -5y '+%Y/%m/%d')
        local end_date=$(date '+%Y/%m/%d')
        ;;
    "Linux")
        local st_date=$(date --date '5 years ago' '+%Y/%m/%d')
        local end_date=$(date '+%Y/%m/%d')
        ;;
    *)
        ;;
esac

local helpmsg=$(cat <<-__HELP__
$(basename ${0})
  download historical data from investing.com

USAGE:
  ${0} [-h|--help] [-d|--daily] [-w|--weekly] [-m|--monthly]
       [-b|--begin <DATE>] [-e|--end <DATE>] [-p|--pair <LABEL>]

Options:
  -h|--help         : print this.
  -d|--daily        : select daily ticker. (default)
  -w|--weekly       : select weekly ticker.
  -m|--monthly      : select moonthly ticker.
  -b|--begin <DATE> : begin date of historical data. format YYYY/MM/DD
  -e|--end <DATE>   : end date of historical data. format YYYY/MM/DD
  -p|--pair <LABEL> : select market for currencies pair. supported below.
                      $(echo ${(k)currencies[@]} | sed -e 's/ /, /g')
__HELP__
)

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
    typeset sep='&'
    [ -z $(eval echo '$'${1}) ] && return 1
    [ -z $params ] && sep=''
    params="${params}${sep}${1}=$(eval echo '$'${1} | urlEnc)"
}

function check_cmd_require() {
    if [ ! -e "$(which ${2})" ]; then
        echo "$(basename ${1}): command not found: ${2}" >&2
        exit 1
    fi
}

[[ -n "${opthash[(i)-h]}" ]] && echo "${helpmsg}" && exit 0
[[ -n "${opthash[(i)-d]}" ]] && interval_sec="Daily"
[[ -n "${opthash[(i)-w]}" ]] && interval_sec="Weekly"
[[ -n "${opthash[(i)-m]}" ]] && interval_sec="Monthly"
[[ -n "${opthash[(i)-b]}" ]] && [[ ${opthash[-b]} =~ ^[0-9]{4}/[0-9]{2}/[0-9]{2}$ ]] && st_date="${opthash[-b]}"
[[ -n "${opthash[(i)-e]}" ]] && [[ ${opthash[-e]} =~ ^[0-9]{4}/[0-9]{2}/[0-9]{2}$ ]] && end_date="${opthash[-e]}"
[[ -n "${opthash[(i)-p]}" ]] && curr_id="${currencies[${opthash[-p]}]}"

addParam 'action'
addParam 'curr_id'
addParam 'st_date'
addParam 'end_date'
addParam 'interval_sec'

#echo $params
curl -s "${url}" \
    -H "${content}" -H "${referer}" -H "${accept}" \
    -H "${useragent}" -H "${origin}" -H "${reqtype}" \
    --data "${params}"
