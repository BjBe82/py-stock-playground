import dash_bootstrap_components as dbc
from dash import html

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.I(
                className="fa-solid fa-solid fa-magnifying-glass-chart me-2",
                style={"color": "white", "fontSize": "1.5rem"},
            ),
            dbc.Nav(
                [
                    dbc.NavItem(dbc.NavLink("Home", href="/")),
                    dbc.NavItem(dbc.NavLink("Other Page", href="/other-page")),
                ],
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True,
)
