import pandas as pd

from utils.constants import (
    CLOSE,
    EMA_12,
    EMA_26,
    MACD,
    MACD_GT_SIGNAL,
    MACD_LT_SIGNAL,
    MACD_SIGNAL,
    SMA_50,
    SMA_200,
)


def add_indicators(df: pd.DataFrame) -> None:
    df[SMA_50] = df[CLOSE].rolling(50, min_periods=50).mean()
    df[SMA_200] = df[CLOSE].rolling(200, min_periods=200).mean()
    df.dropna(inplace=True)

    pd.options.mode.chained_assignment = None
    # df.loc[df[SMA_50] > df[SMA_200], SMA_50_GT_SMA_200_CO] = True
    # df[SMA_50_GT_SMA_200_CO].fillna(False, inplace=True)
    # df.loc[df[SMA_50] < df[SMA_200], SMA_50_LT_SMA_200_CO] = True
    # df[SMA_50_LT_SMA_200_CO].fillna(False, inplace=True)

    # df[SMA_50_GT_SMA_200_CO] = df[SMA_50_GT_SMA_200_CO].ne(df[SMA_50_GT_SMA_200_CO].shift())
    # df.loc[df[SMA_50_GT_SMA_200_CO] == False, SMA_50_GT_SMA_200_CO] = False

    # df[SMA_50_LT_SMA_200_CO] = df[SMA_50_LT_SMA_200_CO].ne(df[SMA_50_LT_SMA_200_CO].shift())
    # df.loc[df[SMA_50_LT_SMA_200_CO] == False, SMA_50_LT_SMA_200_CO] = False

    # FIXME why is the code above not working?
    df.loc[df["sma50"] > df["sma200"], "sma50gtsma200"] = True
    df["sma50gtsma200"].fillna(False, inplace=True)
    df.loc[df["sma50"] < df["sma200"], "sma50ltsma200"] = True
    df["sma50ltsma200"].fillna(False, inplace=True)

    df["sma50gtsma200co"] = df.sma50gtsma200.ne(df.sma50gtsma200.shift())
    df.loc[df["sma50gtsma200"] == False, "sma50gtsma200co"] = False

    df["sma50ltsma200co"] = df.sma50ltsma200.ne(df.sma50ltsma200.shift())
    df.loc[df["sma50ltsma200"] == False, "sma50ltsma200co"] = False

    df[EMA_12] = df[CLOSE].ewm(span=12, adjust=False).mean()
    df[EMA_26] = df[CLOSE].ewm(span=26, adjust=False).mean()

    df[MACD] = df[EMA_12] - df[EMA_26]
    df[MACD_SIGNAL] = df[MACD].ewm(span=9, adjust=False).mean()

    df.loc[df[MACD] > df[MACD_SIGNAL], MACD_GT_SIGNAL] = True
    df[MACD_GT_SIGNAL].fillna(False, inplace=True)

    df.loc[df[MACD] < df[MACD_SIGNAL], MACD_LT_SIGNAL] = True
    df[MACD_LT_SIGNAL].fillna(False, inplace=True)
