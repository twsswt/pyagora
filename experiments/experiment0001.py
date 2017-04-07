from theatre_ag import SynchronizingClock, TaskQueueActor
from pagora import ContinuousOrderDrivenMarket, OrderBookClearingWorkflow, Stock, RandomTraderWorkflow, \
    TradeRange, LimitBuyOrder, LimitSellOrder, SafeTradingAccount

from random import Random

clock = SynchronizingClock(max_ticks=10000)

random = Random(1)

lemons = Stock('lemons')

market_clearer = TaskQueueActor('market', clock)

continuous_order_driven_market = ContinuousOrderDrivenMarket(lemons, clock)

order_book_clearing_workflow = \
    OrderBookClearingWorkflow(continuous_order_driven_market,
                              trade_pricer=lambda so, bo: bo.limit_price if bo.tick < so.tick else so.limit_price,
                              trade_check=lambda so, bo: bo.limit_price >= so.limit_price)

market_clearer.allocate_task(order_book_clearing_workflow.operate)

trading_account = SafeTradingAccount(
    name='trader',
    cash=1000,
    inventory={lemons: 100},
)

trader = TaskQueueActor('trader', clock)

trader_workflow = RandomTraderWorkflow(
    trading_account,
    random,
    sell_ranges={
        lemons: TradeRange(1, 3, -3, 3, random)
    },
    buy_ranges={
        lemons: TradeRange(1, 3, -1, 5, random)
    }
)

trader.allocate_task(trader_workflow.trade, args=[continuous_order_driven_market])


continuous_order_driven_market.record_limit_sell_order(LimitSellOrder(trading_account, lemons, 1, 100))
continuous_order_driven_market.record_limit_buy_order(LimitBuyOrder(trading_account, lemons, 1, 100))
order_book_clearing_workflow.clear()

clock.start()
trader.start()
market_clearer.start()

trader.wait_for_shutdown()
market_clearer.wait_for_shutdown()

print continuous_order_driven_market.average_trade_price

