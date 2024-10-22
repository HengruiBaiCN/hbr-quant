#region imports
from AlgorithmImports import *
#endregion


class MomentumQuantilesAlphaModel(AlphaModel):

    def __init__(self, quantiles, lookback_months):
        self.quantiles = quantiles
        self.lookback_months = lookback_months
        self.securities_list = []
        self.day = -1

    def update(self, algorithm: QCAlgorithm, data: Slice) -> List[Insight]:
        # Reset indicators when corporate actions occur
        for symbol in set(data.splits.keys() + data.dividends.keys()):
            security = algorithm.securities[symbol]
            if security in self.securities_list:
                security.indicator.reset()
                algorithm.subscription_manager.remove_consolidator(security.symbol, security.consolidator)
                self._register_indicator(algorithm, security)

                history = algorithm.history[TradeBar](security.symbol, (security.indicator.warm_up_period+1) * 30, Resolution.DAILY, data_normalization_mode=DataNormalizationMode.SCALED_RAW)
                for bar in history:
                    security.consolidator.update(bar)
        
        # Only emit insights when there is quote data, not when a corporate action occurs (at midnight)
        if data.quote_bars.count == 0:
            return []
        
        # Only emit insights once per day
        if self.day == algorithm.time.day:
            return []
        self.day = algorithm.time.day

        # Get the momentum of each asset in the universe
        momentum_by_symbol = {security.symbol : security.indicator.current.value 
            for security in self.securities_list if security.symbol in data.quote_bars and security.indicator.is_ready}
                
        # Determine how many assets to hold in the portfolio
        quantile_size = int(len(momentum_by_symbol)/self.quantiles)
        if quantile_size == 0:
            return []

        # Create insights to long the assets in the universe with the greatest momentum
        weight = 1 / quantile_size
        insights = []
        for symbol, _ in sorted(momentum_by_symbol.items(), key=lambda x: x[1], reverse=True)[:quantile_size]:
            insights.append(Insight.price(symbol, Expiry.END_OF_DAY, InsightDirection.UP, weight=weight))

        return insights

    def on_securities_changed(self, algorithm: QCAlgorithm, changes: SecurityChanges) -> None:
        # Create and register indicator for each security in the universe
        security_by_symbol = {}
        for security in changes.added_securities:
            security_by_symbol[security.symbol] = security
            
            # Create an indicator that automatically updates each month
            security.indicator = MomentumPercent(self.lookback_months)
            self._register_indicator(algorithm, security)

            self.securities_list.append(security)
        
        # Warm up the indicators of newly-added stocks
        if security_by_symbol:
            history = algorithm.history[TradeBar](list(security_by_symbol.keys()), (self.lookback_months+1) * 30, Resolution.DAILY, data_normalization_mode=DataNormalizationMode.SCALED_RAW)
            for trade_bars in history:
                for bar in trade_bars.values():
                    security_by_symbol[bar.symbol].consolidator.update(bar)

        # Stop updating consolidator when the security is removed from the universe
        for security in changes.removed_securities:
            if security in self.securities_list:
                algorithm.subscription_manager.remove_consolidator(security.symbol, security.consolidator)
                self.securities_list.remove(security)


    def _register_indicator(self, algorithm, security):
        # Update the indicator with monthly bars
        security.consolidator = TradeBarConsolidator(Calendar.MONTHLY)
        algorithm.subscription_manager.add_consolidator(security.symbol, security.consolidator)
        algorithm.register_indicator(security.symbol, security.indicator, security.consolidator)

