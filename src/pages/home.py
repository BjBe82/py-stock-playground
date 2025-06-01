import dash
import dash.dash_table.FormatTemplate as FormatTemplate
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, dash_table, dcc, html

from utils.stock_api import get_history

dash.register_page(__name__, path="/", redirect_from=["/home"], title="Home")


# FIXME split this up  in components + util functions for trading-signals ....

layout = html.Div(
    children=[
        html.H1("Stock Visualization Dashboard"),
        html.Label(
            "Please enter the stock ticker symbol (e.g., ^GSPC) and press enter to update the content: ",
            style={"marginRight": "10px"},
        ),
        dcc.Input(id="input", value="^GSPC", type="text", debounce=True),
        html.Div(id="content", className="mt-4"),
    ]
)


@callback(
    Output(component_id="content", component_property="children"),
    [Input(component_id="input", component_property="value")],
)
def update(ticker: str) -> html.Div:
    start_date = (pd.to_datetime("today") - pd.DateOffset(years=30)).strftime("%Y-%m-%d")
    end_date = pd.to_datetime("today").strftime("%Y-%m-%d")

    df = get_history(ticker, start_date, end_date)
    df["sma50"] = df["Close"].rolling(50, min_periods=50).mean()
    df["sma200"] = df["Close"].rolling(200, min_periods=200).mean()
    df.dropna(inplace=True)

    pd.options.mode.chained_assignment = None
    df.loc[df["sma50"] > df["sma200"], "sma50gtsma200"] = True
    df["sma50gtsma200"].fillna(False, inplace=True)
    df.loc[df["sma50"] < df["sma200"], "sma50ltsma200"] = True
    df["sma50ltsma200"].fillna(False, inplace=True)

    df["sma50gtsma200co"] = df["sma50gtsma200"].ne(df["sma50gtsma200"].shift())
    df.loc[df["sma50gtsma200"] == False, "sma50gtsma200co"] = False

    df["sma50ltsma200co"] = df["sma50ltsma200"].ne(df["sma50ltsma200"].shift())
    df.loc[df["sma50ltsma200"] == False, "sma50ltsma200co"] = False

    df["ema12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["ema26"] = df["Close"].ewm(span=26, adjust=False).mean()

    df["macd"] = df["ema12"] - df["ema26"]
    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    df.loc[df["macd"] > df["signal"], "macdgtsignal"] = True
    df["macdgtsignal"].fillna(False, inplace=True)

    df.loc[df["macd"] < df["signal"], "macdltsignal"] = True
    df["macdltsignal"].fillna(False, inplace=True)

    content = html.Div(
        children=[
            create_graph(df, ticker),
            create_stats_card(df),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "10px"},
    )

    return content


def create_stats_card(df: pd.DataFrame) -> dbc.Card:
    if df.empty:
        return None

    # calculate the all-time high (ATH) from the 'Close' column
    all_time_hight = df["Close"].max()

    # reverse the order to show the most recent dates first + only the last 60 days
    temp = df.reset_index()
    sub_df = (
        temp.iloc[::-1]
        .head(60)
        .loc[
            :,
            [
                "Date",
                "Close",
            ],
        ]
    )

    # calculate the current % drawdown from the ATH
    sub_df["Drawdown (%)"] = (sub_df["Close"] - all_time_hight) / all_time_hight
    sub_df["Date"] = sub_df["Date"].dt.date

    # calculate the maximum drawdown in the last 60 days
    max_drawdown_last_60_days = sub_df["Drawdown (%)"].min()

    return dbc.Card(
        dbc.CardBody(
            [
                html.H4("Data"),
                dbc.Table(
                    [
                        html.Tr([html.Td("ATH:"), html.Td(f"{all_time_hight:,.2f}")]),
                        html.Tr([html.Td("Max draw down last 60 days:"), html.Td(f"{max_drawdown_last_60_days:,.2%}")]),
                    ],
                    bordered=True,
                    color="primary",
                    hover=True,
                    style={"width": "300px"},
                ),
                html.P("Drawdown from ATH (last 60 days): "),
                dash_table.DataTable(
                    columns=[
                        {
                            "name": "Date",
                            "id": "Date",
                            "type": "datetime",
                        },
                        {
                            "name": "Close",
                            "id": "Close",
                            "type": "numeric",
                            "format": FormatTemplate.money(2),
                        },
                        {
                            "name": "Drawdown (%)",
                            "id": "Drawdown (%)",
                            "type": "numeric",
                            "format": FormatTemplate.percentage(2),
                        },
                    ],
                    data=sub_df.to_dict("records"),
                ),
            ]
        ),
    )


def create_graph(df: pd.DataFrame, ticker: str) -> dbc.Card:
    if df.empty:
        return html.Div(
            [
                dbc.Alert("No data available for the given ticker.", color="danger"),
            ]
        )

    # buy_signals = df[df["sma50gtsma200co"] is True]
    # sell_signals = df[df["sma50ltsma200co"] is True]
    buy_signals = df[(df["sma50gtsma200co"] == 1) & (df["macdgtsignal"] == 1)]
    sell_signals = df[(df["sma50ltsma200co"] == 1) & (df["macdltsignal"] == 1)]

    return dbc.Card(
        dbc.CardBody(
            [
                html.H4(f"Chart for '{ticker}'"),
                dcc.Graph(
                    id="stock-chart",
                    figure={
                        "data": [
                            {
                                "x": df.index,
                                "y": df["Close"],
                                "type": "line",
                                "name": ticker,
                                "line": {"width": 1, "color": "black"},
                            },
                            {
                                "x": df.index,
                                "y": df["sma50"],
                                "type": "line",
                                "name": "SMA 50",
                                "line": {"width": 1, "color": "blue"},
                            },
                            {
                                "x": df.index,
                                "y": df["sma200"],
                                "type": "line",
                                "name": "SMA 200",
                                "line": {"width": 1, "color": "green"},
                            },
                            {
                                "x": buy_signals.index,
                                "y": buy_signals["Close"],
                                "mode": "markers",
                                "name": "Buy Signal",
                                "marker": {"color": "green", "size": 10, "symbol": "star"},
                            },
                            {
                                "x": sell_signals.index,
                                "y": sell_signals["Close"],
                                "mode": "markers",
                                "name": "Sell Signal",
                                "marker": {"color": "red", "size": 10, "symbol": "star"},
                            },
                        ],
                        "layout": {"title": ticker},
                    },
                ),
            ]
        ),
    )
