from utils import *

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

import warnings
import base64
warnings.filterwarnings('ignore')

df = pd.read_csv(join(current_dir, 'olympic_medalists.csv'))
years = sorted(df.Year.astype(int).unique().tolist())

app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}], 
            title='Olympic Medalists',
            external_stylesheets=[dbc.themes.BOOTSTRAP]
            )

col_to_show = ['Year', 'Sport_cat', 'Sport', 'Medal', 'Player', 'Gender', 'Country', 'Age', 'DateofBirth', 'SportDetails']
df_display = df.copy()
df_display.sort_values(by=['Age'], ascending=False, inplace=True)
# df_display['Year'] = df_display['Year'].astype(str)

encoded_image = base64.b64encode(open(join(current_dir, 'modal.png'), 'rb').read())
slider_marks = {i:str(i) for i in range(age_min, age_max,5) }
slider_marks[age_max] = str(age_max)+'+'
app.layout = html.Div([
    html.H2(id='title', children='Olympic Medalists Age Distribution By Sports (Summer)', style={"margin-bottom": 20,"margin-left": '20%', "text-align": 'middle'} ),
    html.Div([
        dbc.Modal(id="modal", is_open=True, children=[
                dbc.ModalHeader("You are never too old for a breakthrough. Age is just a number.",
                                style={"margin-bottom":3, 'padding':5}),
                dbc.ModalBody("This project is inspired by below sportsmanship in Tokyo Olympics.", 
                                style={"margin-bottom":0, 'padding':5}),
                dbc.ModalBody(html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode())),
                                style={"margin-top":5, 'padding':5}),
            ], size='lg', style={'width':800}),
        html.Div(children=[html.Div('Age Range: '), html.Div(id='ageRange-text')], 
                style={'width': "15%", "text-align": "right"}),
        html.Div(children= dcc.RangeSlider(id='ageRange',min=age_min,max=age_max,step=1,value=[30, age_max], 
                                            marks=slider_marks),
                style={'width': "30%"}),
        html.Div(children = html.Div('Countries: '),
                style={'width': "10", "text-align": "right", 'margin-right':5}),
        html.Div(dcc.Dropdown(id='countryDropdown', 
                                        options=[{'label' : country, 'value': country} for country in ['All']+sorted(df_display.Country.unique())], 
                                        placeholder="Select interested countries(default to All)", value = ['All'], multi=True),
                style={'width': "30%"}),
        html.Div(children=dcc.Checklist(id='show-bubble-text',
            options=[{'label': 'Text for Bubble', 'value': 'True'},],
            value=['True'],
            labelStyle={
                # 'display': 'inline-block',
                 'text-align': 'middle'}),
                style={'width': 70,  "margin-left": "2%",  "margin-right": "1%"}),
        html.Button('Refresh', id='refresh', n_clicks=0, className="mr-1 mt-1 btn btn-primary",
            style={ "margin-left": "2%", 'height':50,  "margin-bottom": "3%"}
            )
    ],style={'columnCount': 6, 'height':50, 'display':'flex'}),

    dcc.Loading(
            id="loading", type="circle", fullscreen=False, 
            # parent_className='loading_wrapper', 
            children=[ html.Div(id='main-text'), 
                        dcc.Graph(id='main-fig', )],
        ),
    html.Div([html.A('Download More Metadata from '), 
            html.A("Github", href='https://github.com/xudong-z/olympic_medalists', target="_blank"),
            html.A(' or Contact '), 
            html.A("Me", href='xudong.zhg@gmail.com', target="_blank")],
            style={ "float": "right", 'margin-right':'2%', 'margin-top':0, 'margin-bottom':0}),
    html.Div(dash_table.DataTable(id='main-table',
                        columns=[{"name": i, "id": i, "deletable": False, "selectable": False} for i in df_display.columns if i in col_to_show],
                        data=df_display.to_dict('records'),
                        editable=False, row_deletable=False, row_selectable=False,
                        filter_action="custom", filter_query='',
                        sort_action="native", sort_mode="multi",
                        column_selectable="single", 
                        page_action="native",
                        page_current= 0, page_size= 10,
                        style_header={'backgroundColor': 'rgb(230, 230, 230)',  'fontWeight': 'bold'},
                        css=[
                            {"selector": "input", "rule": f"color:{THEME['font_color']}"},
                            {"selector": "tr:hover", "rule": "background-color:transparent"},
                            {"selector": ".dash-table-tooltip", "rule": "color:black"},
                        ],
                        style_cell={"backgroundColor": "transparent", "fontFamily": THEME["font"]},
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            },
                            {
                                "if": {"state": "active"},
                                "backgroundColor": THEME["selected"],
                                "border": "1px solid " + THEME["primary"],
                                "color": THEME["font_color"],
                            },
                            {
                                "if": {"state": "selected"},
                                "backgroundColor": THEME["selected"],
                                "border": "1px solid" + THEME["secondary"],
                                "color": THEME["font_color"],
                            },
                        ],
                        export_format="csv",
                        ),
            style={'margin-left':'2%', 'margin-right':'2%'}
            )
    ]
)

@app.callback(
    Output('ageRange-text', 'children'),
    Input('ageRange', 'value'))
def update_ageRange(value):
    max = str(value[1])+'+' if value[1]==age_max else str(value[1])
    return f'({value[0]}-{max}) selected'
    

fig = get_default_fig(years)
@app.callback(
             Output('main-fig', 'figure'), 
            # Output('main-table', 'data'),
            # Output('main-text', 'children'),
    [Input('refresh', 'n_clicks')], [State('ageRange', 'value')], [State('countryDropdown', 'value')], [State('show-bubble-text', 'value')])
def main_button_callback(n_clicks, age, countries, show):
    s_age = '-'.join([str(v) for v in age])
    s_cty = '-'.join(countries)
    print(s_age, s_cty, show)
    fig['data'], fig['frames']=None, None
    df_bub = get_dfs_bub(df, age, countries, years)
    show_text = True if len(show)>0 else False
    fig_dict = get_fig_data(df_bub, years, show_text=show_text)
    for d in fig_dict['data']:
        fig.add_trace(go.Scatter(d))
    fig['frames']=fig_dict['frames']

    return fig


operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]
def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3

@app.callback(
    Output('main-table', "data"),
    Input('main-table', "filter_query"))
def update_table(filter):
    filtering_expressions = filter.split(' && ')
    dff = df
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(f'(?i){filter_value}')]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    return dff.to_dict('records')

app.run_server(debug=False, use_reloader=True, port=8055)
