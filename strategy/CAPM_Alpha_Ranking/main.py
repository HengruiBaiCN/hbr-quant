#region imports
from AlgorithmImports import *
from universe import Dow30UniverseSelection
from alpha import CAPMAlphaRankingModel
#endregion

class CapmAlphaRankingAlgorithm(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2023, 3, 1)
        self.set_end_date(2024, 3, 1)
        self.set_cash(100000)            # Set Strategy Cash

        # Set number days to trace back
        lookback = self.get_parameter("lookback", 21)
        
        self.set_brokerage_model(BrokerageName.INTERACTIVE_BROKERS_BROKERAGE, AccountType.MARGIN)

        # Dow 30 companies
        dia = self.add_equity("DIA",
            resolution = self.universe_settings.resolution,
            data_normalization_mode = self.universe_settings.data_normalization_mode).symbol
        self.set_benchmark(dia)
        
        self.set_universe_selection(Dow30UniverseSelection(dia, self.universe_settings))
        self.add_alpha(CAPMAlphaRankingModel(dia, lookback))
        self.set_portfolio_construction(EqualWeightingPortfolioConstructionModel(Expiry.END_OF_MONTH))