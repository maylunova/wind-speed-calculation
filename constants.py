URL = 'https://rp5.ru/responses/reFileSynop.php'


HEADERS = {
    'Accept': 'text/html, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8,ru;q=0.7',
    'Content-type': 'application/x-www-form-urlencoded',
    'Referer': 'https://rp5.ru/',
    'User-Agent':
              'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2)'
              'AppleWebKit/537.36 (KHTML, like Gecko)'
              'Chrome/63.0.3239.84 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}

all_days = '1'
only_month = '2'

MAX_DAYS_FOR_INTERVALS = 365

WIND_SPEED = 'Wind speed'
WIND_DIRECTION = 'Wind direction'
CALM = 'Штиль, безветрие'
ALL = 'All'
# продолжительность шторма всегда принимается равной 6 часам
STORM_DURATION = 6
# эмпирический коэффициент из формулы (3.1)
COEF = 4.17
# нормативная повторяемость в годах. Должна задаваться пользователем
STORM_RECURRENCE = 25
MINIMAL_TICK = 0.2
MAXIMAL_TICK = 50
TICKS_NUMBER = 9
MINIMAL_X = 0
MINIMAL_Y = 0.01
MAXIMAL_Y = 60
PER_CENT = 100
MONTH_LIST = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
MONTH_LIST_NUMBER = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
