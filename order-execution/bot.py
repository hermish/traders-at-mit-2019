### IMPORTS
import tradersbot as tt
import math
import random
import heapq

### CONSTANTS
LOGIN = {
	'host': '127.0.0.1',
	'id': 'trader0',
	'password': 'trader0'
}

POS_LIMIT = 500
ORDER_LIMIT = 100
EPSILON = 0.3
MARGIN = 0.03

### STATE
PRICES = {}
BOOKS = {}
OPEN_ORDERS = {}
POSITIONS = {}

NEWS_DEVIATIONS = {}

PREDICTIONS = []
TO_CLEAR = []


### METHODS
def ack_register_method(msg, order):
	securities = msg['case_meta']['securities']
	for ticker, details in securities.items():
		if details['tradeable']:
			price = float(details['starting_price'])
			PRICES[ticker] = price
			BOOKS[ticker] = {}

def market_update_method(msg, order):
	market_state = msg['market_state']
	ticker = market_state['ticker']

	bids = market_state['bids']
	bids = [pair for pair in bids.items()]
	bids.sort(key=lambda pair: float(pair[0]))

	asks = market_state['asks']
	asks = [pair for pair in asks.items()]
	asks.sort(key=lambda pair: float(pair[0]), reverse=True)

	BOOKS[ticker] = {
		'bids': bids,
		'asks': asks
	}

	last_price = market_state['last_price']
	if not bids or not asks:
		PRICES[ticker] = last_price
		return
	max_bid = float(bids[-1][0])
	min_ask = float(asks[-1][0])
	PRICES[ticker] = (max_bid + min_ask) / 2

def trader_update_method(msg, order):
	trader_state = msg['trader_state']
	POSITIONS = trader_state['positions']
	OPEN_ORDERS = trader_state['open_orders']
	# print(trader_state['pnl']['USD'])

def news_method(msg, order):
	# Parse News
	news = msg['news']
	current_time = news['time']
	source = news['source']
	ticker, prediction_time = news['headline'].split()
	prediction_time = int(prediction_time)
	prediction_price = float(news['body'])

	if prediction_price < 0:
		NEWS_DEVIATIONS[source] = float('inf')

	# Bookkeeping
	update_deviations(current_time)
	clean_up_positions(current_time, order)

	# Trade
	if source in NEWS_DEVIATIONS and ticker in PRICES:
		threshold = deviation_to_probability(NEWS_DEVIATIONS[source])
		# print(threshold)
		if random.random() < threshold:
			if PRICES[ticker] + MARGIN < prediction_price:
				top_book_volume = BOOKS[ticker]['bids'][-1][1]
				order.addBuy(
					ticker=ticker,
					quantity=top_book_volume,
					price=None
				)
				heapq.heappush(
					TO_CLEAR,
					(prediction_time, ticker, -top_book_volume)
				)
			elif prediction_price < PRICES[ticker] - MARGIN:
				top_book_volume = BOOKS[ticker]['asks'][-1][1]
				order.addSell(
					ticker=ticker,
					quantity=top_book_volume,
					price=None
				)
				heapq.heappush(
					TO_CLEAR,
					(prediction_time, ticker, top_book_volume)
				)
	heapq.heappush(
		PREDICTIONS,
		(prediction_time, ticker, source, prediction_price)
	)


### HELPER FUNCTIONS
def deviation_to_probability(deviation):
	return math.exp(- EPSILON * deviation ** 2)

def clean_up_positions(current_time, order):
	while TO_CLEAR and TO_CLEAR[0][0] <= current_time:
		_, ticker, volume = heapq.heappop(TO_CLEAR)
		order.addBuy(
			ticker=ticker,
			quantity=volume,
			price=None
		)

def update_deviations(current_time):
	while PREDICTIONS and PREDICTIONS[0][0] <= current_time:
		_, ticker, source, prediction_price = heapq.heappop(PREDICTIONS)
		difference = prediction_price - PRICES[ticker]
		difference /= PRICES[ticker]
		NEWS_DEVIATIONS[source] = NEWS_DEVIATIONS.get(source, 0) + difference

### OVERRIDE & RUN
bot = tt.TradersBot(**LOGIN)
bot.onAckRegister = ack_register_method
bot.onMarketUpdate = market_update_method
bot.onTraderUpdate = trader_update_method
bot.onNews = news_method
bot.run()