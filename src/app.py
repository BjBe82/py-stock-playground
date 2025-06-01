import dash
import dash_bootstrap_components as dbc
from dash import html
from flask import Flask

from components import footer, navbar
from utils.settings import APP_DEBUG, APP_HOST, APP_PORT, DEV_TOOLS_PROPS_CHECK

server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,  # turn on Dash pages
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    title="Py Stock Playground",
)


def serve_layout():
    """
    Serve the layout of the app, which includes the navbar, page content, and footer.
    This function is used to create a consistent layout across all pages of the app.
    """
    return html.Div(
        [
            navbar,
            dbc.Container(
                dash.page_container,
                style={
                    "flexGrow": 1,
                },
            ),
            footer,
        ],
        style={"minHeight": "100vh", "display": "flex", "flexDirection": "column"},
    )


app.layout = serve_layout()
server = app.server

if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, debug=APP_DEBUG, dev_tools_props_check=DEV_TOOLS_PROPS_CHECK)
