# Regresion Lineal - California Housing Dashboard

Aplicacion web profesional para el analisis del dataset California Housing y entrenamiento de un modelo de Regresion Lineal Multiple.

## Tecnologias

- **Backend:** Python, Flask, Pandas, NumPy, Scikit-Learn, Joblib
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js
- **Visualizacion:** Chart.js (graficos interactivos)

## Instalacion

```bash
pip install -r requirements.txt
```

## Uso

### 1. Generar el dataset (opcional)
```bash
python generar_excel.py
```

### 2. Entrenar el modelo
```bash
python entrenamiento.py
```

### 3. Iniciar el servidor
```bash
python app.py
```

### 4. Abrir en el navegador
```
http://127.0.0.1:5000
```

## Estructura del Proyecto

```
PAGINA_REGRESION_LINEAL/
├── app.py                          # Servidor Flask
├── entrenamiento.py                # Preprocesamiento y entrenamiento
├── modelo.py                       # Carga y prediccion del modelo
├── generar_excel.py                # Generacion del dataset
├── requirements.txt                # Dependencias
├── housing_columnas_corregidas.xlsx# Dataset
├── modelo_regresion_lineal.pkl     # Modelo entrenado
├── scaler.pkl                      # Scaler ajustado
├── metadata_entrenamiento.json     # Metadata del modelo
├── resultados_completos.json       # Resultados completos
├── templates/
│   └── index.html                  # Dashboard principal
└── static/
    ├── css/
    │   └── style.css               # Estilos dark mode
    └── js/
        └── main.js                 # Graficos e interactividad
```

## Dataset

California Housing (UCI / Scikit-Learn)
- 20,640 registros
- 8 variables predictoras
- 1 variable objetivo: MedianHouseValue
