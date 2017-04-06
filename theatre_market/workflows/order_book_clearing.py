from theatre_market.system import Trade, TradeExecutionException
from theatre_ag import default_cost


class OrderBookClearingWorkflow(object):

    def __init__(self, market, trade_pricer, trade_check):
        self.market = market

        self.trade_pricer = trade_pricer
        self.trade_check = trade_check

    def operate(self):
        while True:
            self.clear()

    @default_cost(1)
    def clear(self):
        sell_order = self._sell_order_book.best_order
        buy_order = self._buy_order_book.best_order

        while sell_order is not None and buy_order is not None and self.trade_check(sell_order, buy_order):
            price = self.trade_pricer(sell_order, buy_order)
            self._execute_trade(sell_order, buy_order, price)
            sell_order = self._sell_order_book.best_order
            buy_order = self._buy_order_book.best_order

    def _execute_trade(self, sell_order, buy_order, price):
        quantity = self._calculate_trade_quantity(sell_order, buy_order)

        trade = Trade(self.market.stock, quantity, price, sell_order, buy_order)

        try:
            trade.execute(self.market.clock)
            self.market.trade_history.append(trade)

        except TradeExecutionException as e:
            print e.message
            if e.culprit == sell_order.trader:
                self._sell_order_book.cancel_order(sell_order)
            elif e.culprit == buy_order.trader:
                self._buy_order_book.cancel_order(buy_order)

    def _calculate_trade_quantity(self, sell_order, buy_order):
        return min(sell_order.remaining_quantity, buy_order.remaining_quantity)

    @property
    def _sell_order_book(self):
        return self.market.limit_sell_order_book

    @property
    def _buy_order_book(self):
        return self.market.limit_buy_order_book
