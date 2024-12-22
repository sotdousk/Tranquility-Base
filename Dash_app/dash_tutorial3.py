from dash import Dash, dcc, html, Input, Output, callback

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Input(id='input-1', type="text", value="Montréal"),
    dcc.Input(id='input-2', type="text", value="Canada"),
    html.Div(id="number-output"),
])


@callback(
    Output("number-output", "children"),
    Input("input-1", "value"),
    Input("input-2", "value"),
)
def update_output(input1, input2):
    return f'Input 1 is {input1} and Input 2 is {input2}'


if __name__ == "__main__":
    app.run(debug=True)
