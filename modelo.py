import joblib
import pandas as pd
import numpy as np
import json
import os

RUTA_MODELO = 'modelo_regresion_lineal.pkl'
RUTA_SCALER = 'scaler.pkl'
RUTA_METADATA = 'metadata_entrenamiento.json'
RUTA_RESULTADOS = 'resultados_completos.json'

class ModeloRegresionLineal:

    def __init__(self):
        self.modelo = None
        self.scaler = None
        self.metadata = None
        self.resultados = None
        self.cargar()

    def cargar(self):
        if os.path.exists(RUTA_MODELO):
            self.modelo = joblib.load(RUTA_MODELO)
        if os.path.exists(RUTA_SCALER):
            self.scaler = joblib.load(RUTA_SCALER)
        if os.path.exists(RUTA_METADATA):
            with open(RUTA_METADATA, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        if os.path.exists(RUTA_RESULTADOS):
            with open(RUTA_RESULTADOS, 'r', encoding='utf-8') as f:
                self.resultados = json.load(f)

    def predecir(self, datos):
        if self.modelo is None:
            raise ValueError("El modelo no esta cargado. Ejecute entrenamiento.py primero.")
        if isinstance(datos, dict):
            datos = pd.DataFrame([datos])
        return self.modelo.predict(datos).tolist()

    def obtener_info_completa(self):
        return {
            'informacion_inicial': {
                'dataset': 'California Housing',
                'origen': 'Repositorio UCI / Scikit-Learn',
                'descripcion': 'El dataset California Housing contiene informacion sobre viviendas en California, EE.UU., recopilada a partir del censo de 1990. Cada registro representa un bloque censal (block group) y contiene informacion demografica y de vivienda.',
                'tamano': '20,640 registros',
                'variables': '8 variables predictoras + 1 variable objetivo',
                'variable_objetivo': 'MedianHouseValue - Valor medio de las viviendas en USD'
            } if self.resultados else {},
            'estadisticas': self.resultados.get('estadisticas', {}) if self.resultados else {},
            'reporte_preprocesamiento': self.resultados.get('reporte_preprocesamiento', {}) if self.resultados else {},
            'info_entrenamiento': self.resultados.get('info_entrenamiento', {}) if self.resultados else {},
            'metricas': self.resultados.get('metricas', {}) if self.resultados else {},
            'feature_importance': self.resultados.get('feature_importance', []) if self.resultados else [],
            'conclusiones': self.resultados.get('conclusiones', []) if self.resultados else [],
            'predicciones': {
                'y_test': self.metadata.get('y_test', []) if self.metadata else [],
                'y_pred': self.metadata.get('y_pred', []) if self.metadata else [],
                'nombres_columnas': self.metadata.get('nombres_columnas', []) if self.metadata else []
            } if self.metadata else {}
        }

if __name__ == '__main__':
    modelo = ModeloRegresionLineal()
    info = modelo.obtener_info_completa()
    print("Modelo cargado correctamente.")
    print(f"Metricas disponibles: {list(info.get('metricas', {}).keys())}")
