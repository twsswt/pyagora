from sortedcontainers import SortedSet


class Stock(object):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return str(self.name)


class Market(object):
    pass


class TradeExecutionException(Exception):
    def __init__(self, message, trade, culprit):
        super(TradeExecutionException, self).__init__(message)
        self.trade = trade
        self.culprit = culprit


class Trade(object):

    def __init__(self, stock, quantity, price, sell_order, buy_order):
        self.stock = stock
        self.quantity = quantity
        self.price = price
        self.sell_order = sell_order
        self.buy_order = buy_order

        self.tick = None

    @property
    def buyer(self):
        return self.buy_order.trader

    @property
    def seller(self):
        return self.sell_order.trader

    def execute(self, clock):
        self.tick = clock.current_tick

        self.sell_order.satisfy_trade(self)
        try:
            self.buy_order.satisfy_trade(self)
        except TradeExecutionException as e:
            self.sell_order.roll_back_trade(self)
            raise e

    def __str__(self):
        return "%s->(%s:%d:%dp)->%s" % (self.seller, self.stock, self.quantity, self.price, self.buyer)

    def __repr__(self):
        return "%s->(%s:%d:%dp)->%s" % (self.seller, self.stock, self.quantity, self.price, self.buyer)


class Order(object):

    def __init__(self, trader, stock, initial_quantity):
        self.trader = trader
        self.stock = stock
        self.initial_quantity = initial_quantity

        self.trade_history = list()

    @property
    def remaining_quantity(self):
        return self.initial_quantity - sum(map(lambda t: t.quantity,  self.trade_history))

    @property
    def filled(self):
        return self.remaining_quantity <= 0


class BuyOrder(Order):

    def __init__(self, trader, stock, quantity):
        super(BuyOrder, self).__init__(trader, stock, quantity)

    def satisfy_trade(self, trade):
        self.trader.buy_stock(trade)
        self.trade_history.append(trade)

    def roll_back_trade(self, trade):
        if trade in self.trade_history:
            self.trade_history.remove(trade)
            self.trader.sell_stock(trade)


class SellOrder(Order):

    def __init__(self, trader, stock, quantity):
        super(SellOrder, self).__init__(trader, stock, quantity)

    def satisfy_trade(self, trade):
        self.trader.sell_stock(trade)
        self.trade_history.append(trade)

    def roll_back_trade(self, trade):
        if trade in self.trade_history:
            self.trade_history.remove(trade)
            self.trader.buy_stock(trade)


class LimitOrder(Order):

    def __init__(self, trader, stock, quantity, limit_price):
        super(LimitOrder, self).__init__(trader, stock, quantity)
        self.limit_price = limit_price


class LimitBuyOrder(BuyOrder, LimitOrder):

    def __init__(self, trader, stock, quantity, limit_price):
        LimitOrder.__init__(self, trader, stock, quantity, limit_price)

    def __repr__(self):
        return "LBO[%s, %s, %d, %d]" % (self.trader, self.stock, self.remaining_quantity, self.limit_price)

    def __str__(self):
        return "LBO[%s, %s, %d, %d]" % (self.trader, self.stock, self.remaining_quantity, self.limit_price)


class LimitSellOrder(SellOrder, LimitOrder):

    def __init__(self, trader, stock, quantity, limit_price):
        LimitOrder.__init__(self, trader, stock, quantity, limit_price)

    def __repr__(self):
        return "LSO[%s, %s, %d, %d]" % (self.trader, self.stock, self.remaining_quantity, self.limit_price)

    def __str__(self):
        return "LSO[%s, %s, %d, %d]" % (self.trader, self.stock, self.remaining_quantity, self.limit_price)


class OrderBook(object):

    def __init__(self, clock, sort_key):
        self.clock = clock
        self._received_orders = SortedSet(key=sort_key)

    def record_order(self, order):
        order.tick = self.clock.current_tick
        self._received_orders.add(order)

    def cancel_order(self, order):
        order.tick = None
        self._received_orders.remove(order)

    @property
    def open_orders(self):
        return filter(lambda o: not o.filled, self._received_orders)

    @property
    def best_order(self):
        cache = self.open_orders
        return cache[0] if len(cache) > 0 else None

    @property
    def best_price(self):
        cache = self.best_order
        return cache.limit_price if cache is not None else None

    def __str__(self):
        return str(self.open_orders)


class LimitSellOrderBook(OrderBook):

    def __init__(self, clock):
        super(LimitSellOrderBook, self).__init__(clock, sort_key=lambda o: o.limit_price)


class LimitBuyOrderBook(OrderBook):

    def __init__(self, clock):
        super(LimitBuyOrderBook, self).__init__(clock, sort_key=lambda o: -o.limit_price)


class ContinuousOrderDrivenMarket(object):

    def __init__(self, stock, clock):
        self.stock = stock
        self.clock = clock

        self.trade_history = list()

        self.limit_sell_order_book = LimitSellOrderBook(clock)
        self.limit_buy_order_book = LimitBuyOrderBook(clock)

    def record_limit_buy_order(self, limit_buy_order):
        self.limit_buy_order_book.record_order(limit_buy_order)

    def record_limit_sell_order(self, limit_sell_order):
        self.limit_sell_order_book.record_order(limit_sell_order)

    def cancel_limit_sell_order(self, sell_order):
        self.limit_sell_order_book.cancel_order(sell_order)

    def cancel_limit_buy_order(self, buy_order):
        self.limit_buy_order_book.cancel_order(buy_order)

    @property
    def last_known_best_bid_price(self):

        current_best_bid = self.limit_buy_order_book.best_price

        if current_best_bid is None:
            return self.last_traded_price
        else:
            return current_best_bid

    @property
    def last_known_best_offer_price(self):

        current_best_bid = self.limit_sell_order_book.best_price

        if current_best_bid is None:
            return self.last_traded_price
        else:
            return current_best_bid

    @property
    def average_trade_price(self):
        if len(self.trade_history) > 0:
            return sum(map(lambda t: t.price, self.trade_history)) / len(self.trade_history)
        else:
            return None

    @property
    def last_traded_price(self):
        return self.trade_history[-1].price if len(self.trade_history) > 0 else None

    def __str__(self):
        return "market for %s" % self.stock.name
