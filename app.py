from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

app = Dash()

app.layout = [
    html.H1(children='TP1 - ALG2', style={'textAlign':'center'}),
]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)