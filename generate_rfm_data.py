import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Configurar semilla para reproducibilidad
np.random.seed(42)

# Generar datos base
n_transactions = 10000
n_customers = 1000
n_products = 50

# Crear IDs de clientes
customer_ids = [f'CUST_{str(i).zfill(4)}' for i in range(n_customers)]

# Definir categorías de productos
product_categories = ['A', 'B', 'C']

# Crear lista de productos con precios y categorías
products = {}
for i in range(n_products):
    prod_id = f'PROD_{str(i).zfill(3)}'
    
    # Asignar diferentes rangos de precios según la categoría deseada
    if i < n_products * 0.2:  # 20% Estrellas
        precio = round(random.uniform(2000, 5000), 2)  # Productos premium
        market_weight = 2.0  # Mayor peso en selección para ventas
    elif i < n_products * 0.4:  # 20% Vacas
        precio = round(random.uniform(1000, 3000), 2)  # Productos establecidos
        market_weight = 1.5  # Peso medio-alto en selección
    elif i < n_products * 0.7:  # 30% Interrogantes
        precio = round(random.uniform(500, 2000), 2)  # Productos nuevos
        market_weight = 0.5  # Peso bajo en selección
    else:  # 30% Perros
        precio = round(random.uniform(100, 1000), 2)  # Productos económicos
        market_weight = 0.3  # Peso muy bajo en selección
    
    costo = round(precio * random.uniform(0.4, 0.8), 2)
    products[prod_id] = {
        'precio': precio,
        'costo': costo,
        'categoria': random.choice(product_categories),
        'market_weight': market_weight
    }

# Modificar la generación de transacciones para reflejar participación de mercado
weighted_products = [(k, v['market_weight']) for k, v in products.items()]
product_ids, weights = zip(*weighted_products)

# Generar fechas aleatorias en los últimos 2 años
end_date = datetime.now()
start_date = end_date - timedelta(days=730)
dates = [
    start_date + timedelta(
        days=random.randint(0, 730)
    ) for _ in range(n_transactions)
]

# Crear el dataset con selección ponderada de productos
data = {
    'transaction_id': [f'TRX_{str(i).zfill(5)}' for i in range(n_transactions)],
    'customer_id': random.choices(customer_ids, k=n_transactions),
    'transaction_date': dates,
    'product_id': random.choices(product_ids, weights=weights, k=n_transactions),
    'quantity': np.random.randint(1, 10, size=n_transactions)
}

# Convertir a DataFrame
df = pd.DataFrame(data)

# Agregar precio, costo y categoría
df['unit_price'] = df['product_id'].map(lambda x: products[x]['precio'])
df['unit_cost'] = df['product_id'].map(lambda x: products[x]['costo'])
df['category'] = df['product_id'].map(lambda x: products[x]['categoria'])
df['total_amount'] = df['quantity'] * df['unit_price']
df['total_cost'] = df['quantity'] * df['unit_cost']
df['margin'] = df['total_amount'] - df['total_cost']

# Ordenar por fecha
df = df.sort_values('transaction_date')

# Guardar a CSV
df.to_csv('transacciones_rfm.csv', index=False)

# Mostrar las primeras filas
print(df.head()) 