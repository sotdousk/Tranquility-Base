from dash import Dash, html, dcc, Input, Output, callback

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1("My Smart Home App."),
    html.Div(children='Set the alarm status.'),
    html.Br(),
    html.Div(className="row", children=[
        dcc.RadioItems(options=["Monitoring", "Disabled"], value="Disabled",
                       inline=False, id='my-input')
    ]),
    html.Br(),
    html.Div(id='my-output'),
])


@callback(
    Output(component_id='my-output', component_property='children'),
    Input(component_id='my-input', component_property='value')
)
def update_output_div(input_value):
    return f'Alarm is {input_value}'


if __name__ == "__main__":
    app.run(debug=True)
