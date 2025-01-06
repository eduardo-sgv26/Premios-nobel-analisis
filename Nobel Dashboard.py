from dash import Dash, html, dcc, dash_table, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import pycountry #pip install pycountry

app = Dash(external_stylesheets=[dbc.themes.CERULEAN])

data = pd.read_csv('./data/nobel.csv')

# CLEAN DATASET
data['born'] = data['born'].astype(str)
data = data[~data['born'].str.startswith('00')]
data['born'] = pd.to_datetime(data['born'], format='%m/%d/%Y')

# AGE OF EVERY NOBEL PRIZE WINNER
data['age'] = data['year'] - data['born'].dt.year

# FUNCTION GET THE ISO alpha-3 CODE FOR EVERY COUNTRY

def get_country_code(country_name):
    try:
        country = pycountry.countries.get(name=country_name)
        if country:
            return country.alpha_3
        if country_name == 'USA':
            return 'USA'
        else:
            return None
    except Exception as e:
        return None

data['Country_ISO3'] = data['bornCountry'].apply(get_country_code)

# DASHBOARD

# NAVBAR #
navbar = dbc.NavbarSimple(
    brand='Nobel Prize Dashboard',
    brand_style={'marginLeft': 10, 'fontFamily': "Helvetica"},
    children=[
        #html.Img(src=sofifa_logo, height=20),
        html.A('Data Source',
               href='https://www.kaggle.com/datasets/thedevastator/a-complete-history-of-nobel-prize-winners?select=nobelTriples.csv',
               target='_blank')
            ],
    color='primary',
    fluid=True
)

# SLIDER #

year_min = int(data['year'].min())
year_max = int(data['year'].max())

slider = html.Div([
    html.H4('Year', id='titleSlider'),
    dcc.RangeSlider(id='year-slider',
                    min=year_min,
                    max=year_max,
                    value=[year_min, year_max],
                    marks={i:str(i) for i in range(year_min, year_max+1, 10)}),
])

# MENU #

menu_drop = html.Div([
    dcc.Dropdown(data['category'].unique(), placeholder="Select a category", id='cat-dropdown'),
], id='menuDrop')

# MAP #

complete_map = html.Div(dcc.Graph(id='map-graph'))

# PERCENTAGE CARDS #

cards = html.Div([
    dbc.Row([
        dbc.Col(
            dbc.Card([
                html.H4('Man'),
                html.H5(id='percentage-man')
            ],
            body=True,
            id='card-man')
        ),
        dbc.Col(
            dbc.Card([
                html.H4('Woman'),
                html.H5(id='percentage-woman')
            ],
            body=True,
            id='card-woman')
        )
    ])
], id='cards')

# CATEGORIES TABLE #

table = dash_table.DataTable(
    id='table-categories',
    columns=[{'name': 'Category', 'id': 'category'}, {'name': 'Count', 'id': 'count'}],
    data=[]
)

# SCATTER PLOT #

graph_age = html.Div(dcc.Graph(id='scatter-graph'))

# CALLBACKS #

@app.callback(
    Output('map-graph', 'figure'),
    Output('scatter-graph', 'figure'),
    Output('percentage-man', 'children'),
    Output('percentage-woman', 'children'),
    Output('table-categories', 'data'),
    Input('year-slider', 'value'),
    Input('cat-dropdown', 'value')
)
def update_dashboard(selected_years, category):
    
    if category == None:

        filtered_data = data[
            (data['year'] >= selected_years[0]) &
            (data['year'] <= selected_years[1])
        ]
    else:
        filtered_data = data[
            (data['year'] >= selected_years[0]) &
            (data['year'] <= selected_years[1]) &
            (data['category'] == category)
        ]
    categories = filtered_data['category'].value_counts().reset_index()
    categories = filtered_data['category'].value_counts().reset_index()
    categories.columns = ['category', 'count']

    age_winners = px.scatter( #pip install statsmodels
        filtered_data, x='year', y='age', opacity=0.65,
        trendline='ols', trendline_color_override='darkblue',
        title='Age of Nobel Prize Winners by Year'
    ).update_layout(
        xaxis_title="Year", yaxis_title="Age"
    )

    total_ganadores = len(filtered_data)
    ganadores_hombres = len(filtered_data[filtered_data['gender'] == 'male'])
    ganadores_mujeres = len(filtered_data[filtered_data['gender'] == 'female'])

    # Calcular los porcentajes
    porcentaje_hombres = (ganadores_hombres / total_ganadores) * 100
    porcentaje_mujeres = (ganadores_mujeres / total_ganadores) * 100

    winners_country = filtered_data['Country_ISO3'].value_counts().reset_index()
    winners_country.rename(columns={'Country_ISO3': 'country'}, inplace=True)
    map_fig = px.choropleth(winners_country, locations='country', color='count',
                            title='Number of Nobel Prize Winners per Country')

    return map_fig, age_winners, f'{round(porcentaje_hombres, 2)} %', f'{round(porcentaje_mujeres, 2)} %', categories.to_dict('records')

# APP # 

app.layout = html.Div([
    dbc.Row(navbar),
    dbc.Row(slider),
    dbc.Row([
            dbc.Col([complete_map]),
            dbc.Col([dbc.Row(menu_drop), dbc.Row(cards), dbc.Row(table)])
        ]),
    dbc.Row(graph_age)
    ]
)

if __name__ == '__main__':
    app.run_server(debug=True)