# region imports
from AlgorithmImports import *

from universe import QQQConstituentsUniverseSelectionModel
from alpha import MomentumQuantilesAlphaModel
# endregion


class TacticalMomentumRankAlgorithm(QCAlgorithm):

    undesired_symbols_from_previous_deployment = []
    checked_symbols_from_previous_deployment = False

    def initialize(self):
        self.set_start_date(2023, 3, 1)  # Set Start Date
        self.set_end_date(2024, 3, 1) 
        self.set_cash(1_000_000)
        
        self.set_brokerage_model(BrokerageName.INTERACTIVE_BROKERS_BROKERAGE, AccountType.MARGIN)

        self.settings.minimum_order_margin_portfolio_percentage = 0

        self.universe_settings.data_normalization_mode = DataNormalizationMode.RAW
        self.add_universe_selection(QQQConstituentsUniverseSelectionModel(self.universe_settings))
        
        self.add_alpha(MomentumQuantilesAlphaModel(
            int(self.get_parameter("quantiles")),
            int(self.get_parameter("lookback_months"))
        ))

        self.settings.rebalance_portfolio_on_security_changes = False
        self.settings.rebalance_portfolio_on_insight_changes = False
        self.day = -1
        self.set_portfolio_construction(InsightWeightingPortfolioConstructionModel(self._rebalance_func))

        self.add_risk_management(NullRiskManagementModel())

        self.set_execution(ImmediateExecutionModel())

        self.set_warm_up(timedelta(7))

    def _rebalance_func(self, time):
        if self.day != self.time.day and not self.is_warming_up and self.current_slice.quote_bars.count > 0:
            self.day = self.time.day
            return time
        return None

    def on_data(self, data):
        # Exit positions that aren't backed by existing insights.
        # If you don't want this behavior, delete this method definition.
        if not self.is_warming_up and not self.checked_symbols_from_previous_deployment:
            for security_holding in self.portfolio.values():
                if not security_holding.invested:
                    continue
                symbol = security_holding.symbol
                if not self.insights.has_active_insights(symbol, self.utc_time):
                    self.undesired_symbols_from_previous_deployment.append(symbol)
            self.checked_symbols_from_previous_deployment = True
        
        for symbol in self.undesired_symbols_from_previous_deployment:
            if self.is_market_open(symbol):
                self.liquidate(symbol, tag="Holding from previous deployment that's no longer desired")
                self.undesired_symbols_from_previous_deployment.remove(symbol)
