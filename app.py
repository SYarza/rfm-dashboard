import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Leer los datos RFM
rfm = pd.read_csv('resultados_rfm.csv')
df_transacciones = pd.read_csv('transacciones_rfm.csv')
df_transacciones['transaction_date'] = pd.to_datetime(df_transacciones['transaction_date'])

# Inicializar la aplicación Dash
app = dash.Dash(__name__)
server = app.server  # Línea necesaria para Render

# Calcular estadísticas por segmento para el resumen
segmento_stats = rfm.groupby('Segmento').agg({
    'recency': 'mean',
    'frequency': 'mean',
    'monetary': 'mean'
}).round(2)

# Crear gráficas
def create_bar_chart(data, x, y, title):
    fig = px.bar(
        data,
        x=x,
        y=y,
        title=title,
        color=x,
        template='plotly_white'
    )
    return fig

def create_radar_chart():
    # Normalizar datos
    normalized_stats = segmento_stats.copy()
    for column in ['recency', 'frequency', 'monetary']:
        normalized_stats[column] = (segmento_stats[column] - segmento_stats[column].min()) / \
                                 (segmento_stats[column].max() - segmento_stats[column].min())
        if column == 'recency':
            normalized_stats[column] = 1 - normalized_stats[column]

    fig = go.Figure()
    categories = ['Recency', 'Frequency', 'Monetary']

    for segmento in normalized_stats.index:
        fig.add_trace(go.Scatterpolar(
            r=normalized_stats.loc[segmento],
            theta=categories,
            fill='toself',
            name=segmento
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title='Comparación RFM por Segmento'
    )
    return fig

# Diseño del dashboard
app.layout = html.Div([
    html.H1('Dashboard de Análisis RFM', style={'textAlign': 'center'}),
    
    # Agregar selector de segmento
    html.Div([
        html.H3('Seleccionar Segmento'),
        dcc.Dropdown(
            id='segment-selector',
            options=[{'label': seg, 'value': seg} for seg in rfm['Segmento'].unique()],
            value='Champions',  # valor inicial
            style={'width': '50%', 'margin': '10px auto'}
        ),
        
        # Tabla de clientes por segmento
        html.Div([
            html.H3('Clientes del Segmento'),
            dash.dash_table.DataTable(
                id='customer-table',
                columns=[
                    {'name': 'ID Cliente', 'id': 'customer_id'},
                    {'name': 'Días desde última compra', 'id': 'recency'},
                    {'name': 'Frecuencia de compras', 'id': 'frequency'},
                    {'name': 'Valor total ($)', 'id': 'monetary'}
                ],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'minWidth': '100px'
                },
                style_header={
                    'backgroundColor': 'paleturquoise',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                page_size=10  # número de filas por página
            )
        ], style={'margin': '20px 0'})
    ], style={'margin': '20px', 'textAlign': 'center'}),
    
    # Resumen de métricas
    html.Div([
        html.H3('Resumen de Segmentos'),
        html.Div([
            html.Div([
                html.H4('Total de Clientes'),
                html.H2(f"{len(rfm):,}")
            ], className='metric-card'),
            html.Div([
                html.H4('Valor Total'),
                html.H2(f"${rfm['monetary'].sum():,.2f}")
            ], className='metric-card'),
            html.Div([
                html.H4('Promedio por Cliente'),
                html.H2(f"${rfm['monetary'].mean():,.2f}")
            ], className='metric-card')
        ], style={'display': 'flex', 'justifyContent': 'space-around'})
    ]),
    
    # Gráficas principales
    html.Div([
        dcc.Graph(
            figure=create_bar_chart(
                segmento_stats.reset_index(),
                'Segmento',
                'monetary',
                'Valor Monetario por Segmento'
            ),
            style={'width': '50%'}
        ),
        dcc.Graph(
            figure=create_radar_chart(),
            style={'width': '50%'}
        )
    ], style={'display': 'flex'}),
    
    # Gráficas secundarias
    html.Div([
        dcc.Graph(
            figure=create_bar_chart(
                segmento_stats.reset_index(),
                'Segmento',
                'frequency',
                'Frecuencia de Compras por Segmento'
            ),
            style={'width': '50%'}
        ),
        dcc.Graph(
            figure=create_bar_chart(
                segmento_stats.reset_index(),
                'Segmento',
                'recency',
                'Días desde Última Compra por Segmento'
            ),
            style={'width': '50%'}
        )
    ], style={'display': 'flex'}),
    
    # Tabla de estadísticas
    html.Div([
        html.H3('Estadísticas Detalladas por Segmento'),
        dcc.Graph(
            figure=go.Figure(data=[
                go.Table(
                    header=dict(values=['Segmento', 'Recency (días)', 'Frequency (compras)', 'Monetary ($)'],
                              fill_color='paleturquoise',
                              align='left'),
                    cells=dict(values=[
                        segmento_stats.index,
                        segmento_stats['recency'].round(1),
                        segmento_stats['frequency'].round(1),
                        segmento_stats['monetary'].round(2)
                    ],
                    fill_color='lavender',
                    align='left'))
            ])
        )
    ])
])

# Agregar callback para actualizar la tabla
@app.callback(
    Output('customer-table', 'data'),
    Input('segment-selector', 'value')
)
def update_table(selected_segment):
    if selected_segment is None:
        return []
    
    filtered_df = rfm[rfm['Segmento'] == selected_segment].copy()
    filtered_df = filtered_df.round({
        'recency': 1,
        'frequency': 0,
        'monetary': 2
    })
    
    return filtered_df.to_dict('records')

# Agregar estilos CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Dashboard RFM</title>
        {%css%}
        <style>
            .metric-card {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
                flex: 1;
            }
            .metric-card h4 {
                color: #666;
                margin: 0;
            }
            .metric-card h2 {
                color: #333;
                margin: 10px 0 0 0;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    app.run_server(debug=False)  # Cambiado a False para producción 