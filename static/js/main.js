let state = {
    infoCompleta: null,
    datosTabla: [],
    tablaPage: 1,
    tablaPageSize: 15,
    charts: {}
};

const C = {
    primary: '#2563eb',
    primaryLight: 'rgba(37, 99, 235, 0.15)',
    success: '#059669',
    danger: '#dc2626',
    warning: '#d97706',
    purple: '#7c3aed',
    pink: '#db2777',
    teal: '#0d9488',
    gray400: '#94a3b8',
    gray500: '#64748b',
    gray600: '#475569',
    gray700: '#334155',
    gridColor: 'rgba(0,0,0,0.06)',
    tooltipBg: '#1e293b',
    tooltipText: '#f1f5f9'
};

document.addEventListener('DOMContentLoaded', function () {
    initNavigation();
    loadAllData();
});

function initNavigation() {
    const links = document.querySelectorAll('.sidebar .nav-link');
    const toggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');

    links.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const section = this.dataset.section;
            links.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            document.querySelectorAll('.section-content').forEach(s => s.classList.remove('active'));
            const el = document.getElementById('section-' + section);
            if (el) el.classList.add('active');
            if (window.innerWidth <= 768) sidebar.classList.remove('show');
            renderSectionCharts(section);
        });
    });

    toggle.addEventListener('click', function () {
        sidebar.classList.toggle('show');
    });
}

function renderSectionCharts(section) {
    setTimeout(() => {
        switch (section) {
            case 'dashboard': createDashboardCharts(); break;
            case 'exploratorio': createExploratorioCharts(); break;
            case 'preprocesamiento': createPreproChart(); break;
            case 'entrenamiento': createSplitChart(); break;
            case 'predicciones': createPrediccionCharts(); break;
            case 'importancia': createImportanciaChart(); break;
        }
    }, 100);
}

async function loadAllData() {
    try {
        const res = await fetch('/api/info_completa');
        state.infoCompleta = await res.json();
        renderDashboard();
        renderDashboardCharts();
        renderExploratorio();
        renderVariables();
        renderPreprocesamiento();
        renderEntrenamiento();
        renderEvaluacion();
        renderPredicciones();
        renderImportancia();
        renderConclusiones();
        const badge = document.getElementById('statusBadge');
        badge.textContent = 'Datos cargados';
        badge.className = 'badge bg-success badge-status';
    } catch (err) {
        console.error(err);
        const badge = document.getElementById('statusBadge');
        badge.textContent = 'Error';
        badge.className = 'badge bg-danger badge-status';
    }
}

function destroyChart(id) {
    if (state.charts[id]) { state.charts[id].destroy(); delete state.charts[id]; }
}

function getCtx(id) {
    const el = document.getElementById(id);
    return el ? el.getContext('2d') : null;
}

function renderDashboard() {
    const info = state.infoCompleta;
    if (!info || !info.informacion_inicial) return;
    const ini = info.informacion_inicial;
    document.getElementById('totalRegistros').textContent = ini.tamano || '--';
    document.getElementById('totalVariables').textContent = (ini.variables || '--').split('+')[0] || '--';
    document.getElementById('totalNulos').textContent = info.reporte_preprocesamiento?.nulos_iniciales || 0;
    document.getElementById('varObjetivo').textContent = (info.informacion_inicial?.variable_objetivo || '--').split(' - ')[0];
    document.getElementById('resumenDataset').innerHTML = `
        <p><strong>Dataset:</strong> ${ini.dataset || ''}</p>
        <p><strong>Origen:</strong> ${ini.origen || ''}</p>
        <p class="mb-0"><strong>Descripcion:</strong><br><small class="text-muted">${ini.descripcion || ''}</small></p>
        <hr>
        <p><strong>Registros:</strong> ${ini.tamano || '--'}</p>
        <p><strong>${ini.variables || ''}</strong></p>
        <p class="mb-0"><strong>Variable Objetivo:</strong><br><span class="text-primary fw-bold">${ini.variable_objetivo || 'MedianHouseValue'}</span></p>
    `;
}

function renderDashboardCharts() {
    const dist = state.infoCompleta?.distribuciones?.MedianHouseValue;
    if (!dist || !dist.valores || !dist.valores.length) return;
    const ctx = getCtx('chartDistribucionPrecio');
    if (!ctx) return;
    destroyChart('chartDistribucionPrecio');
    state.charts.chartDistribucionPrecio = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dist.edges.slice(0, -1).map(v => '$' + Math.round(v / 10000) + 'K'),
            datasets: [{ label: 'Frecuencia', data: dist.valores, backgroundColor: C.primaryLight, borderColor: C.primary, borderWidth: 1, borderRadius: 3 }]
        },
        options: chartOpts({ xTicks: dist.edges.slice(0, -1).map(v => '$' + Math.round(v / 10000) + 'K') })
    });
}

function createDashboardCharts() { renderDashboardCharts(); }

function renderExploratorio() {
    const resumen = state.infoCompleta?.resumen_valores || {};
    const tbody = document.querySelector('#statsTable tbody');
    if (tbody && Object.keys(resumen).length) {
        tbody.innerHTML = '';
        Object.entries(resumen).forEach(([k, v]) => {
            tbody.innerHTML += `<tr><td class="fw-medium">${k}</td><td>${fmt(v.media)}</td><td>${fmt(v.mediana)}</td><td>${fmt(v.moda)}</td><td>${fmt(v.std)}</td><td>${fmt(v.minimo)}</td><td>${fmt(v.maximo)}</td></tr>`;
        });
    }
    loadDataTable();
}

function createExploratorioCharts() {
    const dists = state.infoCompleta?.distribuciones || {};
    [
        { id: 'chartIngresos', data: dists.MedInc, label: 'Ingreso Medio', color: C.primary },
        { id: 'chartPrecio', data: dists.MedianHouseValue, label: 'Precio Vivienda', color: C.teal },
        { id: 'chartHabitaciones', data: dists.AveRooms, label: 'Habitaciones', color: C.warning },
        { id: 'chartPoblacion', data: dists.Population, label: 'Poblacion', color: C.danger }
    ].forEach(cfg => {
        if (!cfg.data || !cfg.data.valores || !cfg.data.valores.length) return;
        const ctx = getCtx(cfg.id);
        if (!ctx) return;
        destroyChart(cfg.id);
        state.charts[cfg.id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: (cfg.data.edges || []).slice(0, -1).map((_, i) => 'B' + (i + 1)),
                datasets: [{ label: cfg.label, data: cfg.data.valores, backgroundColor: cfg.color + '22', borderColor: cfg.color, borderWidth: 1, borderRadius: 3 }]
            },
            options: chartOpts({})
        });
    });
}

function loadDataTable() {
    fetch('/api/datos_tabla').then(r => r.json()).then(data => {
        state.datosTabla = data.data;
        renderTablePage(1);
    });
}

function renderTablePage(page) {
    const data = state.datosTabla;
    if (!data || !data.length) return;
    state.tablaPage = page;
    const ps = state.tablaPageSize;
    const start = (page - 1) * ps, end = Math.min(start + ps, data.length), pageData = data.slice(start, end);
    const cols = Object.keys(data[0] || {});
    document.getElementById('tablaHead').innerHTML = cols.map(c => `<th>${c}</th>`).join('');
    document.getElementById('tablaBody').innerHTML = pageData.map(r => '<tr>' + cols.map(c => `<td>${cell(r[c])}</td>`).join('') + '</tr>').join('');
    document.getElementById('tablaInfo').textContent = `Mostrando ${start + 1}-${end} de ${data.length} registros`;
    document.getElementById('tablaPagina').textContent = `Pagina ${page} de ${Math.ceil(data.length / ps)}`;
    document.getElementById('tablaPrev').disabled = page <= 1;
    document.getElementById('tablaNext').disabled = end >= data.length;
    document.getElementById('tablaPrev').onclick = () => renderTablePage(page - 1);
    document.getElementById('tablaNext').onclick = () => renderTablePage(page + 1);
    document.getElementById('tablaBuscar').oninput = function () {
        const q = this.value.toLowerCase();
        if (!q) { renderTablePage(1); return; }
        const filtered = data.filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(q)));
        state.datosTabla = filtered;
        renderTablePage(1);
        document.getElementById('tablaInfo').textContent = `Mostrando ${filtered.length} resultados`;
    };
}

function renderVariables() {
    const vars = state.infoCompleta?.info_entrenamiento?.variables_independientes || [];
    const desc = { MedInc: 'Ingreso medio (decenas de miles USD)', HouseAge: 'Edad media de las viviendas', AveRooms: 'Promedio de habitaciones', AveBedrms: 'Promedio de dormitorios', Population: 'Poblacion total', AveOccup: 'Promedio de ocupantes', Latitude: 'Latitud geografica', Longitude: 'Longitud geografica' };
    const list = document.getElementById('varsIndependientes');
    if (!list) return;
    list.innerHTML = vars.map(v => `<li class="list-group-item d-flex justify-content-between align-items-start"><div><strong>${v}</strong><br><small class="text-muted">${desc[v] || 'Variable predictora'}</small></div><span class="badge bg-primary rounded-pill">Predictora</span></li>`).join('');
}

function renderPreprocesamiento() {
    const rep = state.infoCompleta?.reporte_preprocesamiento;
    if (!rep) return;
    document.getElementById('preproCards').innerHTML = [
        { icon: 'bi-exclamation-triangle', label: 'Nulos Iniciales', value: rep.nulos_iniciales, color: C.danger },
        { icon: 'bi-check-circle', label: 'Nulos Finales', value: rep.nulos_final, color: C.success },
        { icon: 'bi-files', label: 'Duplicados', value: rep.duplicados, color: C.warning },
        { icon: 'bi-box', label: 'Outliers', value: rep.outliers_detectados, color: C.primary }
    ].map(c => `<div class="col-md-3"><div class="card stat-card"><div class="card-body"><div class="stat-icon" style="color:${c.color}"><i class="bi ${c.icon}"></i></div><h6 class="stat-label">${c.label}</h6><h2 class="stat-value" style="color:${c.color}">${c.value}</h2></div></div></div>`).join('');
    const det = document.getElementById('detallePrepro');
    det.innerHTML = `<div class="row"><div class="col-md-6"><h6 class="text-primary mb-3">Valores Nulos</h6><p><strong>Detectados:</strong> ${rep.nulos_iniciales} en ${Object.keys(rep.nulos_por_columna||{}).length} columna(s)</p>${Object.entries(rep.nulos_por_columna||{}).map(([c,n]) => `<p class="ms-3 small"><i class="bi bi-dot"></i> ${c}: ${n}</p>`).join('')}<p><strong>Metodo:</strong> ${rep.metodo_nulos}</p><p><strong>Resultado:</strong> ${rep.nulos_final} nulos</p></div><div class="col-md-6"><h6 class="text-primary mb-3">Transformaciones</h6><p><strong>Duplicados:</strong> ${rep.duplicados}</p><p><strong>Categoricas:</strong> ${(rep.variables_categoricas||[]).length > 0 ? rep.variables_categoricas.join(', ') : 'Ninguna'}</p><p><strong>Codificacion:</strong> ${rep.codificacion}</p><p><strong>Outliers:</strong> ${rep.outliers_detectados} - ${rep.metodo_outliers}</p><p><strong>Normalizacion:</strong> ${rep.normalizacion}</p></div></div>`;
}

function createPreproChart() {
    const dist = state.infoCompleta?.distribuciones?.MedInc;
    if (!dist || !dist.valores || !dist.valores.length) return;
    const ctx = getCtx('chartPrepro');
    if (!ctx) return;
    destroyChart('chartPrepro');
    const labels = (dist.edges || []).slice(0, -1).map((v, i) => ((v + dist.edges[i + 1]) / 2).toFixed(2)).slice(0, 20);
    state.charts.chartPrepro = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Ingreso Medio (estandarizado)', data: (dist.valores || []).slice(0, 20), backgroundColor: C.primaryLight, borderColor: C.primary, borderWidth: 1, borderRadius: 3 }] },
        options: chartOpts({ xTitle: 'Rango de valores', yTitle: 'Frecuencia' })
    });
}

function renderEntrenamiento() {
    const info = state.infoCompleta?.info_entrenamiento;
    if (!info) return;
    document.getElementById('paramsEntrenamiento').innerHTML = `
        <div class="d-flex align-items-center mb-3"><i class="bi bi-cpu fs-2 text-primary me-3"></i><div><h5 class="mb-0">${info.algoritmo||'LinearRegression()'}</h5><small class="text-muted">${info.libreria||'Scikit-Learn'}</small></div></div>
        <hr><div class="row"><div class="col-6 mb-2"><small class="text-muted d-block">Division</small><strong>${info.split||'80/20'}</strong></div><div class="col-6 mb-2"><small class="text-muted d-block">Random State</small><strong>${info.random_state||42}</strong></div><div class="col-6 mb-2"><small class="text-muted d-block">Train</small><strong>${fmt(info.train_samples)} (80%)</strong></div><div class="col-6 mb-2"><small class="text-muted d-block">Test</small><strong>${fmt(info.test_samples)} (20%)</strong></div></div>
        <hr><small class="text-muted">Variable Dependiente:</small><p><strong class="text-primary">${info.variable_dependiente||'MedianHouseValue'}</strong></p><small class="text-muted">Independientes:</small><p class="small">${(info.variables_independientes||[]).join(', ')}</p>`;
    document.getElementById('splitInfo').innerHTML = `
        <h5 class="mb-3">Distribucion de la Muestra</h5>
        <div class="mb-2"><div class="d-flex justify-content-between mb-1"><span>Entrenamiento (80%)</span><span class="text-primary fw-bold">${fmt(info.train_samples)}</span></div><div class="progress" style="height:10px"><div class="progress-bar bg-primary" style="width:80%"></div></div></div>
        <div><div class="d-flex justify-content-between mb-1"><span>Prueba (20%)</span><span class="text-primary fw-bold">${fmt(info.test_samples)}</span></div><div class="progress" style="height:10px"><div class="progress-bar bg-warning" style="width:20%"></div></div></div>`;
}

function createSplitChart() {
    const info = state.infoCompleta?.info_entrenamiento;
    if (!info) return;
    const ctx = getCtx('chartSplit');
    if (!ctx) return;
    destroyChart('chartSplit');
    state.charts.chartSplit = new Chart(ctx, {
        type: 'doughnut',
        data: { labels: ['Entrenamiento (80%)', 'Prueba (20%)'], datasets: [{ data: [info.train_samples || 80, info.test_samples || 20], backgroundColor: [C.primary, C.warning], borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { padding: 15, color: C.gray600 } } } }
    });
}

function renderEvaluacion() {
    const met = state.infoCompleta?.metricas;
    if (!met) return;
    const items = [
        { label: 'MAE', value: '$' + fmt(met.mae), desc: 'Error Absoluto Medio', color: C.primary, interp: 'Error promedio de las predicciones.' },
        { label: 'MSE', value: '$' + fmt(met.mse), desc: 'Error Cuadratico Medio', color: C.warning, interp: 'Penaliza errores grandes al elevarlos al cuadrado.' },
        { label: 'RMSE', value: '$' + fmt(met.rmse), desc: 'Raiz Error Cuadratico Medio', color: C.danger, interp: 'Error tipico en las mismas unidades que la variable objetivo.' },
        { label: 'R²', value: (met.r2 * 100).toFixed(1) + '%', desc: 'Coeficiente Determinacion', color: C.success, interp: 'El modelo explica el ' + (met.r2 * 100).toFixed(1) + '% de la variabilidad.' }
    ];
    document.getElementById('metricCards').innerHTML = items.map(m => `<div class="col-md-6 col-lg-3"><div class="card metric-card"><div class="card-body"><div class="stat-icon" style="color:${m.color};background:${m.color}15"><i class="bi ${m.icon || 'bi-bar-chart'}"></i></div><div class="metric-label">${m.label}</div><div class="metric-value" style="color:${m.color}">${m.value}</div><div class="metric-desc">${m.desc}</div></div></div></div>`).join('');
    const interp = document.getElementById('interpretacionMetricas');
    interp.innerHTML = items.map(m => `<div class="d-flex align-items-start mb-2 p-3" style="background:${C.gray400}08;border-radius:6px;"><span class="badge me-3" style="background:${m.color};min-width:50px">${m.label}</span><div><strong>${m.value}</strong> - ${m.interp}</div></div>`).join('') +
        `<div class="alert mt-3" style="background:${C.primaryLight};border:1px solid ${C.primary};color:${C.gray700};"> <i class="bi bi-info-circle text-primary me-2"></i><strong>Interpretacion general:</strong> Un R² de ${(met.r2*100).toFixed(1)}% indica que el modelo ${met.r2 >= 0.7 ? 'tiene buen poder predictivo.' : met.r2 >= 0.5 ? 'captura tendencias importantes pero es mejorable.' : 'es limitado, se recomienda explorar modelos mas complejos.'}</div>`;
}

function renderPredicciones() {
    const p = state.infoCompleta?.predicciones;
    if (!p || !p.y_test || !p.y_pred) return;
    const tbody = document.querySelector('#tablaComparativa tbody');
    if (!tbody) return;
    const n = Math.min(p.y_test.length, 10);
    tbody.innerHTML = '';
    for (let i = 0; i < n; i++) {
        const d = p.y_test[i] - p.y_pred[i];
        const pct = p.y_test[i] !== 0 ? Math.abs(d / p.y_test[i]) * 100 : 0;
        tbody.innerHTML += `<tr><td>${i+1}</td><td>$${fmt(p.y_test[i])}</td><td>$${fmt(p.y_pred[i])}</td><td class="${d>=0?'text-success':'text-danger'}">${d>=0?'+':''}$${fmt(d)}</td><td>${pct.toFixed(2)}%</td></tr>`;
    }
}

function createPrediccionCharts() {
    const p = state.infoCompleta?.predicciones;
    if (!p || !p.y_test || !p.y_pred) return;
    const n = Math.min(p.y_test.length, 200);
    const scatter = [];
    for (let i = 0; i < n; i++) scatter.push({ x: p.y_test[i], y: p.y_pred[i] });
    const minV = Math.min(...p.y_test.slice(0, n), ...p.y_pred.slice(0, n));
    const maxV = Math.max(...p.y_test.slice(0, n), ...p.y_pred.slice(0, n));

    let ctx = getCtx('chartScatter');
    if (ctx) {
        destroyChart('chartScatter');
        state.charts.chartScatter = new Chart(ctx, {
            type: 'scatter',
            data: { datasets: [{ label: 'Real vs Predicho', data: scatter, backgroundColor: C.primaryLight, borderColor: C.primary, pointRadius: 3, pointHoverRadius: 6 }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: { color: C.gray600 } }, tooltip: { callbacks: { label: c => 'Real: $' + fmt(c.parsed.x) + ', Pred: $' + fmt(c.parsed.y) } } },
                scales: { x: { title: { display: true, text: 'Valor Real (USD)', color: C.gray500 }, ticks: { color: C.gray500 }, grid: { color: C.gridColor }, min: minV * 0.9, max: maxV * 1.1 }, y: { title: { display: true, text: 'Valor Predicho (USD)', color: C.gray500 }, ticks: { color: C.gray500 }, grid: { color: C.gridColor }, min: minV * 0.9, max: maxV * 1.1 } }
            }
        });
    }

    ctx = getCtx('chartLineas');
    if (ctx) {
        const sn = Math.min(p.y_test.length, 100);
        const labels = Array.from({ length: sn }, (_, i) => i + 1);
        destroyChart('chartLineas');
        state.charts.chartLineas = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    { label: 'Valor Real', data: p.y_test.slice(0, sn), borderColor: C.primary, backgroundColor: C.primaryLight, fill: true, tension: 0.3, pointRadius: 1 },
                    { label: 'Valor Predicho', data: p.y_pred.slice(0, sn), borderColor: C.success, backgroundColor: 'rgba(5,150,105,0.1)', fill: true, tension: 0.3, pointRadius: 1 }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: { color: C.gray600 } } },
                scales: { x: { title: { display: true, text: 'Muestra #', color: C.gray500 }, ticks: { color: C.gray500 }, grid: { color: C.gridColor } }, y: { title: { display: true, text: 'Valor (USD)', color: C.gray500 }, ticks: { color: C.gray500 }, grid: { color: C.gridColor } } }
            }
        });
    }
}

function createImportanciaChart() {
    const fi = state.infoCompleta?.feature_importance;
    if (!fi || !fi.length) return;
    const sorted = [...fi].sort((a, b) => Math.abs(b.abs_coeficiente) - Math.abs(a.abs_coeficiente));
    const ctx = getCtx('chartImportancia');
    if (!ctx) return;
    destroyChart('chartImportancia');
    const colors = sorted.map(v => v.coeficiente >= 0 ? 'rgba(5,150,105,0.6)' : 'rgba(220,38,38,0.6)');
    const borders = sorted.map(v => v.coeficiente >= 0 ? C.success : C.danger);
    state.charts.chartImportancia = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sorted.map(v => v.variable),
            datasets: [{ label: 'Coeficiente', data: sorted.map(v => v.coeficiente), backgroundColor: colors, borderColor: borders, borderWidth: 1, borderRadius: 3 }]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { ticks: { color: C.gray500 }, grid: { color: C.gridColor } }, y: { ticks: { color: C.gray700 }, grid: { display: false } } }
        }
    });
}

function renderImportancia() {
    const fi = state.infoCompleta?.feature_importance;
    if (!fi || !fi.length) return;
    const sorted = [...fi].sort((a, b) => Math.abs(b.abs_coeficiente) - Math.abs(a.abs_coeficiente));
    const div = document.getElementById('topVariables');
    div.innerHTML = sorted.slice(0, 5).map((v, i) => {
        const medal = i === 0 ? '1' : i === 1 ? '2' : i === 2 ? '3' : '' + (i + 1);
        const pos = v.coeficiente >= 0;
        return `<div class="d-flex align-items-center p-2 mb-1" style="background:${C.gray400}08;border-radius:6px;"><span class="badge bg-primary me-2">${medal}</span><div class="flex-grow-1"><strong class="small">${v.variable}</strong><br><small class="${pos?'text-success':'text-danger'}">Coef: ${v.coeficiente.toFixed(4)} (${pos?'positiva':'negativa'})</small></div></div>`;
    }).join('');
}

function renderConclusiones() {
    const conc = state.infoCompleta?.conclusiones;
    if (!conc || !conc.length) return;
    document.getElementById('conclusionesContent').innerHTML = conc.map(c => `<p><i class="bi bi-arrow-right-circle text-primary me-2"></i>${c}</p>`).join('');
}

function chartOpts(extra) {
    return {
        responsive: true, maintainAspectRatio: false,
        plugins: {
            legend: { labels: { color: C.gray600 } },
            tooltip: { backgroundColor: C.tooltipBg, titleColor: C.tooltipText, bodyColor: C.tooltipText }
        },
        scales: {
            x: { ticks: { color: C.gray500 }, grid: { color: C.gridColor }, title: extra.xTitle ? { display: true, text: extra.xTitle, color: C.gray500 } : undefined },
            y: { ticks: { color: C.gray500 }, grid: { color: C.gridColor }, title: extra.yTitle ? { display: true, text: extra.yTitle, color: C.gray500 } : undefined }
        }
    };
}

function fmt(n) {
    if (n === null || n === undefined || isNaN(n)) return '--';
    return Number(n).toLocaleString('en-US', { maximumFractionDigits: 2, minimumFractionDigits: 0 });
}

function cell(v) {
    if (v === null || v === undefined) return '<span class="text-muted">N/A</span>';
    if (typeof v === 'number') return Number.isInteger(v) ? v.toLocaleString() : v.toFixed(4);
    return String(v);
}
