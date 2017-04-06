import unittest

from mock import Mock

from theatre_ag import SynchronizingClock
from theatre_market.system import LimitBuyOrderBook, LimitBuyOrder, Stock


class LimitBuyOrderBookTestCase(unittest.TestCase):

    def setUp(self):
        self.lemons = Stock('lemons')
        self.clock = Mock(spec=SynchronizingClock)
        self.limit_buy_order_book = LimitBuyOrderBook(self.clock)

    def test_ordering(self):
        self.clock.current_tick = 1
        buy_order_1 = LimitBuyOrder(None, self.lemons, 1, 30)

        self.limit_buy_order_book.record_order(buy_order_1)

        self.clock.current_tick = 2
        buy_order_2 = LimitBuyOrder(None, self.lemons, 1, 40)

        self.limit_buy_order_book.record_order(buy_order_2)

        self.assertEquals(self.limit_buy_order_book.best_price, 40)

    def test_remove(self):
        self.clock.current_tick = 1
        buy_order_1 = LimitBuyOrder(None, self.lemons, 1, 30)

        self.limit_buy_order_book.record_order(buy_order_1)

        self.clock.current_tick = 2
        buy_order_2 = LimitBuyOrder(None, self.lemons, 1, 40)

        self.limit_buy_order_book.record_order(buy_order_2)
        self.limit_buy_order_book.cancel_order(buy_order_1)

        self.assertEquals(1, len(self.limit_buy_order_book.open_orders))

if __name__ == '__main__':
    unittest.main()
