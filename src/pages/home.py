import dash
import dash.dash_table.FormatTemplate as FormatTemplate
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, dash_table, dcc, html

from utils.constants import (
    CLOSE,
    DATE,
    DRAWDOWN,
    MACD_GT_SIGNAL,
    MACD_LT_SIGNAL,
    SMA_50,
    SMA_50_GT_SMA_200_CO,
    SMA_50_LT_SMA_200_CO,
    SMA_200,
)
from utils.stock_api import get_history
from utils.trading_signals import add_indicators

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
    add_indicators(df)

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
    all_time_hight = df[CLOSE].max()

    # reverse the order to show the most recent dates first + only the last 60 days
    temp = df.reset_index()
    sub_df = (
        temp.iloc[::-1]
        .head(60)
        .loc[
            :,
            [
                DATE,
                CLOSE,
            ],
        ]
    )

    # calculate the current % drawdown from the ATH
    sub_df[DRAWDOWN] = (sub_df[CLOSE] - all_time_hight) / all_time_hight
    sub_df[DATE] = sub_df[DATE].dt.date

    # calculate the maximum drawdown in the last 60 days
    max_drawdown_last_60_days = sub_df[DRAWDOWN].min()

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
                            "name": DATE,
                            "id": DATE,
                            "type": "datetime",
                        },
                        {
                            "name": CLOSE,
                            "id": CLOSE,
                            "type": "numeric",
                            "format": FormatTemplate.money(2),
                        },
                        {
                            "name": DRAWDOWN,
                            "id": DRAWDOWN,
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

    # buy_signals = df[df[SMA_50_GT_SMA_200_CO] is True]
    # sell_signals = df[df[SMA_50_LT_SMA_200_CO] is True]
    buy_signals = df[(df[SMA_50_GT_SMA_200_CO] == 1) & (df[MACD_GT_SIGNAL] == 1)]
    sell_signals = df[(df[SMA_50_LT_SMA_200_CO] == 1) & (df[MACD_LT_SIGNAL] == 1)]

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
                                "y": df[CLOSE],
                                "type": "line",
                                "name": ticker,
                                "line": {"width": 1, "color": "black"},
                            },
                            {
                                "x": df.index,
                                "y": df[SMA_50],
                                "type": "line",
                                "name": "SMA 50",
                                "line": {"width": 1, "color": "blue"},
                            },
                            {
                                "x": df.index,
                                "y": df[SMA_200],
                                "type": "line",
                                "name": "SMA 200",
                                "line": {"width": 1, "color": "green"},
                            },
                            {
                                "x": buy_signals.index,
                                "y": buy_signals[CLOSE],
                                "mode": "markers",
                                "name": "Buy Signal",
                                "marker": {"color": "green", "size": 15, "symbol": "triangle-up"},
                            },
                            {
                                "x": sell_signals.index,
                                "y": sell_signals[CLOSE],
                                "mode": "markers",
                                "name": "Sell Signal",
                                "marker": {"color": "red", "size": 10, "symbol": "triangle-down"},
                            },
                        ],
                        "layout": {"title": ticker},
                    },
                ),
            ]
        ),
    )
