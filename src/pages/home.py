import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, callback, dash_table, dcc, html

from utils.stock_api import get_history

dash.register_page(__name__, path="/", redirect_from=["/home"], title="Home")


# FIXME split this up  in components ....

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
    content = html.Div(
        children=[
            create_graph(df, ticker),
            dbc.Col(
                [
                    create_stats_card(df),
                ],
                className="mt-4",
            ),
        ],
    )

    return content


def create_stats_card(df: pd.DataFrame) -> dbc.Card:
    if df.empty:
        return None

    # calculate the all-time high (ATH) from the 'Close' column
    all_time_hight = df["Close"].max()

    # calculate the current % drawdown from the ATH
    df["PctDrawdownFromHigh"] = ((df["Close"] - all_time_hight) / all_time_hight) * 100

    df.reset_index(inplace=True)
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4("Data"),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div("ATH: "),
                            width="auto",
                        ),
                        dbc.Col(
                            html.Div(f"{all_time_hight:,.2f}"),
                            width="auto",
                        ),
                    ]
                ),
                html.P("Drawdown from ATH (last 60 days): "),
                dash_table.DataTable(
                    df.iloc[::-1]  # reverse the order to show the most recent dates first
                    .head(60)  # show only the last 60 days
                    .loc[
                        :,
                        [
                            "Date",
                            "Close",
                            "PctDrawdownFromHigh",
                        ],
                    ]
                    .to_dict("records")
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

    return dbc.Card(
        dbc.CardBody(
            [
                html.H4(f"Chart for '{ticker}'"),
                dcc.Graph(
                    id="stock-chart",
                    figure={
                        "data": [{"x": df.index, "y": df["Close"], "type": "line", "name": ticker}],
                        "layout": {"title": ticker},
                    },
                ),
            ]
        ),
    )
