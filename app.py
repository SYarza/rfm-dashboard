import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import random

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

# Crear análisis de productos
product_analysis = df_transacciones.groupby('product_id').agg({
    'quantity': 'sum',
    'total_amount': 'sum',
    'transaction_id': 'count'
}).rename(columns={
    'transaction_id': 'num_ventas'
})

product_analysis['precio_promedio'] = product_analysis['total_amount'] / product_analysis['quantity']

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

# Agregar cálculos para análisis ABC
def calculate_abc_analysis(df):
    # Análisis por producto
    product_metrics = df.groupby('product_id').agg({
        'total_amount': 'sum',
        'margin': 'sum',
        'quantity': 'sum'
    }).reset_index()
    
    # Calcular porcentajes acumulados
    product_metrics = product_metrics.sort_values('total_amount', ascending=False)
    product_metrics['porcentaje_ventas'] = product_metrics['total_amount'] / product_metrics['total_amount'].sum() * 100
    product_metrics['porcentaje_acumulado'] = product_metrics['porcentaje_ventas'].cumsum()
    
    # Asignar clasificación ABC
    product_metrics['clasificacion_abc'] = product_metrics['porcentaje_acumulado'].apply(
        lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C')
    )
    
    return product_metrics

# Cálculos para matriz BCG
def calculate_bcg_analysis(df):
    # Calcular métricas por producto
    product_metrics = df.groupby('product_id').agg({
        'total_amount': 'sum',
        'margin': 'sum',
        'quantity': 'sum'
    }).reset_index()
    
    # Calcular participación de mercado relativa
    total_market = product_metrics['total_amount'].sum()
    product_metrics['market_share'] = product_metrics['total_amount'] / total_market
    
    # Calcular tasa de crecimiento (simulada pero más realista)
    # Usamos una distribución que garantiza diferentes categorías
    n_products = len(product_metrics)
    growth_rates = []
    for i in range(n_products):
        if i < n_products * 0.2:  # Estrellas
            growth_rates.append(random.uniform(20, 40))  # Alto crecimiento
        elif i < n_products * 0.4:  # Vacas
            growth_rates.append(random.uniform(-10, 5))  # Bajo crecimiento
        elif i < n_products * 0.7:  # Interrogantes
            growth_rates.append(random.uniform(20, 35))  # Alto crecimiento
        else:  # Perros
            growth_rates.append(random.uniform(-20, 0))  # Crecimiento negativo
    
    product_metrics['growth_rate'] = growth_rates
    
    # Ajustar umbrales para clasificación
    product_metrics['bcg_category'] = product_metrics.apply(
        lambda x: 'Estrella' if x['market_share'] >= 0.03 and x['growth_rate'] >= 20
        else ('Vaca' if x['market_share'] >= 0.03 and x['growth_rate'] < 10
        else ('Interrogante' if x['market_share'] < 0.03 and x['growth_rate'] >= 20
        else 'Perro')), axis=1
    )
    
    return product_metrics

# Diseño del dashboard
app.layout = html.Div([
    html.H1('Dashboard de Análisis de Ventas', style={'textAlign': 'center'}),
    
    dcc.Tabs([
        # Pestaña de Análisis RFM
        dcc.Tab(label='Análisis RFM', children=[
            html.Div([
                # Selector de segmento y tabla
                html.Div([
                    html.H3('Seleccionar Segmento'),
                    dcc.Dropdown(
                        id='segment-selector',
                        options=[{'label': seg, 'value': seg} for seg in rfm['Segmento'].unique()],
                        value='Champions',
                        style={'width': '50%', 'margin': '10px auto'}
                    ),
                    html.Div([
                        html.H3('Clientes del Segmento'),
                        dash_table.DataTable(
                            id='customer-table',
                            columns=[
                                {'name': 'ID Cliente', 'id': 'customer_id'},
                                {'name': 'Días desde última compra', 'id': 'recency'},
                                {'name': 'Frecuencia de compras', 'id': 'frequency'},
                                {'name': 'Valor total ($)', 'id': 'monetary'}
                            ],
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left', 'padding': '10px', 'minWidth': '100px'},
                            style_header={'backgroundColor': 'paleturquoise', 'fontWeight': 'bold'},
                            style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}],
                            page_size=10
                        )
                    ], style={'margin': '20px 0'})
                ], style={'margin': '20px', 'textAlign': 'center'}),

                # Resumen de métricas RFM
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

                # Gráficas RFM
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

                # Tabla de estadísticas RFM
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
        ]),
        
        # Nueva Pestaña de Análisis de Productos
        dcc.Tab(label='Análisis de Productos', children=[
            html.Div([
                # Métricas principales de productos
                html.Div([
                    html.H3('Resumen de Productos'),
                    html.Div([
                        html.Div([
                            html.H4('Total Productos'),
                            html.H2(f"{len(product_analysis):,}")
                        ], className='metric-card'),
                        html.Div([
                            html.H4('Total Unidades Vendidas'),
                            html.H2(f"{product_analysis['quantity'].sum():,}")
                        ], className='metric-card'),
                        html.Div([
                            html.H4('Venta Total'),
                            html.H2(f"${product_analysis['total_amount'].sum():,.2f}")
                        ], className='metric-card')
                    ], style={'display': 'flex', 'justifyContent': 'space-around'})
                ]),

                # Gráficas de productos
                html.Div([
                    dcc.Graph(
                        figure=px.bar(
                            product_analysis.nlargest(10, 'total_amount').reset_index(),
                            x='product_id',
                            y='total_amount',
                            title='Top 10 Productos por Ventas Totales'
                        ),
                        style={'width': '50%'}
                    ),
                    dcc.Graph(
                        figure=px.bar(
                            product_analysis.nlargest(10, 'quantity').reset_index(),
                            x='product_id',
                            y='quantity',
                            title='Top 10 Productos por Unidades Vendidas'
                        ),
                        style={'width': '50%'}
                    )
                ], style={'display': 'flex'}),

                # Tabla de productos
                html.Div([
                    html.H3('Detalles de Productos'),
                    dash_table.DataTable(
                        id='product-table',
                        columns=[
                            {'name': 'ID Producto', 'id': 'product_id'},
                            {'name': 'Unidades Vendidas', 'id': 'quantity'},
                            {'name': 'Número de Ventas', 'id': 'num_ventas'},
                            {'name': 'Venta Total ($)', 'id': 'total_amount'},
                            {'name': 'Precio Promedio ($)', 'id': 'precio_promedio'}
                        ],
                        data=product_analysis.reset_index().round(2).to_dict('records'),
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'padding': '10px'},
                        style_header={'backgroundColor': 'paleturquoise', 'fontWeight': 'bold'},
                        style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}],
                        page_size=10,
                        sort_action='native'
                    )
                ])
            ])
        ]),
        
        # Nueva Pestaña de Análisis ABC/BCG
        dcc.Tab(label='Análisis ABC/BCG', children=[
            html.Div([
                # Resumen ABC
                html.Div([
                    html.H3('Análisis ABC'),
                    dcc.Graph(
                        figure=px.pie(
                            calculate_abc_analysis(df_transacciones),
                            names='clasificacion_abc',
                            values='total_amount',
                            title='Distribución de Ventas por Clasificación ABC'
                        )
                    )
                ]),
                
                # Matriz BCG
                html.Div([
                    html.H3('Matriz BCG'),
                    dcc.Graph(
                        figure=px.scatter(
                            calculate_bcg_analysis(df_transacciones),
                            x='market_share',
                            y='growth_rate',
                            size='total_amount',
                            color='bcg_category',
                            hover_data=['product_id'],
                            title='Matriz BCG'
                        )
                    )
                ]),
                
                # Tabla detallada
                html.Div([
                    html.H3('Detalles por Producto'),
                    dash_table.DataTable(
                        id='abc-bcg-table',
                        columns=[
                            {'name': 'Producto', 'id': 'product_id'},
                            {'name': 'Ventas Totales ($)', 'id': 'total_amount', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                            {'name': 'Margen ($)', 'id': 'margin', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                            {'name': 'Participación (%)', 'id': 'market_share', 'type': 'numeric', 'format': {'specifier': '.2%'}},
                            {'name': 'Crecimiento (%)', 'id': 'growth_rate', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                            {'name': 'Clasificación ABC', 'id': 'clasificacion_abc'},
                            {'name': 'Categoría BCG', 'id': 'bcg_category'}
                        ],
                        data=pd.merge(
                            calculate_abc_analysis(df_transacciones),
                            calculate_bcg_analysis(df_transacciones),
                            on='product_id'
                        ).to_dict('records'),
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'padding': '10px'},
                        style_header={'backgroundColor': 'paleturquoise', 'fontWeight': 'bold'},
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            },
                            {
                                'if': {'column_id': 'bcg_category', 'filter_query': '{bcg_category} = "Estrella"'},
                                'backgroundColor': '#ffeb3b',
                                'fontWeight': 'bold'
                            },
                            {
                                'if': {'column_id': 'bcg_category', 'filter_query': '{bcg_category} = "Vaca"'},
                                'backgroundColor': '#4caf50',
                                'color': 'white'
                            },
                            {
                                'if': {'column_id': 'bcg_category', 'filter_query': '{bcg_category} = "Interrogante"'},
                                'backgroundColor': '#2196f3',
                                'color': 'white'
                            },
                            {
                                'if': {'column_id': 'bcg_category', 'filter_query': '{bcg_category} = "Perro"'},
                                'backgroundColor': '#f44336',
                                'color': 'white'
                            }
                        ],
                        page_size=10,
                        sort_action='native'
                    )
                ])
            ])
        ])
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