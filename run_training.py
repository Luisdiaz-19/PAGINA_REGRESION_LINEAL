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

df = pd.read_excel('housing_columnas_corregidas.xlsx')
print('Datos cargados:', df.shape)
print('Columnas:', list(df.columns))

cols_original = ['MedInc', 'HouseAge', 'AveRooms', 'AveBedrms', 'Population', 'AveOccup', 'Latitude', 'Longitude', 'MedianHouseValue']
cols_actual = ['median_income', 'housing_median_age', 'total_rooms', 'total_bedrooms', 'population', 'households', 'latitude', 'longitude', 'median_house_value']

rename_map = {}
for orig, actual in zip(cols_original, cols_actual):
    if actual in df.columns:
        rename_map[actual] = orig

if rename_map:
    df = df.rename(columns=rename_map)
    print('Renombradas:', rename_map)

target_col = 'MedianHouseValue'
if target_col not in df.columns:
    print(f'ERROR: columna objetivo {target_col} no encontrada')
    exit(1)

print('Columnas finales:', list(df.columns))

cat_cols = df.select_dtypes(include=['object']).columns.tolist()
print('Variables categoricas:', cat_cols)

if cat_cols:
    df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
    print('One-hot encoding aplicado a:', cat_cols)

nulos_originales = int(df.isnull().sum().sum())
nulos_por_col = {}
for c in df.columns:
    n = int(df[c].isnull().sum())
    if n > 0:
        nulos_por_col[c] = n

imputer = SimpleImputer(strategy='median')
df = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
nulos_final = int(df.isnull().sum().sum())
print(f'Nulos: {nulos_originales} -> {nulos_final}')

Q1 = df.quantile(0.25)
Q3 = df.quantile(0.75)
IQR = Q3 - Q1
outliers_before = int(((df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR))).any(axis=1).sum())

for col in df.columns:
    if col != target_col:
        q_low = df[col].quantile(0.01)
        q_high = df[col].quantile(0.99)
        df[col] = df[col].clip(lower=q_low, upper=q_high)
print('Outliers tratados:', outliers_before)

scaler = StandardScaler()
feature_cols = [c for c in df.columns if c != target_col]
df[feature_cols] = scaler.fit_transform(df[feature_cols])
print(f'Estandarizadas: {len(feature_cols)} variables')

X = df[feature_cols]
y = df[target_col]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f'Train: {X_train.shape[0]}, Test: {X_test.shape[0]}')

modelo = LinearRegression()
modelo.fit(X_train, y_train)
print('Modelo entrenado')

y_pred = modelo.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

print(f'MAE: {mae:.2f}, MSE: {mse:.2f}, RMSE: {rmse:.2f}, R2: {r2:.4f}')

joblib.dump(modelo, 'modelo_regresion_lineal.pkl')
joblib.dump(scaler, 'scaler.pkl')

fi = pd.DataFrame({'variable': feature_cols, 'coeficiente': modelo.coef_, 'abs_coeficiente': np.abs(modelo.coef_)}).sort_values('abs_coeficiente', ascending=False)

metadata = {
    'info_entrenamiento': {
        'algoritmo': 'LinearRegression()',
        'libreria': 'Scikit-Learn',
        'split': '80% Train / 20% Test',
        'train_samples': int(X_train.shape[0]), 'test_samples': int(X_test.shape[0]),
        'random_state': 42, 'variables_independientes': feature_cols, 'variable_dependiente': target_col
    },
    'metricas': {'mae': round(mae,2), 'mse': round(mse,2), 'rmse': round(rmse,2), 'r2': round(r2,4)},
    'feature_importance': fi.to_dict('records'),
    'X_test': X_test.values.tolist(), 'y_test': y_test.values.tolist(), 'y_pred': y_pred.tolist(),
    'nombres_columnas': feature_cols
}
with open('metadata_entrenamiento.json', 'w', encoding='utf-8') as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

mean_y = float(y.mean())
var_names_es = {
    'MedInc': 'Ingreso Medio', 'HouseAge': 'Antiguedad Viviendas', 'AveRooms': 'Prom. Habitaciones',
    'AveBedrms': 'Prom. Dormitorios', 'Population': 'Poblacion', 'AveOccup': 'Ocupacion Prom.',
    'Latitude': 'Latitud', 'Longitude': 'Longitud',
    'median_income': 'Ingreso Medio', 'housing_median_age': 'Antiguedad Viviendas',
    'total_rooms': 'Total Habitaciones', 'total_bedrooms': 'Total Dormitorios',
    'population': 'Poblacion', 'households': 'Hogares',
    'latitude': 'Latitud', 'longitude': 'Longitud',
    'ocean_proximity': 'Proximidad Oceano'
}
cat_dummies = [c for c in feature_cols if c not in cols_original]
cat_info = cat_cols + [c for c in cat_dummies if c not in cols_original]

info = {
    'informacion_inicial': {
        'dataset': 'California Housing', 'origen': 'Repositorio UCI / Kaggle',
        'descripcion': 'El dataset California Housing contiene informacion sobre viviendas en California, EE.UU., recopilada a partir del censo de 1990.',
        'tamano': f'{len(df):,} registros',
        'variables': f'{len(feature_cols)} variables predictoras + 1 variable objetivo',
        'variable_objetivo': 'MedianHouseValue - Valor medio de las viviendas en USD'
    },
    'estadisticas': df.describe().to_dict(),
    'reporte_preprocesamiento': {
        'nulos_iniciales': nulos_originales, 'nulos_por_columna': nulos_por_col,
        'metodo_nulos': 'SimpleImputer (mediana)',
        'nulos_final': nulos_final, 'duplicados': 0,
        'variables_categoricas': cat_cols,
        'codificacion': 'One-Hot Encoding' if cat_cols else 'No aplica',
        'outliers_detectados': outliers_before,
        'metodo_outliers': 'Winsorization (percentiles 1-99)',
        'normalizacion': 'Estandarizacion Z-score (StandardScaler)',
        'variables_escaladas': feature_cols
    },
    'info_entrenamiento': metadata['info_entrenamiento'],
    'metricas': metadata['metricas'],
    'feature_importance': metadata['feature_importance'],
    'conclusiones': [
        f'El precio medio de las viviendas es de ${mean_y:,.2f}.',
        f'El modelo explica el {r2*100:.1f}% de la variabilidad del precio.',
        f'RMSE de ${rmse:,.2f} ({(rmse/mean_y)*100:.1f}% del valor medio).',
        f'Error promedio de ${mae:,.2f} por prediccion.',
        f'Variable mas influyente: {fi.iloc[0]["variable"]} (coef: {fi.iloc[0]["coeficiente"]:.4f}).',
        'Mejoras futuras: probar Random Forest, Gradient Boosting, ingenieria de caracteristicas.',
        'La Regresion Lineal Multiple proporciona una base solida e interpretable.'
    ]
}
with open('resultados_completos.json', 'w', encoding='utf-8') as f:
    json.dump(info, f, ensure_ascii=False, indent=2, default=str)

print('TODO COMPLETADO')
