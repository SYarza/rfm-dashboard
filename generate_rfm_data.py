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

# Crear lista de productos con precios
products = {
    f'PROD_{str(i).zfill(3)}': round(random.uniform(100, 5000), 2) 
    for i in range(n_products)
}

# Después de crear products, agregar categorías y costos
product_categories = ['A', 'B', 'C']
for prod_id in products:
    # Agregar costo (entre 40% y 80% del precio)
    precio = products[prod_id]
    costo = round(precio * random.uniform(0.4, 0.8), 2)
    products[prod_id] = {
        'precio': precio,
        'costo': costo,
        'categoria': random.choice(product_categories)
    }

# Generar fechas aleatorias en los últimos 2 años
end_date = datetime.now()
start_date = end_date - timedelta(days=730)
dates = [
    start_date + timedelta(
        days=random.randint(0, 730)
    ) for _ in range(n_transactions)
]

# Crear el dataset
data = {
    'transaction_id': [f'TRX_{str(i).zfill(5)}' for i in range(n_transactions)],
    'customer_id': random.choices(customer_ids, k=n_transactions),
    'transaction_date': dates,
    'product_id': random.choices(list(products.keys()), k=n_transactions),
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