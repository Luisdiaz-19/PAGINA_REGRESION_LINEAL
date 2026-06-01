import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import joblib
import json
import warnings
warnings.filterwarnings('ignore')

RUTA_EXCEL = 'housing_columnas_corregidas.xlsx'
RUTA_MODELO = 'modelo_regresion_lineal.pkl'
RUTA_SCALER = 'scaler.pkl'
RUTA_METADATA = 'metadata_entrenamiento.json'

def cargar_datos(ruta):
    print("=" * 60)
    print("LABORATORIO DE REGRESION LINEAL - CALIFORNIA HOUSING")
    print("=" * 60)
    df = pd.read_excel(ruta)
    colmap = {
        'median_income': 'MedInc', 'housing_median_age': 'HouseAge',
        'total_rooms': 'AveRooms', 'total_bedrooms': 'AveBedrms',
        'population': 'Population', 'households': 'AveOccup',
        'latitude': 'Latitude', 'longitude': 'Longitude',
        'median_house_value': 'MedianHouseValue'
    }
    rename = {k: v for k, v in colmap.items() if k in df.columns}
    if rename:
        df = df.rename(columns=rename)
    print(f"\n[1] Datos cargados: {df.shape[0]} registros, {df.shape[1]} columnas")
    print(f"    Columnas: {list(df.columns)}")
    return df

def preprocesar(df):
    print("\n[2] PREPROCESAMIENTO DE DATOS")
    print("-" * 40)

    nulos_originales = int(df.isnull().sum().sum())
    nulos_por_col = {}
    for c in df.columns:
        n = int(df[c].isnull().sum())
        if n > 0:
            nulos_por_col[c] = n
    print(f"  Valores nulos detectados: {nulos_originales}")
    for col, cant in nulos_por_col.items():
        print(f"    - {col}: {cant}")

    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
    print(f"  Variables categoricas: {cat_cols if cat_cols else 'Ninguna'}")

    if cat_cols:
        df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
        print(f"  One-Hot Encoding aplicado a: {cat_cols}")

    imputer = SimpleImputer(strategy='median')
    df = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
    nulos_final = int(df.isnull().sum().sum())
    print(f"  Nulos corregidos con SimpleImputer (mediana): {nulos_originales} -> {nulos_final}")

    duplicados = int(df.duplicated().sum())
    df = df.drop_duplicates()
    print(f"  Duplicados: {duplicados}")

    Q1 = df.quantile(0.25)
    Q3 = df.quantile(0.75)
    IQR = Q3 - Q1
    outliers_before = int(((df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR))).any(axis=1).sum())
    print(f"  Outliers detectados (IQR): {outliers_before}")

    for col in df.columns:
        if col != 'MedianHouseValue':
            q_low = df[col].quantile(0.01)
            q_high = df[col].quantile(0.99)
            df[col] = df[col].clip(lower=q_low, upper=q_high)
    print(f"  Outliers tratados con winsorization (1-99)")

    scaler = StandardScaler()
    feature_cols = [c for c in df.columns if c != 'MedianHouseValue']
    df[feature_cols] = scaler.fit_transform(df[feature_cols])
    print(f"  Estandarizadas: {len(feature_cols)} variables con Z-score")

    reporte = {
        'nulos_iniciales': nulos_originales,
        'nulos_por_columna': nulos_por_col,
        'metodo_nulos': 'SimpleImputer (mediana)',
        'nulos_final': nulos_final,
        'duplicados': duplicados,
        'variables_categoricas': cat_cols,
        'codificacion': 'One-Hot Encoding' if cat_cols else 'No aplica',
        'outliers_detectados': outliers_before,
        'metodo_outliers': 'Winsorization (percentiles 1-99)',
        'normalizacion': 'Estandarizacion Z-score (StandardScaler)',
        'variables_escaladas': feature_cols
    }
    print(f"\n[3] PREPROCESAMIENTO COMPLETADO")
    return df, reporte, scaler

def entrenar(df, scaler):
    print("\n[4] ENTRENAMIENTO DEL MODELO")
    print("-" * 40)

    X = df.drop(columns=['MedianHouseValue'])
    y = df['MedianHouseValue']

    print(f"  Variables independientes (X): {X.shape[1]}")
    print(f"  Variable dependiente (y): MedianHouseValue")
    print(f"  Dimensiones: {X.shape}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"  Train: {X_train.shape[0]} (80%), Test: {X_test.shape[0]} (20%)")

    modelo = LinearRegression()
    modelo.fit(X_train, y_train)
    print(f"  Algoritmo: LinearRegression(), coeficientes: {len(modelo.coef_)}")

    y_pred = modelo.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    print(f"\n[5] EVALUACION")
    print(f"  MAE:  ${mae:,.2f}")
    print(f"  MSE:  ${mse:,.2f}")
    print(f"  RMSE: ${rmse:,.2f}")
    print(f"  R²:   {r2:.4f} ({r2*100:.2f}%)")

    metricas = {'mae': round(mae,2), 'mse': round(mse,2), 'rmse': round(rmse,2), 'r2': round(r2,4)}

    info_entrenamiento = {
        'algoritmo': 'LinearRegression()', 'libreria': 'Scikit-Learn',
        'split': '80% Train / 20% Test', 'train_samples': int(X_train.shape[0]),
        'test_samples': int(X_test.shape[0]), 'random_state': 42,
        'variables_independientes': list(X.columns), 'variable_dependiente': 'MedianHouseValue'
    }

    fi = pd.DataFrame({
        'variable': X.columns, 'coeficiente': modelo.coef_,
        'abs_coeficiente': np.abs(modelo.coef_)
    }).sort_values('abs_coeficiente', ascending=False)

    print("\n[6] IMPORTANCIA DE VARIABLES")
    for _, r in fi.iterrows():
        print(f"  {r['variable']:30s}: {r['coeficiente']:>10.4f}")

    joblib.dump(modelo, RUTA_MODELO)
    joblib.dump(scaler, RUTA_SCALER)

    metadata = {
        'info_entrenamiento': info_entrenamiento, 'metricas': metricas,
        'feature_importance': fi.to_dict('records'),
        'X_test': X_test.values.tolist(), 'y_test': y_test.values.tolist(),
        'y_pred': y_pred.tolist(), 'nombres_columnas': list(X.columns)
    }
    with open(RUTA_METADATA, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\n[7] Modelo guardado en {RUTA_MODELO}")
    return modelo, metricas, info_entrenamiento, fi, X_train, X_test, y_train, y_test, y_pred

def generar_conclusiones(metricas, fi, df):
    r2 = metricas['r2']; rmse = metricas['rmse']; mae = metricas['mae']
    mean_y = df['MedianHouseValue'].mean()
    top = fi.head(3)
    c = []
    c.append(f"El precio medio de las viviendas es de ${mean_y:,.2f}.")
    if r2 >= 0.7:
        c.append(f"R² de {r2*100:.1f}%: el modelo tiene buen ajuste.")
    elif r2 >= 0.5:
        c.append(f"R² de {r2*100:.1f}%: el modelo captura tendencias importantes pero es mejorable.")
    else:
        c.append(f"R² de {r2*100:.1f}%: el modelo tiene capacidad explicativa limitada.")
    c.append(f"RMSE de ${rmse:,.2f} ({(rmse/mean_y)*100:.1f}% del precio medio).")
    c.append(f"Error promedio de ${mae:,.2f} por prediccion.")
    for _, r in top.iterrows():
        signo = "positiva" if r['coeficiente'] > 0 else "negativa"
        c.append(f"'{r['variable']}' tiene influencia {signo} (coef: {r['coeficiente']:.4f}).")
    c.append("Mejoras: Random Forest, Gradient Boosting, ingenieria de caracteristicas.")
    c.append("La Regresion Lineal Multiple ofrece una base solida e interpretable.")
    return c

def ejecutar():
    df = cargar_datos(RUTA_EXCEL)
    df_proc, reporte, scaler = preprocesar(df)
    modelo, metricas, info_entrenamiento, fi, X_train, X_test, y_train, y_test, y_pred = entrenar(df_proc, scaler)
    conclusiones = generar_conclusiones(metricas, fi, df)

    resultados = {
        'informacion_inicial': {
            'dataset': 'California Housing', 'origen': 'Repositorio UCI / Kaggle',
            'descripcion': 'Datos de viviendas en California del censo de 1990.',
            'tamano': f'{len(df):,} registros',
            'variables': f'{len(info_entrenamiento["variables_independientes"])} predictoras + 1 objetivo',
            'variable_objetivo': 'MedianHouseValue - Valor medio en USD'
        },
        'estadisticas': df_proc.describe().to_dict(),
        'reporte_preprocesamiento': reporte,
        'info_entrenamiento': info_entrenamiento,
        'metricas': metricas,
        'feature_importance': fi.to_dict('records'),
        'conclusiones': conclusiones
    }
    with open('resultados_completos.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n{'='*60}")
    print("ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
    print(f"{'='*60}")

if __name__ == '__main__':
    ejecutar()
