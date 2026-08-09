/**
 * Baloto Oracle - Main Application
 * Handles data loading, visualizations, and interactivity
 */

// ==========================================================================
// Configuration & Constants
// ==========================================================================
const CONFIG = {
    apiBase: 'data/processed/',
    charts: {
        colors: {
            primary: '#00d4aa',
            secondary: '#6366f1',
            tertiary: '#f59e0b',
            danger: '#ef4444',
            warning: '#f97316',
            info: '#3b82f6'
        },
        gradients: {
            primary: ['#00d4aa', '#00b894'],
            secondary: ['#6366f1', '#818cf8'],
            warm: ['#f59e0b', '#f97316'],
            cool: ['#3b82f6', '#06b6d4']
        }
    },
    animation: {
        duration: 1000,
        easing: 'easeOutQuart'
    }
};

// Ball colors for numbers 1-43
const BALL_COLORS = [
    '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
    '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
    '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
    '#ec4899', '#f43f5e', '#ef4444', '#f97316', '#f59e0b',
    '#eab308', '#84cc16', '#22c55e', '#10b981', '#14b8a6',
    '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6',
    '#a855f7', '#d946ef', '#ec4899', '#f43f5e', '#ef4444',
    '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e',
    '#10b981', '#14b8a6', '#06b6d4'
];

// ==========================================================================
// State Management
// ==========================================================================
const state = {
    data: {
        baloto: null,
        revancha: null,
        metadata: null,
        analysis: null
    },
    charts: {},
    currentTheme: 'dark',
    filters: {
        game: 'baloto',
        period: 'all',
        vizType: 'frequency'
    }
};

// ==========================================================================
// Utility Functions
// ==========================================================================
const utils = {
    formatNumber: (num) => new Intl.NumberFormat('es-CO').format(num),
    
    formatDate: (dateStr) => {
        const date = new Date(dateStr + 'T00:00:00');
        return date.toLocaleDateString('es-CO', {
            weekday: 'short',
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    },
    
    formatJackpot: (amount) => {
        if (amount >= 1e12) return `$${(amount / 1e12).toFixed(1)}B`;
        if (amount >= 1e9) return `$${(amount / 1e9).toFixed(1)}M`;
        if (amount >= 1e6) return `$${(amount / 1e6).toFixed(1)}K`;
        return utils.formatNumber(amount);
    },
    
    getBallColor: (num) => BALL_COLORS[(num - 1) % BALL_COLORS.length],
    
    createBall: (num, size = 32, superbalota = false) => {
        const ball = document.createElement('span');
        ball.className = `ball ${superbalota ? 'superbalota' : ''}`;
        ball.style.width = `${size}px`;
        ball.style.height = `${size}px`;
        ball.style.fontSize = `${size * 0.4}px`;
        ball.textContent = num.toString().padStart(2, '0');
        
        if (superbalota) {
            ball.style.background = 'var(--bg-card)';
            ball.style.color = 'var(--accent-tertiary)';
            ball.style.border = '2px solid var(--accent-tertiary)';
        } else {
            ball.style.background = utils.getBallColor(num);
            ball.style.color = 'white';
        }
        return ball;
    },
    
    showToast: (message, type = 'info') => {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    ${type === 'success' ? '<polyline points="20 6 9 17 4 12"></polyline>' : ''}
                    ${type === 'error' ? '<circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>' : ''}
                    ${type === 'info' ? '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>' : ''}
                </svg>
            </div>
            <span class="toast-message">${message}</span>
            <button class="toast-close" aria-label="Cerrar">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        `;
        
        toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
        container.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
    },
    
    debounce: (fn, delay) => {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn(...args), delay);
        };
    },
    
    animateValue: (element, start, end, duration = 1000) => {
        const startTime = performance.now();
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = start + (end - start) * eased;
            element.textContent = utils.formatNumber(Math.round(current));
            if (progress < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
    }
};

// ==========================================================================
// Data Loading
// ==========================================================================
async function loadData() {
    try {
        showLoading(true);
        
        const [balotoRes, revanchaRes, metadataRes, analysisRes] = await Promise.all([
            fetch(`${CONFIG.apiBase}baloto.json`),
            fetch(`${CONFIG.apiBase}revancha.json`),
            fetch(`${CONFIG.apiBase}metadata.json`),
            fetch(`${CONFIG.apiBase}analysis_results.json`)
        ]);
        
        state.data.baloto = await balotoRes.json();
        state.data.revancha = await revanchaRes.json();
        state.data.metadata = await metadataRes.json();
        state.data.analysis = await analysisRes.json();
        
        // Sort by date descending
        state.data.baloto.sort((a, b) => new Date(b.date) - new Date(a.date));
        state.data.revancha.sort((a, b) => new Date(b.date) - new Date(a.date));
        
        updateHeroStats();
        initializeCharts();
        populateLatestDraws();
        populatePredictions();
        initializeVisualizer();
        
        showLoading(false);
        utils.showToast('Datos cargados correctamente', 'success');
        hideErrorState();
    } catch (error) {
        console.error('Error loading data:', error);
        showLoading(false);
        utils.showToast('Error cargando los datos. Verifique su conexión e intente nuevamente.', 'error');
        showErrorState();
    }
}

function showErrorState() {
    const main = document.querySelector('.main-content');
    if (main) main.style.display = 'none';

    const hero = document.querySelector('.hero');
    if (hero) hero.style.display = 'none';

    const errorPanel = document.getElementById('error-panel');
    if (errorPanel) {
        errorPanel.style.display = 'flex';
    }
}

function hideErrorState() {
    const main = document.querySelector('.main-content');
    if (main) main.style.display = '';

    const hero = document.querySelector('.hero');
    if (hero) hero.style.display = '';

    const errorPanel = document.getElementById('error-panel');
    if (errorPanel) {
        errorPanel.style.display = 'none';
    }
}

function showLoading(show) {
    document.querySelectorAll('.chart-wrapper').forEach(wrapper => {
        if (show) {
            wrapper.classList.add('loading');
            wrapper.innerHTML = '<div class="skeleton" style="width:100%;height:300px;"></div>';
        } else {
            wrapper.classList.remove('loading');
        }
    });
}

// ==========================================================================
// Hero Stats Update
// ==========================================================================
function updateHeroStats() {
    const { baloto, metadata } = state.data;
    
    if (!baloto || baloto.length === 0) return;
    
    // Total draws
    const totalDrawsEl = document.getElementById('total-draws');
    utils.animateValue(totalDrawsEl, 0, baloto.length);
    
    // Date range
    const dateRangeEl = document.getElementById('date-range');
    if (metadata?.date_range) {
        const start = utils.formatDate(metadata.date_range.start);
        const end = utils.formatDate(metadata.date_range.end);
        dateRangeEl.textContent = `${start} - ${end}`;
    }
    
    // Last update
    const lastUpdateEl = document.getElementById('last-update');
    if (metadata?.last_updated) {
        lastUpdateEl.textContent = utils.formatDate(metadata.last_updated.split('T')[0]);
    } else {
        lastUpdateEl.textContent = utils.formatDate(baloto[0].date);
    }
    
    // Current jackpot
    const jackpotEl = document.getElementById('current-jackpot');
    if (baloto[0]?.jackpot) {
        jackpotEl.textContent = utils.formatJackpot(baloto[0].jackpot);
    }
}

// ==========================================================================
// Chart Initialization
// ==========================================================================
function initializeCharts() {
    createFrequencyHeatmap();
    createSuperbalotaChart();
    createPositionChart();
    createSumChart();
    createOddEvenChart();
    createHighLowChart();
    createConsecutiveChart();
    createGapsChart();
    createComparisonChart();
    createProbabilityChart();
    createHeroChart();
    renderInferentialTests();
    renderInterpretation();
    renderPredictiveModeling();
}

function getChartColors(count, scheme = 'primary') {
    const colors = CONFIG.charts.gradients[scheme] || CONFIG.charts.gradients.primary;
    return Array.from({length: count}, (_, i) => {
        const ratio = i / Math.max(count - 1, 1);
        return interpolateColor(colors[0], colors[1], ratio);
    });
}

function interpolateColor(color1, color2, factor) {
    const c1 = hexToRgb(color1);
    const c2 = hexToRgb(color2);
    if (!c1 || !c2) return color1;
    const r = Math.round(c1.r + (c2.r - c1.r) * factor);
    const g = Math.round(c1.g + (c2.g - c1.g) * factor);
    const b = Math.round(c1.b + (c2.b - c1.b) * factor);
    return `rgb(${r}, ${g}, ${b})`;
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? { r: parseInt(result[1], 16), g: parseInt(result[2], 16), b: parseInt(result[3], 16) } : null;
}

// ==========================================================================
// Frequency Heatmap (D3)
// ==========================================================================
function createFrequencyHeatmap() {
    const container = d3.select('#frequency-heatmap');
    container.selectAll('*').remove();
    
    const freqData = state.data.analysis?.descriptive?.number_frequencies?.frequencies || {};
    const numbers = Object.keys(freqData).map(Number).sort((a, b) => a - b);
    
    if (numbers.length === 0) {
        container.html('<div class="no-data">No hay datos disponibles</div>');
        return;
    }
    
    const maxFreq = Math.max(...Object.values(freqData).map(d => d.count));
    const minFreq = Math.min(...Object.values(freqData).map(d => d.count));
    
    const width = container.node().getBoundingClientRect().width || 600;
    const cellSize = Math.floor((width - 40) / 7);
    const height = cellSize * 7 + 40;
    
    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height)
        .style('font-family', 'var(--font-sans)');
    
    // Color scale
    const colorScale = d3.scaleSequential(d3.interpolateViridis)
        .domain([minFreq, maxFreq]);
    
    // Create cells
    const cells = svg.selectAll('g')
        .data(numbers)
        .enter()
        .append('g')
        .attr('transform', (d, i) => {
            const col = (d - 1) % 7;
            const row = Math.floor((d - 1) / 7);
            return `translate(${20 + col * (cellSize + 4)}, ${20 + row * (cellSize + 4)})`;
        });
    
    cells.append('rect')
        .attr('width', cellSize)
        .attr('height', cellSize)
        .attr('rx', 6)
        .attr('fill', d => colorScale(freqData[d].count))
        .attr('stroke', 'var(--border-color)')
        .attr('stroke-width', 1)
        .on('mouseover', function(event, d) {
            d3.select(this).attr('stroke', 'var(--accent-primary)').attr('stroke-width', 2);
            showTooltip(event, d, freqData[d]);
        })
        .on('mouseout', function() {
            d3.select(this).attr('stroke', 'var(--border-color)').attr('stroke-width', 1);
            hideTooltip();
        });
    
    cells.append('text')
        .attr('x', cellSize / 2)
        .attr('y', cellSize / 2 - 4)
        .attr('text-anchor', 'middle')
        .attr('font-size', '11px')
        .attr('font-weight', 600)
        .attr('fill', 'white')
        .text(d => d.toString().padStart(2, '0'));
    
    cells.append('text')
        .attr('x', cellSize / 2)
        .attr('y', cellSize / 2 + 10)
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px')
        .attr('fill', 'rgba(255,255,255,0.7)')
        .text(d => freqData[d].count);
    
    // Legend
    createHeatmapLegend(container, colorScale, minFreq, maxFreq);
}

function createHeatmapLegend(container, colorScale, min, max) {
    const legendContainer = d3.select('#freq-legend');
    legendContainer.selectAll('*').remove();
    
    const svg = legendContainer.append('svg')
        .attr('width', '100%')
        .attr('height', 30);
    
    const gradient = svg.append('defs')
        .append('linearGradient')
        .attr('id', 'freq-gradient')
        .attr('x1', '0%').attr('y1', '0%')
        .attr('x2', '100%').attr('y2', '0%');
    
    gradient.selectAll('stop')
        .data(d3.range(0, 1.01, 0.1))
        .enter()
        .append('stop')
        .attr('offset', d => `${d * 100}%`)
        .attr('stop-color', d => colorScale(min + (max - min) * d));
    
    svg.append('rect')
        .attr('x', 0).attr('y', 5)
        .attr('width', '100%').attr('height', 15)
        .attr('rx', 3)
        .style('fill', 'url(#freq-gradient)');
    
    svg.append('text')
        .attr('x', 0).attr('y', 4)
        .attr('font-size', '10px')
        .attr('fill', 'var(--text-muted)')
        .text(`Menos frecuente (${min})`);
    
    svg.append('text')
        .attr('x', '100%').attr('y', 4)
        .attr('text-anchor', 'end')
        .attr('font-size', '10px')
        .attr('fill', 'var(--text-muted)')
        .text(`Más frecuente (${max})`);
}

let tooltip = null;
function showTooltip(event, number, data) {
    if (!tooltip) {
        tooltip = d3.select('body').append('div')
            .attr('class', 'd3-tooltip')
            .style('position', 'absolute')
            .style('padding', '10px')
            .style('background', 'var(--bg-card)')
            .style('border', '1px solid var(--border-color)')
            .style('border-radius', '8px')
            .style('pointer-events', 'none')
            .style('z-index', 1000)
            .style('font-size', '12px')
            .style('box-shadow', 'var(--shadow-lg)');
    }
    
    tooltip.html(`
        <strong>Número ${number}</strong><br>
        Frecuencia: ${data.count} (${data.percentage}%)<br>
        Esperado: ${data.expected}<br>
        Desviación: ${data.deviation > 0 ? '+' : ''}${data.deviation}<br>
        Z-score: ${data.z_score}
    `)
    .style('left', (event.pageX + 10) + 'px')
    .style('top', (event.pageY - 10) + 'px')
    .style('opacity', 1);
}

function hideTooltip() {
    if (tooltip) tooltip.style('opacity', 0);
}

// ==========================================================================
// Chart.js Charts
// ==========================================================================
function createSuperbalotaChart() {
    const ctx = document.getElementById('superbalota-chart');
    if (!ctx) return;
    
    const freqData = state.data.analysis?.descriptive?.superbalota_frequencies?.frequencies || {};
    const numbers = Object.keys(freqData).map(Number).sort((a, b) => a - b);
    const counts = numbers.map(n => freqData[n].count);
    const percentages = numbers.map(n => freqData[n].percentage);
    
    destroyChart('superbalota');
    state.charts.superbalota = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: numbers.map(n => n.toString().padStart(2, '0')),
            datasets: [{
                label: 'Frecuencia',
                data: counts,
                backgroundColor: numbers.map((n, i) => 
                    i < 3 ? 'rgba(0, 212, 170, 0.8)' : 
                    i > numbers.length - 4 ? 'rgba(239, 68, 68, 0.5)' : 
                    'rgba(99, 102, 241, 0.6)'
                ),
                borderColor: numbers.map((n, i) => 
                    i < 3 ? 'rgba(0, 212, 170, 1)' : 
                    i > numbers.length - 4 ? 'rgba(239, 68, 68, 1)' : 
                    'rgba(99, 102, 241, 1)'
                ),
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: getBarChartOptions('Frecuencia Superbalota', '%', true)
    });
}

function createPositionChart() {
    const ctx = document.getElementById('position-chart');
    if (!ctx) return;
    
    const posData = state.data.analysis?.descriptive?.position_frequencies || {};
    const positions = ['position_1', 'position_2', 'position_3', 'position_4', 'position_5'];
    const numbers = Array.from({length: 43}, (_, i) => i + 1);
    
    const datasets = positions.map((pos, idx) => {
        const freq = posData[pos]?.frequencies || {};
        return {
            label: `${idx + 1}ª Posición`,
            data: numbers.map(n => freq[n] || 0),
            borderColor: CONFIG.charts.gradients.primary[idx % 2 === 0 ? 0 : 1],
            backgroundColor: CONFIG.charts.gradients.primary[idx % 2 === 0 ? 0 : 1].replace(')', ', 0.1)').replace('rgb', 'rgba'),
            fill: false,
            tension: 0.3,
            pointRadius: 0,
            pointHoverRadius: 4
        };
    });
    
    destroyChart('position');
    state.charts.position = new Chart(ctx, {
        type: 'line',
        data: {
            labels: numbers.map(n => n.toString().padStart(2, '0')),
            datasets
        },
        options: getLineChartOptions('Frecuencia por Posición', 'Frecuencia')
    });
}

function createSumChart() {
    const ctx = document.getElementById('sum-chart');
    if (!ctx) return;
    
    const sumData = state.data.analysis?.descriptive?.sum_statistics || {};
    const distribution = sumData.distribution || {};
    const sums = Object.keys(distribution).map(Number).sort((a, b) => a - b);
    const counts = sums.map(s => distribution[s]);
    
    destroyChart('sum');
    state.charts.sum = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sums,
            datasets: [{
                label: 'Frecuencia',
                data: counts,
                backgroundColor: 'rgba(99, 102, 241, 0.6)',
                borderColor: 'rgba(99, 102, 241, 1)',
                borderWidth: 1,
                borderRadius: 2
            }]
        },
        options: getBarChartOptions('Distribución de Sumas', 'Frecuencia')
    });
    
    // Update stats summary
    const statsEl = document.getElementById('sum-stats');
    if (statsEl) {
        statsEl.innerHTML = `
            <div class="stat-mini"><span>Media:</span> <strong>${sumData.mean}</strong></div>
            <div class="stat-mini"><span>Mediana:</span> <strong>${sumData.median}</strong></div>
            <div class="stat-mini"><span>Desv. Est.:</span> <strong>${sumData.std}</strong></div>
            <div class="stat-mini"><span>Rango:</span> <strong>${sumData.min} - ${sumData.max}</strong></div>
        `;
    }
}

function createOddEvenChart() {
    const ctx = document.getElementById('oddeven-chart');
    if (!ctx) return;
    
    const oeData = state.data.analysis?.descriptive?.odd_even_balance || {};
    const dist = oeData.distribution || {};
    const labels = Object.keys(dist).sort();
    const data = labels.map(l => dist[l]);
    const percentages = labels.map(l => oeData.percentages[l]);
    
    destroyChart('oddeven');
    state.charts.oddeven = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => `${l.replace('-', ' Par / ')} Impar`),
            datasets: [{
                data,
                backgroundColor: [
                    'rgba(0, 212, 170, 0.8)',
                    'rgba(99, 102, 241, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(168, 85, 247, 0.8)',
                    'rgba(6, 182, 212, 0.8)'
                ],
                borderWidth: 0
            }]
        },
        options: {
            ...getDoughnutChartOptions(),
            plugins: {
                legend: { position: 'bottom', labels: { padding: 15, font: { size: 11 } } },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.label}: ${context.raw} (${percentages[context.dataIndex]}%)`
                    }
                }
            }
        }
    });
}

function createHighLowChart() {
    const ctx = document.getElementById('highlow-chart');
    if (!ctx) return;
    
    const hlData = state.data.analysis?.descriptive?.high_low_balance || {};
    const dist = hlData.distribution || {};
    const labels = Object.keys(dist).sort();
    const data = labels.map(l => dist[l]);
    const percentages = labels.map(l => hlData.percentages[l]);
    
    destroyChart('highlow');
    state.charts.highlow = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => `${l.replace('-', ' Alto / ')} Bajo`),
            datasets: [{
                data,
                backgroundColor: [
                    'rgba(0, 212, 170, 0.8)',
                    'rgba(99, 102, 241, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(168, 85, 247, 0.8)',
                    'rgba(6, 182, 212, 0.8)'
                ],
                borderWidth: 0
            }]
        },
        options: {
            ...getDoughnutChartOptions(),
            plugins: {
                legend: { position: 'bottom', labels: { padding: 15, font: { size: 11 } } },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.label}: ${context.raw} (${percentages[context.dataIndex]}%)`
                    }
                }
            }
        }
    });
}

function createConsecutiveChart() {
    const ctx = document.getElementById('consecutive-chart');
    if (!ctx) return;
    
    const consData = state.data.analysis?.descriptive?.consecutive_numbers || {};
    const dist = consData.distribution || {};
    const labels = Object.keys(dist).map(k => k === '0' ? 'Ninguno' : `${k} par${k > 1 ? 'es' : ''}`);
    const data = Object.values(dist);
    const percentages = Object.values(dist).map(v => ((v / Object.values(dist).reduce((a, b) => a + b, 0)) * 100).toFixed(1));
    
    destroyChart('consecutive');
    state.charts.consecutive = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Frecuencia',
                data,
                backgroundColor: 'rgba(245, 158, 11, 0.6)',
                borderColor: 'rgba(245, 158, 11, 1)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: getBarChartOptions('Números Consecutivos', 'Frecuencia')
    });
}

function createGapsChart() {
    const ctx = document.getElementById('gaps-chart');
    if (!ctx) return;
    
    const gapsData = state.data.analysis?.descriptive?.number_gaps || {};
    const dist = gapsData.gap_distribution || {};
    const gaps = Object.keys(dist).map(Number).sort((a, b) => a - b);
    const data = gaps.map(g => dist[g]);
    
    destroyChart('gaps');
    state.charts.gaps = new Chart(ctx, {
        type: 'line',
        data: {
            labels: gaps.map(g => `${g}`),
            datasets: [{
                label: 'Frecuencia',
                data,
                borderColor: 'rgba(6, 182, 212, 1)',
                backgroundColor: 'rgba(6, 182, 212, 0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: getLineChartOptions('Distribución de Gaps', 'Frecuencia')
    });
}

function createComparisonChart() {
    const ctx = document.getElementById('comparison-chart');
    if (!ctx) return;
    
    const balotoFreq = state.data.analysis?.descriptive?.number_frequencies?.frequencies || {};
    const revanchaFreq = state.data.analysis?.descriptive?.revancha_number_frequencies?.frequencies || {};
    
    const numbers = Array.from({length: 43}, (_, i) => i + 1);
    const balotoData = numbers.map(n => balotoFreq[n]?.count || 0);
    const revanchaData = numbers.map(n => revanchaFreq[n]?.count || 0);
    
    destroyChart('comparison');
    state.charts.comparison = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: numbers.map(n => n.toString().padStart(2, '0')),
            datasets: [
                {
                    label: 'Baloto',
                    data: balotoData,
                    backgroundColor: 'rgba(0, 212, 170, 0.6)',
                    borderColor: 'rgba(0, 212, 170, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Revancha',
                    data: revanchaData,
                    backgroundColor: 'rgba(99, 102, 241, 0.6)',
                    borderColor: 'rgba(99, 102, 241, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: getBarChartOptions('Comparativa Baloto vs Revancha', 'Frecuencia')
    });
}

function createProbabilityChart() {
    const ctx = document.getElementById('probability-chart');
    if (!ctx) return;
    
    const predData = state.data.analysis?.predictions?.next_draw_numbers?.probabilities || {};
    const numbers = Object.keys(predData).map(Number).sort((a, b) => a - b);
    const probs = numbers.map(n => predData[n] * 100);
    
    // Highlight top 5
    const top5 = state.data.analysis?.predictions?.next_draw_numbers?.top_5_most_likely || [];
    const colors = numbers.map(n => top5.includes(n) ? 'rgba(0, 212, 170, 0.8)' : 'rgba(99, 102, 241, 0.4)');
    const borderColors = numbers.map(n => top5.includes(n) ? 'rgba(0, 212, 170, 1)' : 'rgba(99, 102, 241, 0.6)');
    
    destroyChart('probability');
    state.charts.probability = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: numbers.map(n => n.toString().padStart(2, '0')),
            datasets: [{
                label: 'Probabilidad (%)',
                data: probs,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 1,
                borderRadius: 2
            }]
        },
        options: {
            ...getBarChartOptions('Distribución de Probabilidades para el Próximo Sorteo', 'Probabilidad (%)'),
            plugins: {
                ...getBarChartOptions().plugins,
                annotation: {
                    annotations: {
                        expectedLine: {
                            type: 'line',
                            mode: 'horizontal',
                            scale: 'y',
                            value: 100 / 43,
                            borderColor: 'rgba(239, 68, 68, 0.5)',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {
                                enabled: true,
                                content: 'Probabilidad teórica (2.33%)',
                                position: 'start',
                                backgroundColor: 'rgba(239, 68, 68, 0.8)',
                                color: 'white'
                            }
                        }
                    }
                }
            }
        }
    });
}

function createHeroChart() {
    const ctx = document.getElementById('hero-chart');
    if (!ctx) return;
    
    const freqData = state.data.analysis?.descriptive?.number_frequencies?.frequencies || {};
    const numbers = Object.keys(freqData).map(Number).sort((a, b) => a - b);
    const counts = numbers.map(n => freqData[n].count);
    
    destroyChart('hero');
    state.charts.hero = new Chart(ctx, {
        type: 'line',
        data: {
            labels: numbers.map(n => n.toString().padStart(2, '0')),
            datasets: [{
                label: 'Frecuencia Histórica',
                data: counts,
                borderColor: 'rgba(0, 212, 170, 1)',
                backgroundColor: 'rgba(0, 212, 170, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 2000, easing: 'easeOutQuart' },
            interaction: { intersect: false, mode: 'index' },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'var(--bg-card)',
                    titleColor: 'var(--text-primary)',
                    bodyColor: 'var(--text-secondary)',
                    borderColor: 'var(--border-color)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (context) => `Número ${context.label}: ${context.raw} veces`
                    }
                }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        }
    });
}

// ==========================================================================
// Chart Options Helpers
// ==========================================================================
function getBarChartOptions(title, yLabel, showPercent = false) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: CONFIG.animation.duration, easing: CONFIG.animation.easing },
        interaction: { intersect: false, mode: 'index' },
        plugins: {
            legend: { display: false },
            title: { display: !!title, text: title, font: { size: 13, weight: 600 }, color: 'var(--text-secondary)', padding: { bottom: 10 } },
            tooltip: {
                backgroundColor: 'var(--bg-card)',
                titleColor: 'var(--text-primary)',
                bodyColor: 'var(--text-secondary)',
                borderColor: 'var(--border-color)',
                borderWidth: 1,
                padding: 12,
                callbacks: {
                    label: (context) => `${context.dataset.label}: ${context.raw}${showPercent ? '%' : ''}`
                }
            }
        },
        scales: {
            x: {
                grid: { display: false },
                ticks: { color: 'var(--text-muted)', font: { size: 10 }, maxRotation: 0 }
            },
            y: {
                grid: { color: 'var(--border-color)', drawBorder: false },
                ticks: { color: 'var(--text-muted)', font: { size: 10 }, callback: v => showPercent ? `${v}%` : v },
                beginAtZero: true
            }
        }
    };
}

function getLineChartOptions(title, yLabel) {
    return {
        ...getBarChartOptions(title, yLabel),
        elements: { point: { radius: 0, hoverRadius: 5 } }
    };
}

function getDoughnutChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: { animateRotate: true, animateScale: true, duration: 1500 },
        cutout: '65%',
        plugins: {
            legend: { display: true },
            tooltip: { backgroundColor: 'var(--bg-card)', titleColor: 'var(--text-primary)', bodyColor: 'var(--text-secondary)', borderColor: 'var(--border-color)', borderWidth: 1 }
        }
    };
}

function destroyChart(key) {
    if (state.charts[key]) {
        state.charts[key].destroy();
        state.charts[key] = null;
    }
}

// ==========================================================================
// Inferential Statistics Rendering
// ==========================================================================
function renderInferentialTests() {
    const inferential = state.data.analysis?.inferential || {};
    const parametric = inferential.parametric || {};
    const nonParametric = inferential.non_parametric || {};
    
    // Testes paramétricos
    renderTestResult('uniformity-test', parametric.uniformity_test);
    renderTestResult('independence-test', parametric.independence_test);
    renderTestResult('hotcold-test', parametric.hot_cold_significance);
    renderTestResult('ci-test', parametric.confidence_intervals);
    renderTestResult('shapiro-test', parametric.normality_shapiro);
    renderTestResult('anderson-test', parametric.normality_anderson);
    
    // Testes não-paramétricos
    renderTestResult('mannwhitney-test', nonParametric.mann_whitney_odd_even);
    renderTestResult('kruskal-test', nonParametric.kruskal_wallis_position);
    renderTestResult('friedman-test', nonParametric.friedman_consecutive);
    renderTestResult('wilcoxon-test', nonParametric.wilcoxon_signed_rank);
}

function renderTestResult(containerId, testData) {
    const container = document.getElementById(containerId);
    if (!container || !testData) return;
    
    let statusClass = 'pass';
    let icon = '✓';
    let title = 'No significativo';
    
    if (testData.p_value !== undefined) {
        if (testData.significant_at_01) { statusClass = 'fail'; icon = '✗'; title = 'Muy significativo (p < 0.01)'; }
        else if (testData.significant_at_05) { statusClass = 'warning'; icon = '⚠'; title = 'Significativo (p < 0.05)'; }
        else { statusClass = 'pass'; icon = '✓'; title = 'No significativo (p ≥ 0.05)'; }
    } else if (testData.significant_at_05 !== undefined) {
        statusClass = testData.significant_at_05 ? 'fail' : 'pass';
        icon = testData.significant_at_05 ? '✗' : '✓';
        title = testData.significant_at_05 ? 'Significativo' : 'No significativo';
    }
    
    let detailsHtml = '';
    if (testData.chi2_statistic !== undefined) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">Chi-Cuadrado</span><span class="detail-value">${testData.chi2_statistic}</span></div>`;
    }
    if (testData.ljung_box_statistic !== undefined) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">Ljung-Box</span><span class="detail-value">${testData.ljung_box_statistic}</span></div>`;
    }
    if (testData.p_value !== undefined) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">Valor p</span><span class="detail-value">${testData.p_value.toFixed(6)}</span></div>`;
    }
    if (testData.degrees_of_freedom !== undefined) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">Grados Libertad</span><span class="detail-value">${testData.degrees_of_freedom}</span></div>`;
    }
    if (testData.mean_autocorrelation !== undefined) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">Autocorr. Media</span><span class="detail-value">${testData.mean_autocorrelation.toFixed(6)}</span></div>`;
    }
    if (testData.mean_sum_ci) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">IC Media Sumas</span><span class="detail-value">[${testData.mean_sum_ci[0]}, ${testData.mean_sum_ci[1]}]</span></div>`;
    }
    if (testData.number_frequency_ci) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">IC Frec. Números</span><span class="detail-value">[${testData.number_frequency_ci[0].toFixed(4)}, ${testData.number_frequency_ci[1].toFixed(4)}]</span></div>`;
    }
    if (testData.hot_significant_at_05 !== undefined) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">Calientes Sig.</span><span class="detail-value">${testData.hot_significant_at_05} / ${testData.hot_numbers_tested}</span></div>`;
        detailsHtml += `<div class="detail-item"><span class="detail-label">Fríos Sig.</span><span class="detail-value">${testData.cold_significant_at_05} / ${testData.cold_numbers_tested}</span></div>`;
        detailsHtml += `<div class="detail-item"><span class="detail-label">Bonferroni</span><span class="detail-value">${testData.bonferroni_threshold?.toFixed(6)}</span></div>`;
    }
    // FDR (Benjamini-Hochberg) counts
    if (testData.hot_fdr_significant_at_05 !== undefined) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">Calientes Sig. FDR</span><span class="detail-value">${testData.hot_fdr_significant_at_05} / ${testData.hot_numbers_tested}</span></div>`;
    }
    if (testData.cold_fdr_significant_at_05 !== undefined) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">Fríos Sig. FDR</span><span class="detail-value">${testData.cold_fdr_significant_at_05} / ${testData.cold_numbers_tested}</span></div>`;
    }
    // Effect size block
    if (testData.effect_size) {
        const es = testData.effect_size;
        let esText = '';
        if (es.cohens_w !== undefined) esText += `W de Cohen: ${es.cohens_w}`;
        if (es.cramers_v !== undefined) esText += (esText ? ' · ' : '') + `V de Cramér: ${es.cramers_v}`;
        if (es.r !== undefined) esText += (esText ? ' · ' : '') + `r: ${es.r}`;
        if (es.rank_biserial !== undefined) esText += (esText ? ' · ' : '') + `Corr. Rango-Biserial: ${es.rank_biserial}`;
        if (es.eta_squared !== undefined) esText += (esText ? ' · ' : '') + `η²: ${es.eta_squared}`;
        if (es.kendalls_w !== undefined) esText += (esText ? ' · ' : '') + `W de Kendall: ${es.kendalls_w}`;
        detailsHtml += `<div class="detail-item"><span class="detail-label">Tamaño del Efecto</span><span class="detail-value">${esText || '—'}</span></div>`;
        if (es.label) {
            detailsHtml += `<div class="detail-item"><span class="detail-label">Magnitud</span><span class="detail-value">${es.label}</span></div>`;
        }
    }
    // Power analysis block
    if (testData.power_analysis) {
        const pw = testData.power_analysis;
        detailsHtml += `<div class="detail-item"><span class="detail-label">Potencia (α=0.05)</span><span class="detail-value">${pw.power_at_05 !== undefined ? pw.power_at_05 : '—'}</span></div>`;
        if (pw.power_interpretation) {
            detailsHtml += `<div class="detail-item"><span class="detail-label">Poder Estadístico</span><span class="detail-value">${pw.power_interpretation}</span></div>`;
        }
    }
    // Non-parametric specific detail fields
    if (testData.test === 'Mann-Whitney U Test' && testData.median_odd_heavy !== undefined) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">Mediana Impar-High</span><span class="detail-value">${testData.median_odd_heavy}</span></div>`;
        detailsHtml += `<div class="detail-item"><span class="detail-label">Mediana Par-High</span><span class="detail-value">${testData.median_even_heavy}</span></div>`;
    }
    if (testData.n_total !== undefined && testData.chi2_statistic === undefined && testData.ljung_box_statistic === undefined) {
        detailsHtml += `<div class="detail-item"><span class="detail-label">N Total</span><span class="detail-value">${testData.n_total}</span></div>`;
    }
    
    container.innerHTML = `
        <div class="test-status ${statusClass}">
            <div class="status-icon">${icon}</div>
            <div class="status-info">
                <h4>${testData.test || 'Prueba Estadística'}</h4>
                <p>${testData.interpretation || title}</p>
            </div>
        </div>
        <div class="test-details">${detailsHtml}</div>
    `;
}

function renderInterpretation() {
    const container = document.getElementById('interpretation');
    if (!container) return;
    
    const inferential = state.data.analysis?.inferential || {};
    const parametric = inferential.parametric || {};
    const nonParametric = inferential.non_parametric || {};
    
    // Efecto de tamaño global para interpretación
    const esLabel = parametric.uniformity_test?.effect_size?.label || '';
    
    let html = `
        <h4>Conclusiones Principales</h4>
        <ul>
            <li><strong>Uniformidad:</strong> ${parametric.uniformity_test?.interpretation || 'Los números siguen una distribución uniforme consistente con la aleatoriedad.'}${esLabel ? ` <em>(Tamaño del efecto: ${esLabel})</em>` : ''}</li>
            <li><strong>Independencia:</strong> ${parametric.independence_test?.interpretation || 'No hay evidencia de autocorrelación entre sorteos consecutivos.'}</li>
            <li><strong>Patrones Calientes/Fríos:</strong> ${parametric.hot_cold_significance?.interpretation || 'Las desviaciones observadas son consistentes con fluctuaciones aleatorias normales.'}</li>
            <li><strong>Normalidad:</strong> ${parametric.normality_shapiro?.interpretation || 'La distribución de frecuencias de números es compatible con un proceso aleatorio.'}</li>
            <li><strong>Comparación Impar/Par:</strong> ${nonParametric.mann_whitney_odd_even?.interpretation || 'No hay diferencias significativas entre la distribución de números impares y pares.'}</li>
            <li><strong>Posición:</strong> ${nonParametric.kruskal_wallis_position?.interpretation || 'No hay diferencias sistemáticas entre las posiciones de los números.'}</li>
            <li><strong>Intervalos de Confianza:</strong> La media de las sumas se encuentra dentro del rango esperado teóricamente.</li>
        </ul>
        <p style="margin-top: 1rem; color: var(--accent-tertiary); font-weight: 500;">
            ⚠️ Interpretación: Todos los resultados son consistentes con un proceso aleatorio. 
            Las "tendencias" observadas son fluctuaciones estadísticas normales, no patrones predictivos.
        </p>
    `;
    
    container.innerHTML = html;
}

// ==========================================================================
// Predictions Rendering
// ==========================================================================
function populatePredictions() {
    const pred = state.data.analysis?.predictions || {};
    const numbersPred = pred.next_draw_numbers || {};
    const superPred = pred.next_superbalota || {};
    
    // Top Numbers
    const topNumbersContainer = document.getElementById('top-numbers-prediction');
    if (topNumbersContainer && numbersPred.probabilities) {
        const top10 = Object.entries(numbersPred.probabilities).slice(0, 10);
        topNumbersContainer.innerHTML = top10.map(([num, prob], idx) => `
            <div class="prediction-item" style="animation-delay: ${idx * 50}ms">
                <span class="prediction-rank">${idx + 1}</span>
                <span class="prediction-number">${num}</span>
                <span class="prediction-prob">${(prob * 100).toFixed(2)}%</span>
            </div>
        `).join('');
    }
    
    // Superbalota
    const superContainer = document.getElementById('superbalota-prediction');
    if (superContainer && superPred.probabilities) {
        const topSuper = Object.entries(superPred.probabilities).slice(0, 5);
        superContainer.innerHTML = topSuper.map(([num, prob], idx) => `
            <div class="prediction-item" style="animation-delay: ${idx * 50}ms">
                <span class="prediction-rank">${idx + 1}</span>
                <span class="prediction-number">${num}</span>
                <span class="prediction-prob">${(prob * 100).toFixed(2)}%</span>
            </div>
        `).join('');
    }
    
    // Recommended Combination
    const comboContainer = document.getElementById('recommended-combo');
    if (comboContainer) {
        const top5 = numbersPred.top_5_most_likely || [11, 38, 40, 8, 3];
        const topSuper = superPred.most_likely?.[0] || 7;
        
        comboContainer.innerHTML = `
            <div class="combo-numbers">
                ${top5.map((num, idx) => {
                    const ball = utils.createBall(num, 50);
                    ball.style.animationDelay = `${idx * 100}ms`;
                    return ball.outerHTML;
                }).join('')}
                ${(() => {
                    const ball = utils.createBall(topSuper, 45, true);
                    ball.style.animationDelay = `${top5.length * 100}ms`;
                    return ball.outerHTML;
                })()}
            </div>
            <div class="combo-info">
                Basado en probabilidades bayesianas | 
                Números: ${top5.join(', ')} | 
                Superbalota: ${topSuper} | 
                Probabilidad conjunta: ~${(top5.reduce((p, n) => p * (numbersPred.probabilities?.[n] || 0.023), 1) * 100).toFixed(4)}%
            </div>
        `;
    }
}

// ==========================================================================
// Predictive Modeling Rendering
// ==========================================================================
function renderPredictiveModeling() {
    const container = document.getElementById('predictive-models-container');
    if (!container) return;
    
    const pm = state.data.analysis?.predictive_modeling || {};
    if (!pm || !Object.keys(pm).length) {
        container.innerHTML = '<p class="empty-state">Los modelos predictivos se calcularán en el siguiente análisis automático.</p>';
        return;
    }
    
    const modelDefs = [
        { key: 'bayesian', label: 'Modelo Bayesiano', icon: '🎲', desc: 'Probabilidades por número con actualización de creencias.' },
        { key: 'markov_chain', label: 'Cadena de Markov', icon: '🔗', desc: 'Transiciones entre sorteos consecutivos.' },
        { key: 'regression_trends', label: 'Regresión de Tendencias', icon: '📈', desc: 'Proyección de sumas y frecuencias.' },
        { key: 'exponential_smoothing', label: 'Suavizado Exponencial', icon: '✨', desc: 'Promedios ponderados con decaimiento temporal.' },
        { key: 'ensemble', label: 'Modelo Ensamble', icon: '🧠', desc: 'Combinación ponderada de todos los modelos.' }
    ];
    
    const getTopNumbers = (m) => {
        if (!m) return [];
        if (Array.isArray(m.top_5)) return m.top_5.slice(0, 5);
        if (Array.isArray(m.top_10)) return m.top_10.slice(0, 5);
        if (Array.isArray(m.predictions)) return m.predictions.slice(0, 5);
        if (m.most_likely !== undefined) return [m.most_likely];
        return [];
    };
    
    const cardsHtml = modelDefs.map(def => {
        const m = pm[def.key];
        if (!m) return '';
        const top = getTopNumbers(m);
        const balls = top.map((num, idx) => {
            const ball = utils.createBall(num, 40);
            ball.style.animationDelay = `${idx * 60}ms`;
            return ball.outerHTML;
        }).join('');
        const confidence = m.confidence !== undefined
            ? (m.confidence * 100).toFixed(1) + '%'
            : (m.confidence_at_05 !== undefined ? (m.confidence_at_05 * 100).toFixed(1) + '%' : '—');
        return `
            <div class="model-card">
                <h4>${def.icon} ${def.label}</h4>
                <p class="combo-info">${def.desc}</p>
                ${balls ? `<div class="combo-numbers">${balls}</div>` : '<p class="empty-state">Sin predicción numérica.</p>'}
                ${confidence !== '—' ? `<div class="detail-item"><span class="detail-label">Confianza</span><span class="detail-value">${confidence}</span></div>` : ''}
            </div>
        `;
    }).filter(Boolean).join('');
    
    container.innerHTML = `<div class="model-grid">${cardsHtml}</div>`;
}
// ==========================================================================
// Latest Draws Table
// ==========================================================================
function populateLatestDraws() {
    const tbody = document.querySelector('#latest-draws-table tbody');
    if (!tbody) return;
    
    const draws = [...state.data.baloto.slice(0, 20), ...state.data.revancha.slice(0, 20)]
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 20);
    
    tbody.innerHTML = draws.map(draw => `
        <tr>
            <td>${utils.formatDate(draw.date)}</td>
            <td><span style="color: ${draw.game === 'Baloto' ? 'var(--accent-primary)' : 'var(--accent-secondary)'}; font-weight: 600;">${draw.game}</span></td>
            <td>${draw.numbers.map(n => utils.createBall(n, 28).outerHTML).join('')}</td>
            <td>${utils.createBall(draw.superbalota, 28, true).outerHTML}</td>
            <td class="jackpot">${utils.formatJackpot(draw.jackpot)}</td>
        </tr>
    `).join('');
}

// ==========================================================================
// Interactive Visualizer
// ==========================================================================
function initializeVisualizer() {
    const gameSelect = document.getElementById('viz-game');
    const periodSelect = document.getElementById('viz-period');
    const typeSelect = document.getElementById('viz-type');
    const refreshBtn = document.getElementById('viz-refresh');
    
    const updateViz = utils.debounce(() => {
        state.filters.game = gameSelect.value;
        state.filters.period = periodSelect.value;
        state.filters.vizType = typeSelect.value;
        renderVisualizer();
    }, 300);
    
    [gameSelect, periodSelect, typeSelect].forEach(el => el.addEventListener('change', updateViz));
    refreshBtn.addEventListener('click', () => renderVisualizer());
    
    renderVisualizer();
}

function renderVisualizer() {
    const container = d3.select('#interactive-viz');
    container.selectAll('*').remove();
    
    const { game, period, vizType } = state.filters;
    let data = game === 'baloto' ? state.data.baloto : 
               game === 'revancha' ? state.data.revancha : 
               [...state.data.baloto, ...state.data.revancha];
    
    // Filter by period
    if (period !== 'all') {
        const daysAgo = parseInt(period);
        const cutoff = new Date();
        cutoff.setDate(cutoff.getDate() - daysAgo);
        data = data.filter(d => new Date(d.date) >= cutoff);
    }
    
    const width = container.node().getBoundingClientRect().width || 800;
    const height = 400;
    const margin = { top: 40, right: 40, bottom: 60, left: 60 };
    
    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height)
        .style('font-family', 'var(--font-sans)');
    
    switch (vizType) {
        case 'frequency':
            renderFrequencyViz(svg, data, width, height, margin);
            break;
        case 'timeline':
            renderTimelineViz(svg, data, width, height, margin);
            break;
        case 'patterns':
            renderPatternsViz(svg, data, width, height, margin);
            break;
        case 'jackpot':
            renderJackpotViz(svg, data, width, height, margin);
            break;
    }
}

function renderFrequencyViz(svg, data, width, height, margin) {
    const freq = {};
    data.forEach(d => d.numbers.forEach(n => freq[n] = (freq[n] || 0) + 1));
    
    const numbers = Array.from({length: 43}, (_, i) => i + 1);
    const counts = numbers.map(n => freq[n] || 0);
    const maxCount = Math.max(...counts);
    
    const x = d3.scaleBand()
        .domain(numbers.map(String))
        .range([margin.left, width - margin.right])
        .padding(0.1);
    
    const y = d3.scaleLinear()
        .domain([0, maxCount * 1.1])
        .nice()
        .range([height - margin.bottom, margin.top]);
    
    // Bars
    svg.selectAll('rect.bar')
        .data(numbers)
        .enter()
        .append('rect')
        .attr('class', 'bar')
        .attr('x', d => x(String(d)))
        .attr('y', d => y(freq[d] || 0))
        .attr('width', x.bandwidth())
        .attr('height', d => height - margin.bottom - y(freq[d] || 0))
        .attr('fill', d => utils.getBallColor(d))
        .attr('rx', 3)
        .on('mouseover', function(event, d) {
            d3.select(this).attr('opacity', 0.8);
            showTooltip(event, d, { count: freq[d], percentage: ((freq[d] / data.length) * 100).toFixed(1) });
        })
        .on('mouseout', function() {
            d3.select(this).attr('opacity', 1);
            hideTooltip();
        });
    
    // Axes
    svg.append('g')
        .attr('transform', `translate(0, ${height - margin.bottom})`)
        .call(d3.axisBottom(x).tickSize(0))
        .selectAll('text')
        .attr('font-size', '10px')
        .attr('fill', 'var(--text-muted)');
    
    svg.append('g')
        .attr('transform', `translate(${margin.left}, 0)`)
        .call(d3.axisLeft(y).ticks(5))
        .selectAll('text')
        .attr('font-size', '10px')
        .attr('fill', 'var(--text-muted)');
    
    // Title
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', margin.top / 2)
        .attr('text-anchor', 'middle')
        .attr('font-size', '14px')
        .attr('font-weight', 600)
        .attr('fill', 'var(--text-primary)')
        .text(`Frecuencia de Números - ${data.length} sorteos`);
}

function renderTimelineViz(svg, data, width, height, margin) {
    // Sort by date ascending for timeline
    const sortedData = [...data].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    const dates = sortedData.map(d => new Date(d.date));
    const sums = sortedData.map(d => d.numbers.reduce((a, b) => a + b, 0));
    
    const x = d3.scaleTime()
        .domain(d3.extent(dates))
        .range([margin.left, width - margin.right]);
    
    const y = d3.scaleLinear()
        .domain([d3.min(sums) - 5, d3.max(sums) + 5])
        .nice()
        .range([height - margin.bottom, margin.top]);
    
    const line = d3.line()
        .x(d => x(new Date(d.date)))
        .y(d => y(d.numbers.reduce((a, b) => a + b, 0)))
        .curve(d3.curveMonotoneX);
    
    // Line
    svg.append('path')
        .datum(sortedData)
        .attr('fill', 'none')
        .attr('stroke', 'var(--accent-primary)')
        .attr('stroke-width', 2)
        .attr('d', line);
    
    // Points
    svg.selectAll('circle.point')
        .data(sortedData)
        .enter()
        .append('circle')
        .attr('class', 'point')
        .attr('cx', d => x(new Date(d.date)))
        .attr('cy', d => y(d.numbers.reduce((a, b) => a + b, 0)))
        .attr('r', 4)
        .attr('fill', 'var(--accent-primary)')
        .on('mouseover', function(event, d) {
            d3.select(this).attr('r', 6).attr('fill', 'var(--accent-tertiary)');
            showTooltip(event, d.date, { 
                sum: d.numbers.reduce((a, b) => a + b, 0),
                numbers: d.numbers.join(', '),
                superbalota: d.superbalota
            });
        })
        .on('mouseout', function() {
            d3.select(this).attr('r', 4).attr('fill', 'var(--accent-primary)');
            hideTooltip();
        });
    
    // Axes
    svg.append('g')
        .attr('transform', `translate(0, ${height - margin.bottom})`)
        .call(d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat('%b %Y')))
        .selectAll('text')
        .attr('font-size', '10px')
        .attr('fill', 'var(--text-muted)');
    
    svg.append('g')
        .attr('transform', `translate(${margin.left}, 0)`)
        .call(d3.axisLeft(y).ticks(5))
        .selectAll('text')
        .attr('font-size', '10px')
        .attr('fill', 'var(--text-muted)');
    
    // Title
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', margin.top / 2)
        .attr('text-anchor', 'middle')
        .attr('font-size', '14px')
        .attr('font-weight', 600)
        .attr('fill', 'var(--text-primary)')
        .text(`Evolución de Sumas - ${sortedData.length} sorteos`);
}

function renderPatternsViz(svg, data, width, height, margin) {
    // Consecutive numbers over time
    const sortedData = [...data].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    const consecData = sortedData.map(d => {
        let consec = 0;
        for (let i = 0; i < 4; i++) {
            if (d.numbers[i + 1] === d.numbers[i] + 1) consec++;
        }
        return { date: new Date(d.date), consec };
    });
    
    const x = d3.scaleTime()
        .domain(d3.extent(consecData, d => d.date))
        .range([margin.left, width - margin.right]);
    
    const y = d3.scaleLinear()
        .domain([-0.5, 3.5])
        .range([height - margin.bottom, margin.top]);
    
    // Bars for consecutive count
    svg.selectAll('rect.consec')
        .data(consecData)
        .enter()
        .append('rect')
        .attr('class', 'consec')
        .attr('x', d => x(d.date) - 2)
        .attr('y', d => y(d.consec))
        .attr('width', 4)
        .attr('height', d => height - margin.bottom - y(d.consec))
        .attr('fill', d => d.consec > 0 ? 'var(--accent-tertiary)' : 'var(--accent-primary)')
        .attr('opacity', 0.7);
    
    // Axes
    svg.append('g')
        .attr('transform', `translate(0, ${height - margin.bottom})`)
        .call(d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat('%b %Y')))
        .selectAll('text')
        .attr('font-size', '10px')
        .attr('fill', 'var(--text-muted)');
    
    svg.append('g')
        .attr('transform', `translate(${margin.left}, 0)`)
        .call(d3.axisLeft(y).tickValues([0, 1, 2, 3]).tickFormat(d => `${d} par${d !== 1 ? 'es' : ''}`))
        .selectAll('text')
        .attr('font-size', '10px')
        .attr('fill', 'var(--text-muted)');
    
    // Title
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', margin.top / 2)
        .attr('text-anchor', 'middle')
        .attr('font-size', '14px')
        .attr('font-weight', 600)
        .attr('fill', 'var(--text-primary)')
        .text(`Números Consecutivos por Sorteo`);
}

function renderJackpotViz(svg, data, width, height, margin) {
    const sortedData = [...data].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    const x = d3.scaleTime()
        .domain(d3.extent(sortedData, d => new Date(d.date)))
        .range([margin.left, width - margin.right]);
    
    const y = d3.scaleLinear()
        .domain([0, d3.max(sortedData, d => d.jackpot) * 1.1])
        .nice()
        .range([height - margin.bottom, margin.top]);
    
    // Area chart
    const area = d3.area()
        .x(d => x(new Date(d.date)))
        .y0(height - margin.bottom)
        .y1(d => y(d.jackpot))
        .curve(d3.curveMonotoneX);
    
    svg.append('path')
        .datum(sortedData)
        .attr('fill', 'rgba(0, 212, 170, 0.1)')
        .attr('stroke', 'none')
        .attr('d', area);
    
    // Line
    const line = d3.line()
        .x(d => x(new Date(d.date)))
        .y(d => y(d.jackpot))
        .curve(d3.curveMonotoneX);
    
    svg.append('path')
        .datum(sortedData)
        .attr('fill', 'none')
        .attr('stroke', 'var(--accent-primary)')
        .attr('stroke-width', 2)
        .attr('d', line);
    
    // Axes
    svg.append('g')
        .attr('transform', `translate(0, ${height - margin.bottom})`)
        .call(d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat('%b %Y')))
        .selectAll('text')
        .attr('font-size', '10px')
        .attr('fill', 'var(--text-muted)');
    
    svg.append('g')
        .attr('transform', `translate(${margin.left}, 0)`)
        .call(d3.axisLeft(y).ticks(5).tickFormat(d => utils.formatJackpot(d)))
        .selectAll('text')
        .attr('font-size', '10px')
        .attr('fill', 'var(--text-muted)');
    
    // Title
    svg.append('text')
        .attr('x', width / 2)
        .attr('y', margin.top / 2)
        .attr('text-anchor', 'middle')
        .attr('font-size', '14px')
        .attr('font-weight', 600)
        .attr('fill', 'var(--text-primary)')
        .text(`Evolución del Jackpot`);
}

// ==========================================================================
// Theme Toggle
// ==========================================================================
function initializeTheme() {
    const toggleBtn = document.getElementById('theme-toggle');
    const savedTheme = localStorage.getItem('theme') || 'dark';
    
    document.documentElement.setAttribute('data-theme', savedTheme);
    state.currentTheme = savedTheme;
    
    toggleBtn.addEventListener('click', () => {
        const newTheme = state.currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        state.currentTheme = newTheme;
        
        // Update charts colors
        Object.values(state.charts).forEach(chart => {
            if (chart && chart.update) chart.update();
        });
    });
}

// ==========================================================================
// Mobile Menu
// ==========================================================================
function initializeMobileMenu() {
    const menuBtn = document.getElementById('mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    menuBtn.addEventListener('click', () => {
        const isOpen = navLinks.classList.toggle('open');
        menuBtn.setAttribute('aria-expanded', isOpen);
    });
    
    // Close on link click
    navLinks.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('open');
            menuBtn.setAttribute('aria-expanded', 'false');
        });
    });
    
    // Active link highlighting
    const sections = document.querySelectorAll('section[id]');
    const navLinksArray = document.querySelectorAll('.nav-link');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                navLinksArray.forEach(link => {
                    link.classList.toggle('active', link.dataset.section === entry.target.id);
                });
            }
        });
    }, { threshold: 0.3, rootMargin: '-80px 0px -50% 0px' });
    
    sections.forEach(section => observer.observe(section));
}

// ==========================================================================
// Particle Background
// ==========================================================================
function initializeParticles() {
    const canvas = document.getElementById('bg-canvas');
    const ctx = canvas.getContext('2d');
    
    // A11y: respetar prefers-reduced-motion (dibujar un frame estático, sin bucle)
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    let particles = [];
    const particleCount = 50;
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    function createParticles() {
        particles = [];
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                radius: Math.random() * 2 + 0.5,
                color: Math.random() > 0.5 ? 'rgba(0, 212, 170,' : 'rgba(99, 102, 241,',
                opacity: Math.random() * 0.5 + 0.1
            });
        }
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;
            
            if (p.x < 0) p.x = canvas.width;
            if (p.x > canvas.width) p.x = 0;
            if (p.y < 0) p.y = canvas.height;
            if (p.y > canvas.height) p.y = 0;
            
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = `${p.color}${p.opacity})`;
            ctx.fill();
        });
        
        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist < 150) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(0, 212, 170, ${0.1 * (1 - dist / 150)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
        
        if (!reduceMotion) requestAnimationFrame(animate);
    }
    
    window.addEventListener('resize', () => {
        resize();
        createParticles();
    });
    
    resize();
    createParticles();
    animate();
}

// ==========================================================================
// Smooth Scroll for Anchor Links
// ==========================================================================
function initializeSmoothScroll() {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                const headerHeight = document.querySelector('.navbar').offsetHeight;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight;
                
                window.scrollTo({ top: targetPosition, behavior: reduceMotion ? 'auto' : 'smooth' });
            }
        });
    });
}

// ==========================================================================
// Visit Counter
// ==========================================================================
async function initializeVisitCounter() {
    const counterEl = document.getElementById('visit-count');
    if (!counterEl) return;
    
    try {
        // Use a simple localStorage counter + API for display
        let count = parseInt(localStorage.getItem('baloto_oracle_visits') || '0', 10);
        count += 1;
        localStorage.setItem('baloto_oracle_visits', count.toString());
        
        // Also try to fetch from a public counter API for cross-device count
        try {
            const response = await fetch('https://api.countapi.xyz/hit/baloto-oracle/visits', {
                method: 'GET',
                mode: 'cors'
            });
            if (response.ok) {
                const data = await response.json();
                count = data.value;
            }
        } catch {
            // Fallback to local count
        }
        
        counterEl.textContent = utils.formatNumber(count);
    } catch (error) {
        console.warn('Visit counter error:', error);
        counterEl.textContent = '—';
    }
}

// ==========================================================================
// Keyboard Focus Visibility (a11y)
// ==========================================================================
function initializeFocusVisible() {
    const html = document.documentElement;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Detectar navegación por teclado: añadir clase cuando se pulsa Tab
    html.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            html.classList.add('keyboard-nav');
        }
    });

    // Quitar la clase cuando se usa el ratón
    html.addEventListener('mousedown', () => {
        html.classList.remove('keyboard-nav');
    });

    // A11y: animaciones reducidas — pausar transiciones del tema
    if (reduceMotion) {
        html.classList.add('reduce-motion');
    }
}

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
    initializeFocusVisible();
    initializeTheme();
    initializeMobileMenu();
    initializeParticles();
    initializeSmoothScroll();
    initializeVisitCounter();
    loadData();

    // Reintentar carga de datos sin datos de ejemplo
    const retryBtn = document.getElementById('error-retry-btn');
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            if (retryBtn.disabled) return;
            retryBtn.disabled = true;
            loadData().finally(() => {
                retryBtn.disabled = false;
            });
        });
    }
    
    // Add Chart.js annotation plugin if not loaded
    if (typeof Chart !== 'undefined' && !Chart.registry.plugins.has('annotation')) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js';
        script.onload = () => {
            Object.values(state.charts).forEach(chart => {
                if (chart && chart.update) chart.update();
            });
        };
        document.head.appendChild(script);
    }
});

// Handle visibility change to pause/resume particles
document.addEventListener('visibilitychange', () => {
    const canvas = document.getElementById('bg-canvas');
    canvas.style.display = document.hidden ? 'none' : 'block';
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { utils, CONFIG, state };
}