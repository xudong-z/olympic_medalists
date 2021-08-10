from collections import defaultdict
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

import json
import pandas as pd
import numpy as np
from os.path import dirname, join

current_dir = dirname(__file__)
duration = 2500
age_min = 10
age_max = 40
range_balance = [0.2, 5]
range_xaxis = [0.01, 100]
with open(join(current_dir, 'hostcities.json'), 'rb') as f:
    hosts = json.load(f)
with open(join(current_dir, 'sportcats.json'), 'rb') as f:
    sportcats  = json.load(f)

THEME = {
    "external_stylesheets": [dbc.themes.BOOTSTRAP],
    "primary": "#007bff",
    "secondary": "#6c757d",
    "selected": "rgba(0, 0, 0, 0.075)",
    "font_color": "black",
    "font": "sans-serif",
}

def format_info_by_gender_country(row):
    info = row['iMeta']
    d_male = defaultdict(list)
    d_female = defaultdict(list)
    if isinstance(info, list):
        for each in info:
            player, age, gender, country = each.split('::')
            d = d_male if gender == 'Male' else d_female
            d[country].append(f'{player}({age})')

    s_male, s_female, step = '', '', 6
    for country, players in d_male.items():
        for breakpt in range(0, len(players)//step):
            i_breakpt = (breakpt+1) * step + breakpt
            players.insert(i_breakpt, '<br>&nbsp;&nbsp;')
        s_player = ' ,'.join(players)
        s_male += f'{country}: {s_player}<br>'

    
    for country, players in d_female.items():
        for breakpt in range(0, len(players)//step):
            i_breakpt = (breakpt+1) * step + breakpt
            players.insert(i_breakpt, '<br>&nbsp;&nbsp;')
        s_player = ' ,'.join(players)
        s_female += f'{country}: {s_player}<br>'
    
    return f'<br><b>Females</b>:<br>{s_female}<br><b>Males</b>:<br>{s_male}'

def format_sport_en_cn(row):
    sport = row['Sport']
    i=sport.index('(')
    return  f'{sport[:i]}<br>{sport[i:]}'

def get_df_bub_1_yr(df, yr, age, countries):
    if countries != ['All']:
        _df = df[df.Country.isin(countries)]
    else:
        _df = df.copy()
    _all_sports = _df.groupby(['Sport'])['Year'].apply(set)

    df_yr =  _df.query('Year==@yr')
    if age[1]==age_max:
        age[1] = 1000
    df_age_yr = _df[_df.Age.between(age[0], age[1])].query('Year==@yr')

    _base = df_yr.groupby('Sport')['Player'].count()
    _male = df_age_yr.query("Gender=='Male'").groupby('Sport')['Player'].count()
    _female = df_age_yr.query("Gender=='Female'").groupby('Sport')['Player'].count()
    _info = df_age_yr.groupby(['Sport'])['iMeta'].apply(list)

    temp = pd.concat([_all_sports,_base, _male, _female, _info], axis = 1).reset_index()
    temp.columns = ['Sport', 'YearsofOccurance', 'All', 'Male', 'Female', 'iMeta']
    temp = temp.fillna({'All':0,'Male':0,'Female':0, 'iFemale': '', 'iMale':''})
    temp = temp.assign(Year = yr,
                        FaM = temp['Female'] + temp['Male'],
                        FoM = round(temp['Female']/temp['Male'], 2))
    temp = temp.assign(AoAll = round(temp['FaM']/temp['All']*100, 2))
    temp.replace({'FoM':{0: 0.01, np.inf:100}}, inplace=True)
    temp = temp.fillna({'FoM':-100})
    temp['iDisplay'] = temp.apply(format_info_by_gender_country, axis = 1)
    return temp.sort_values(by=['Sport'])

def get_dfs_bub(df, age, countries, years):
    df_bub = pd.DataFrame()
    for yr in years:
        _df_bub = get_df_bub_1_yr(df, yr, age, countries)
        df_bub = pd.concat([df_bub, _df_bub])
    df_bub['Sport_cat'] = df_bub['Sport'].map(sportcats)
    df_bub['iSport'] = df_bub.apply(format_sport_en_cn, axis=1)
    return df_bub

def get_default_fig(years):
    sliders_dict = {
        "active": len(years)-1,
        "yanchor": "top", "xanchor": "left",
        "currentvalue": {
            "font": {"size": 20},
            "prefix": "Year: ",
            "visible": True,
            "xanchor": "right"
        },
        "transition": {"duration": 0.4*duration, "easing": "cubic-in-out"},
        "pad": {"b": 20, "t": 20},"len": 0.9,"x": 0.1,"y": 0,"steps": [],
        }

    for yr in years:
        slider_step = {"args": [
                [yr],
                {"frame": {"duration": duration, "redraw": False},
                "mode": "afterall", #next, afterall , immediate
                "transition": {"duration": 0.4*duration}}
                ],
                "label": hosts.get(str(yr), ''),
                "method": "animate"}
        sliders_dict["steps"].append(slider_step)
    layout_dict= dict(
        xaxis=dict(range=[-2.1, 2.1], type="log", title= dict(text="Ratio of Female/Male within Selected Age Range", standoff=5), fixedrange=True),
        yaxis=dict(range=[-10, 120], title="% Among All Medalists",fixedrange=True),
        legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="left", x=0,  itemsizing='constant'),
        margin=dict(l=50, r=50, t=10, b=10),
        height=500,
        hovermode='closest',
        template= 'none',
        updatemenus=[
            {
                "buttons": [
                    {
                        "args": [None, {"frame": {"duration": duration, "redraw": False},
                                        "fromcurrent": True, "transition": {"duration": 0.4*duration,
                                                                            "easing": "quadratic-in-out"}}],
                        "label": "Play",
                        "method": "animate"
                    },
                    {
                        "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                        "mode": "immediate",
                                        "transition": {"duration": 0}}],
                        "label": "Pause",
                        "method": "animate"
                    }
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 50},
                "showactive": False,
                "type": "buttons",
                "x": 0.1,
                "xanchor": "right",
                "y": 0,
                "yanchor": "top"
            }
        ],
        sliders=[sliders_dict]
    )
    
    fig = go.Figure()
    fig['layout']=layout_dict
    fig.add_vline(x=1, line_dash="dot", opacity=0.3)
    fig.add_vrect(x0=range_balance[0], x1=range_balance[1], fillcolor="green", opacity=0.1, line_width=0)
    fig.add_vrect(x0=0, x1=range_balance[0], fillcolor="steelblue", opacity=0.1, line_width=0)
    fig.add_vrect(x0=range_balance[1], x1=150, fillcolor="pink", opacity=0.1, line_width=0)
    fig.add_annotation(text="Let's call this <br> Gender Balance Zone", x=0, y=114, showarrow=False)
    fig.add_annotation(text="Male-favored", x=-1.9, y=114, showarrow=False)
    fig.add_annotation(text="Female-favored", x=1.9, y=114, showarrow=False)

    return fig

def get_fig_data(df_bub, years, show_text=True):
    fig_dict = {"data": [],"frames": []}
    # make frames
    for yr in years:
        frame = {"data": [], "name": str(yr)}
        _df = df_bub.query('Year==@yr')
        _percent = _df.groupby('Year')[['All', 'FaM']].sum()
        __percent = _percent['FaM'] / _percent['All'] * 100
        yy = __percent.values[0]
        line_dict = {
            'x': [0, 0.01, 1, 100, 150],
            'y': [yy] * 5,
            'name': '% of Age',
            "textposition": 'middle right',
            'showlegend': False,
            'line': dict(color='lightgrey', dash='dash', width=2),
            'text': [f'<b>{yy:.2f}%</b> of all medalists at that olympic (all sports aggregated)<br> fell in this age range'] * 5,
            'hovertemplate': '%{text}',
            'opacity': 0.5
        }
        frame["data"].append(line_dict)
        for cat in _df.Sport_cat.unique():
            __df = _df.query('Sport_cat==@cat')
            mode="markers+text" if show_text else 'markers'
            bubble_dict = {
                "x": __df["FoM"].fillna(0),
                "y": __df["AoAll"].fillna(0),
                'customdata': __df['iDisplay'],
                "mode": mode,
                "text": __df["iSport"], 
                "textposition": 'middle center',
                "textfont": dict(family="sans serif",size=10,color="grey"),
                "marker": dict(sizemode= "area", size= __df["FaM"], 
                                sizeref=df_bub['FaM'].max()/1e3,
                                sizemin = 1,
                        ),
                "name": cat,
                'hovertemplate':'<b>%{text}</b>'+
                                '<br><br><b>Size</b>(# of medalists within this age group):%{marker.size} (Female+Male)' +
                                '<br><b>Y</b>(% of this age group of all):%{y}%' +
                                '<br><b>X</b>(ratio of female over male): %{x:.2f}' +
                                '<br><br> %{customdata}<br>'
                        }
            frame["data"].append(bubble_dict)
        fig_dict["frames"].append(frame)

    fig_dict["data"]= fig_dict['frames'][-1]['data']
    return fig_dict

