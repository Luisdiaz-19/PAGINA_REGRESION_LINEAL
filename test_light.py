import warnings
warnings.filterwarnings('ignore')
from app import app
with app.test_client() as c:
    r = c.get('/')
    print('HTML OK:', r.status_code, 'len:', len(r.data))
    r = c.get('/api/info_completa')
    d = r.get_json()
    print('Distribuciones:', list(d.get('distribuciones', {}).keys()))
    print('Metricas:', d.get('metricas'))
print('TODO OK')
