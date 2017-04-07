from theatre_ag import default_cost

from pagora.system import LimitSellOrder, LimitBuyOrder


class TradeRange(object):

    def __init__(self, low_quantity, high_quantity, low_price, high_price, random):
        self.low_quantity = low_quantity
        self.high_quantity = high_quantity
        self.low_price = low_price
        self.high_price = high_price
        self.random = random

    def random_quantity(self, ceiling):
        return min(ceiling, self.random.randint(self.low_quantity, self.high_quantity))

    def random_price(self, mid_point):
        return max(1, self.random.randint(self.low_price, self.high_price) + mid_point)


class RandomTraderWorkflow(object):

    is_workflow = True

    def __init__(self, trading_account, random, sell_ranges, buy_ranges):
        self.trading_account = trading_account
        self.random = random
        self.sell_ranges = sell_ranges
        self.buy_ranges = buy_ranges

    def trade(self, market):
        while True:
            self.speak(market)

    @default_cost(1)
    def speak(self, market):

        random_stock = self.random.choice(self.sell_ranges.keys())

        if self.random.choice([True, False]):
            self.perform_sell_action(random_stock, market)
        else:
            self.perform_buy_action(random_stock, market)

    def perform_sell_action(self, stock, market):
        uncommitted_quantity = self.trading_account.available_inventory[stock]

        sell_range = self.sell_ranges[stock]

        quantity = sell_range.random_quantity(uncommitted_quantity)

        if quantity > 0:

            offer_price = market.last_known_best_offer_price

            if offer_price is None:
                return

            price = sell_range.random_price(offer_price)
            limit_sell_order = LimitSellOrder(self.trading_account, stock, quantity, price)
            self.trading_account.place_safe_sell_order(market, limit_sell_order)

        elif len(self.trading_account.open_sell_orders) > 0:
            limit_sell_order = self.random.choice(self.trading_account.open_sell_orders)
            self.trading_account.cancel_safe_sell_order(market, limit_sell_order)

    def perform_buy_action(self, stock, market):

        bid_price = market.last_known_best_bid_price

        if bid_price is None:
            return

        bid_range = self.buy_ranges[stock]

        price = bid_range.random_price(bid_price)

        quantity = bid_range.random_quantity(self.trading_account.available_cash / price)

        if quantity > 0:
            limit_buy_order = LimitBuyOrder(self.trading_account, stock, quantity, price)

            self.trading_account.place_safe_buy_order(market, limit_buy_order)

        elif len(self.trading_account.open_buy_orders) > 0:
            limit_buy_order = self.random.choice(self.trading_account.open_buy_orders)
            self.trading_account.cancel_safe_buy_order(market, limit_buy_order)

    def __str__(self):
        return "trader"


