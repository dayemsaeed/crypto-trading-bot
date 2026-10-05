"""Trend-following swing strategy: long-only spot, 4h candles.

Logic:
- Trade only with the major trend (EMA50 > EMA200).
- Confirm momentum with MACD (line above signal).
- Enter on RSI pullback turning back up (buy dips in uptrends, not tops).
- Skip dead markets (volume above its 20-period mean).
- Exit on trend break or overbought; ATR-informed stop + trailing stop.
"""

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy, IntParameter


class TrendFollowStrategy(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "4h"
    can_short = False

    # Take-profit ladder: let trends run early, tighten over time (keys = minutes).
    minimal_roi = {
        "0": 0.15,
        "1440": 0.08,
        "4320": 0.04,
        "8640": 0.02,
    }

    # Hard stop; roughly 2x typical 4h ATR on majors. Trailing stop does the fine work.
    stoploss = -0.08

    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.05
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    startup_candle_count = 200  # EMA200 needs history

    # Hyperopt-tunable entry knobs (defaults are the live values).
    rsi_entry = IntParameter(40, 55, default=50, space="buy")
    rsi_exit = IntParameter(70, 85, default=75, space="sell")

    # FreqUI chart overlays: EMAs on the price chart, RSI/MACD as subplots.
    plot_config = {
        "main_plot": {
            "ema50": {"color": "#3987e5"},
            "ema200": {"color": "#c98500"},
        },
        "subplots": {
            "RSI": {"rsi": {"color": "#9085e9"}},
            "MACD": {
                "macd": {"color": "#3987e5"},
                "macdsignal": {"color": "#e66767"},
            },
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]

        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["volume_mean20"] = dataframe["volume"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["ema50"] > dataframe["ema200"])  # uptrend
                & (dataframe["macd"] > dataframe["macdsignal"])  # momentum up
                & (dataframe["rsi"] < self.rsi_entry.value)  # pulled back
                & (dataframe["rsi"] > dataframe["rsi"].shift(1))  # turning up
                & (dataframe["volume"] > dataframe["volume_mean20"])  # market awake
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["ema50"] < dataframe["ema200"])  # trend broke
                | (dataframe["rsi"] > self.rsi_exit.value)  # overbought
            ),
            "exit_long",
        ] = 1
        return dataframe
