from flask import Flask, render_template, jsonify
from modelo import ModeloRegresionLineal
import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings('ignore')
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)
modelo = ModeloRegresionLineal()

RUTA_EXCEL = 'housing_columnas_corregidas.xlsx'

def cargar_dataframe():
    df = pd.read_excel(RUTA_EXCEL)
    colmap = {}
    if 'median_income' in df.columns: colmap['median_income'] = 'MedInc'
    if 'housing_median_age' in df.columns: colmap['housing_median_age'] = 'HouseAge'
    if 'total_rooms' in df.columns: colmap['total_rooms'] = 'AveRooms'
    if 'total_bedrooms' in df.columns: colmap['total_bedrooms'] = 'AveBedrms'
    if 'population' in df.columns: colmap['population'] = 'Population'
    if 'households' in df.columns: colmap['households'] = 'AveOccup'
    if 'latitude' in df.columns: colmap['latitude'] = 'Latitude'
    if 'longitude' in df.columns: colmap['longitude'] = 'Longitude'
    if 'median_house_value' in df.columns: colmap['median_house_value'] = 'MedianHouseValue'
    if colmap:
        df = df.rename(columns=colmap)
    num_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in num_cols:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())
    return df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info_completa')
def api_info_completa():
    info = modelo.obtener_info_completa()
    df = cargar_dataframe()

    cat_cols = df.select_dtypes(include=['object']).columns.tolist()

    info['datos_raw'] = {
        'nombres_columnas': list(df.columns),
        'primeros_registros': json.loads(df.head(10).to_json(orient='records')),
        'estadisticas_descriptivas': json.loads(df.describe().to_json())
    }

    resumen_valores = {}
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            resumen_valores[col] = {
                'media': round(float(df[col].mean()), 2),
                'mediana': round(float(df[col].median()), 2),
                'moda': round(float(df[col].mode().iloc[0]), 2) if not df[col].mode().empty else 0,
                'maximo': round(float(df[col].max()), 2),
                'minimo': round(float(df[col].min()), 2),
                'std': round(float(df[col].std()), 2)
            }
    info['resumen_valores'] = resumen_valores

    info['distribuciones'] = {}
    for col in ['MedInc', 'MedianHouseValue', 'AveRooms', 'Population']:
        if col in df.columns:
            vals = df[col].dropna()
            if len(vals) > 0:
                hist, edges = np.histogram(vals, bins=30)
                info['distribuciones'][col] = {'valores': hist.tolist(), 'edges': edges.tolist()}

    info['variables_categoricas'] = cat_cols

    return jsonify(info)

@app.route('/api/datos_tabla')
def api_datos_tabla():
    df = cargar_dataframe()
    data = json.loads(df.to_json(orient='records'))
    return jsonify({'data': data, 'total': len(data), 'columnas': list(df.columns)})

@app.route('/api/estadisticas')
def api_estadisticas():
    df = cargar_dataframe()
    stats = {}
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            stats[col] = {
                'media': round(float(df[col].mean()), 4),
                'mediana': round(float(df[col].median()), 4),
                'moda': round(float(df[col].mode().iloc[0]), 4) if not df[col].mode().empty else 0,
                'std': round(float(df[col].std()), 4),
                'min': round(float(df[col].min()), 4),
                'max': round(float(df[col].max()), 4),
                'q25': round(float(df[col].quantile(0.25)), 4),
                'q50': round(float(df[col].quantile(0.5)), 4),
                'q75': round(float(df[col].quantile(0.75)), 4)
            }
    return jsonify(stats)

@app.route('/api/correlaciones')
def api_correlaciones():
    df = cargar_dataframe()
    df_numeric = df.select_dtypes(include=['float64', 'int64'])
    corr = df_numeric.corr()
    return jsonify({'variables': list(corr.columns), 'matriz': corr.values.tolist()})

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    print("Dashboard disponible en: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
