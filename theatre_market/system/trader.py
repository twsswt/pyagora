from theatre_market.system import TradeExecutionException


class LimitOrderException(Exception):
    pass


class TradingAccount(object):

    def __init__(self, name, cash, inventory):
        self.name = name
        self.cash = cash
        self.inventory = dict(inventory)
        self.sell_trades = list()
        self.buy_trades = list()

    def sell_stock(self, trade):
        if trade.seller is not self:
            raise TradeExecutionException("Trader is not the same", trade, self)

        current_quantity = self.inventory.get(trade.stock, 0)

        if current_quantity < trade.quantity:
            raise TradeExecutionException("Seller cannot satisfy trade - insufficient quantity", trade, self)
        else:
            self.inventory[trade.stock] = current_quantity - trade.quantity
            self.cash += trade.price * trade.quantity
            self.sell_trades.append(trade)

    def buy_stock(self, trade):

        if trade.buyer is not self:
            raise TradeExecutionException("Trader is not the same", trade, self)

        total_price = trade.price * trade.quantity

        if total_price > self.cash:
            raise TradeExecutionException("Buyer cannot satisfy trade - insufficient cash.", trade, self)
        else:
            current_quantity = self.inventory.get(trade.stock, 0)
            self.inventory[trade.stock] = current_quantity + trade.quantity
            self.cash -= total_price
            self.buy_trades.append(trade)

    def __str__(self):
        return str(self.name)


class SafeTradingAccount(TradingAccount):

    def __init__(self, name, cash, inventory):
        super(SafeTradingAccount, self).__init__(name, cash, inventory)
        self.open_sell_orders = list()
        self.open_buy_orders = list()

    def place_safe_sell_order(self, market, limit_sell_order):
        if limit_sell_order.remaining_quantity <= self.available_inventory[limit_sell_order.stock]:
            self.open_sell_orders.append(limit_sell_order)
            market.record_limit_sell_order(limit_sell_order)
        else:
            raise LimitOrderException()

    def place_safe_buy_order(self, market, limit_buy_order):
        if limit_buy_order.limit_price * limit_buy_order.remaining_quantity <= self.available_cash:
            self.open_buy_orders.append(limit_buy_order)
            market.record_limit_buy_order(limit_buy_order)
        else:
            raise LimitOrderException()

    def cancel_safe_buy_order(self, market, limit_buy_order):
        if limit_buy_order in self.open_buy_orders:
            self.open_buy_orders.remove(limit_buy_order)
            market.cancel_limit_buy_order(limit_buy_order)

    def cancel_safe_sell_order(self, market, limit_sell_order):
        if limit_sell_order in self.open_sell_orders:
            self.open_sell_orders.remove(limit_sell_order)
            market.cancel_limit_sell_order(limit_sell_order)

    @property
    def available_cash(self):
        return self.cash - sum(map(lambda bo: bo.limit_price * bo.remaining_quantity, self.open_buy_orders))

    @property
    def available_inventory(self):
        result = dict()
        for stock in self.inventory.keys():
            quantity = self.inventory[stock]
            committed_quantity = \
                sum(map(lambda so: so.remaining_quantity, filter(lambda so: so.stock == stock, self.open_sell_orders)))
            result[stock] = quantity - committed_quantity

        return result
