import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Leer los datos
df = pd.read_csv('transacciones_rfm.csv')
df['transaction_date'] = pd.to_datetime(df['transaction_date'])

# Establecer la fecha de análisis (último día en los datos)
fecha_analisis = df['transaction_date'].max()

# Calcular métricas RFM por cliente
rfm = df.groupby('customer_id').agg({
    'transaction_date': lambda x: (fecha_analisis - x.max()).days,  # Recency
    'transaction_id': 'count',  # Frequency
    'total_amount': 'sum'  # Monetary
}).rename(columns={
    'transaction_date': 'recency',
    'transaction_id': 'frequency',
    'total_amount': 'monetary'
})

# Calcular quintiles para cada métrica
r_labels = range(5, 0, -1)  # 5 es mejor (compra reciente)
f_labels = range(1, 6)      # 5 es mejor (compra frecuente)
m_labels = range(1, 6)      # 5 es mejor (gasta más)

r_quintiles = pd.qcut(rfm['recency'], q=5, labels=r_labels)
f_quintiles = pd.qcut(rfm['frequency'], q=5, labels=f_labels)
m_quintiles = pd.qcut(rfm['monetary'], q=5, labels=m_labels)

# Agregar scores al dataframe
rfm['R'] = r_quintiles
rfm['F'] = f_quintiles
rfm['M'] = m_quintiles

# Calcular RFM Score
rfm['RFM_Score'] = rfm['R'].astype(str) + rfm['F'].astype(str) + rfm['M'].astype(str)

# Clasificar clientes
def clasificar_cliente(row):
    if row['R'] >= 4 and row['F'] >= 4 and row['M'] >= 4:
        return 'Champions'
    elif row['R'] >= 3 and row['F'] >= 3 and row['M'] >= 3:
        return 'Leales'
    elif row['R'] >= 3 and row['F'] >= 1 and row['M'] >= 2:
        return 'Potenciales'
    elif row['R'] <= 2 and row['F'] <= 2 and row['M'] <= 2:
        return 'En riesgo'
    elif row['R'] <= 1 and row['F'] <= 1 and row['M'] <= 1:
        return 'Perdidos'
    else:
        return 'Regular'

rfm['Segmento'] = rfm.apply(clasificar_cliente, axis=1)

# Mostrar resumen de segmentos
print("\nResumen de Segmentos de Clientes:")
print(rfm['Segmento'].value_counts())

# Mostrar estadísticas por segmento
print("\nEstadísticas por Segmento:")
segmento_stats = rfm.groupby('Segmento').agg({
    'recency': 'mean',
    'frequency': 'mean',
    'monetary': 'mean'
}).round(2)
print(segmento_stats)

# Modificar la configuración del estilo
plt.style.use('default')  # Usar estilo default de matplotlib
sns.set_theme()  # Aplicar tema de seaborn
sns.set_palette("husl")

# Crear figura con tres subplots
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 6))

# Preparar datos para gráficas
plot_data = segmento_stats.reset_index()

# Gráfica de Recency
sns.barplot(x='Segmento', y='recency', data=plot_data, ax=ax1)
ax1.set_title('Días desde última compra por Segmento')
ax1.set_xlabel('Segmento')
ax1.set_ylabel('Días (promedio)')
ax1.tick_params(axis='x', rotation=45)

# Gráfica de Frequency
sns.barplot(x='Segmento', y='frequency', data=plot_data, ax=ax2)
ax2.set_title('Frecuencia de compras por Segmento')
ax2.set_xlabel('Segmento')
ax2.set_ylabel('Número de compras (promedio)')
ax2.tick_params(axis='x', rotation=45)

# Gráfica de Monetary
sns.barplot(x='Segmento', y='monetary', data=plot_data, ax=ax3)
ax3.set_title('Valor monetario por Segmento')
ax3.set_xlabel('Segmento')
ax3.set_ylabel('Monto total (promedio)')
ax3.tick_params(axis='x', rotation=45)

# Ajustar layout
plt.tight_layout()

# Guardar gráfica
plt.savefig('analisis_rfm.png')

# Crear gráfica de radar (spider plot)

# Normalizar datos para el gráfico de radar
normalized_stats = segmento_stats.copy()
for column in ['recency', 'frequency', 'monetary']:
    normalized_stats[column] = (segmento_stats[column] - segmento_stats[column].min()) / \
                              (segmento_stats[column].max() - segmento_stats[column].min())
    if column == 'recency':  # Invertir recency ya que menor es mejor
        normalized_stats[column] = 1 - normalized_stats[column]

# Crear gráfica de radar
categories = ['Recency', 'Frequency', 'Monetary']
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='polar')

angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False)
angles = np.concatenate((angles, [angles[0]]))  # Cerrar el polígono

for segmento in normalized_stats.index:
    values = normalized_stats.loc[segmento].values
    values = np.concatenate((values, [values[0]]))
    ax.plot(angles, values, linewidth=2, label=segmento)
    ax.fill(angles, values, alpha=0.25)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories)
ax.set_title('Comparación RFM por Segmento')
plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

plt.tight_layout()
plt.savefig('radar_rfm.png')

# Guardar resultados
rfm.to_csv('resultados_rfm.csv') 