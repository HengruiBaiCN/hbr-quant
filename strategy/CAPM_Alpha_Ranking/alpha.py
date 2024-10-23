from AlgorithmImports import *

class CAPMAlphaRankingModel(AlphaModel):

    def __init__(self, benchmark, lookback):
        self.benchmark = benchmark
        self.lookback = lookback
        self.symbols = []
        self.month = -1

    def update(self, algorithm, data):
        if algorithm.time.month == self.month: return []
        self.month = algorithm.time.month

        # Fetch the historical data and calculate the returns
        # to perform the linear regression
        returns = algorithm.history(
            self.symbols + [self.benchmark], 
            self.lookback,
            Resolution.DAILY).close.unstack(level=0).pct_change().iloc[1:].fillna(0)
            
        return [
            Insight.price(symbol, Expiry.END_OF_MONTH, InsightDirection.UP) for symbol in self.select_symbols(algorithm, returns)
        ]

    def select_symbols(self, algorithm, all_returns):
        '''Select symbols with the highest intercept/alpha to the benchmark
        '''
        alphas = dict()

        # Get the benchmark returns
        benchmark = all_returns[self.benchmark]

        # Conducts linear regression for each symbol and save the intercept/alpha
        for symbol in self.symbols:
            if not str(symbol.id) in all_returns.columns:
                algorithm.log(f'{symbol} not found in the historical data request')
                continue
            
            # Get the security returns
            returns = all_returns[symbol]
            bla = np.vstack([benchmark, np.ones(len(returns))]).T

            # Simple linear regression function in Numpy
            result = np.linalg.lstsq(bla , returns)
            alphas[symbol] = result[0][1]

        # Select symbols with the highest intercept/alpha to the benchmark
        selected = sorted(alphas.items(), key=lambda x: x[1], reverse=True)[:2]
        return [x[0] for x in selected]

    def on_securities_changed(self, algorithm, changes):
        for added in changes.added_securities:
            self.symbols.append(added.symbol)

        for removed in changes.removed_securities:
            symbol = removed.symbol
            if symbol in self.symbols:
                self.symbols.remove(symbol)