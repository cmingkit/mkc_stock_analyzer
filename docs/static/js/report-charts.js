/**
 * Stock Analyzer Report Charts
 * Chart.js initialization and configuration
 */

// Color palette
const COLORS = {
    positive: '#4CAF50',
    negative: '#F44336',
    neutral: '#9E9E9E',
    warning: '#FF9800',
    info: '#2196F3',
    purple: '#9C27B0',
    cyan: '#00BCD4'
};

// Chart instances storage
const charts = {};

/**
 * Initialize all charts with data
 */
function initializeCharts(chartData) {
    // Initialize sentiment charts
    if (chartData.sentiment) {
        Object.keys(chartData.sentiment).forEach(ticker => {
            createSentimentChart(ticker, chartData.sentiment[ticker]);
        });
    }
    
    // Initialize sentiment trend charts
    if (chartData.sentimentTrend) {
        Object.keys(chartData.sentimentTrend).forEach(ticker => {
            createSentimentTrendChart(ticker, chartData.sentimentTrend[ticker]);
        });
    }
    
    // Initialize price charts
    if (chartData.price) {
        Object.keys(chartData.price).forEach(ticker => {
            createPriceChart(ticker, chartData.price[ticker]);
        });
    }
    
    // Initialize comparison charts
    if (chartData.comparison) {
        Object.keys(chartData.comparison).forEach(ticker => {
            createComparisonChart(ticker, chartData.comparison[ticker]);
        });
    }
}

/**
 * Sentiment Distribution Chart (Doughnut)
 */
function createSentimentChart(ticker, data) {
    const ctx = document.getElementById('sentiment-' + ticker);
    if (!ctx) return;
    
    if (charts['sentiment-' + ticker]) {
        charts['sentiment-' + ticker].destroy();
    }
    
    charts['sentiment-' + ticker] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [data.positive || 0, data.neutral || 0, data.negative || 0],
                backgroundColor: [COLORS.positive, COLORS.neutral, COLORS.negative],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 10,
                        font: { size: 11 },
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
                            return context.label + ': ' + context.raw + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Sentiment Trend Chart (7 days)
 */
function createSentimentTrendChart(ticker, data) {
    const ctx = document.getElementById('sentiment-trend-' + ticker);
    if (!ctx) return;
    
    if (charts['sentiment-trend-' + ticker]) {
        charts['sentiment-trend-' + ticker].destroy();
    }
    
    charts['sentiment-trend-' + ticker] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels || ['7d', '6d', '5d', '4d', '3d', '2d', '1d', 'Today'],
            datasets: [
                {
                    label: 'Positive',
                    data: data.positive || [],
                    borderColor: COLORS.positive,
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Neutral',
                    data: data.neutral || [],
                    borderColor: COLORS.neutral,
                    backgroundColor: 'rgba(158, 158, 158, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Negative',
                    data: data.negative || [],
                    borderColor: COLORS.negative,
                    backgroundColor: 'rgba(244, 67, 54, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { font: { size: 10 }, usePointStyle: true }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Mentions', font: { size: 10 } }
                }
            }
        }
    });
}

/**
 * Price & Moving Averages Chart
 */
function createPriceChart(ticker, data) {
    const ctx = document.getElementById('price-' + ticker);
    if (!ctx) return;
    
    if (charts['price-' + ticker]) {
        charts['price-' + ticker].destroy();
    }
    
    const datasets = [
        {
            label: 'Price',
            data: data.prices || [],
            borderColor: COLORS.info,
            backgroundColor: 'rgba(33, 150, 243, 0.1)',
            borderWidth: 2,
            tension: 0.1,
            fill: true,
            yAxisID: 'y'
        }
    ];
    
    // Add SMA20 if available
    if (data.sma20 && data.sma20.length > 0) {
        datasets.push({
            label: 'SMA 20',
            data: data.sma20,
            borderColor: COLORS.warning,
            borderWidth: 1.5,
            borderDash: [5, 5],
            tension: 0.1,
            fill: false,
            yAxisID: 'y'
        });
    }
    
    // Add SMA50 if available
    if (data.sma50 && data.sma50.length > 0) {
        datasets.push({
            label: 'SMA 50',
            data: data.sma50,
            borderColor: COLORS.purple,
            borderWidth: 1.5,
            borderDash: [5, 5],
            tension: 0.1,
            fill: false,
            yAxisID: 'y'
        });
    }
    
    // Add EMA12 if available
    if (data.ema12 && data.ema12.length > 0) {
        datasets.push({
            label: 'EMA 12',
            data: data.ema12,
            borderColor: COLORS.cyan,
            borderWidth: 1.5,
            tension: 0.1,
            fill: false,
            yAxisID: 'y'
        });
    }
    
    // Add volume bars if available
    if (data.volumes && data.volumes.length > 0) {
        datasets.push({
            type: 'bar',
            label: 'Volume',
            data: data.volumes,
            backgroundColor: data.volumes.map(function(v, i) { 
                return (i > 0 && data.prices && data.prices[i] > data.prices[i-1]) 
                    ? 'rgba(76, 175, 80, 0.3)' 
                    : 'rgba(244, 67, 54, 0.3)';
            }),
            yAxisID: 'y1'
        });
    }
    
    charts['price-' + ticker] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates || [],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        font: { size: 10 }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Price ($)',
                        font: { size: 10 }
                    }
                },
                y1: {
                    type: 'linear',
                    display: data.volumes && data.volumes.length > 0,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Volume',
                        font: { size: 10 }
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

/**
 * Industry Comparison Chart (Radar)
 */
function createComparisonChart(ticker, data) {
    const ctx = document.getElementById('comparison-' + ticker);
    if (!ctx) return;
    
    if (charts['comparison-' + ticker]) {
        charts['comparison-' + ticker].destroy();
    }
    
    charts['comparison-' + ticker] = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['P/E', 'P/B', 'ROE', 'Debt Ratio', 'Profit Margin', 'Growth'],
            datasets: [
                {
                    label: ticker,
                    data: data.stock || [],
                    backgroundColor: 'rgba(33, 150, 243, 0.2)',
                    borderColor: COLORS.info,
                    borderWidth: 2,
                    pointBackgroundColor: COLORS.info
                },
                {
                    label: 'Industry Avg',
                    data: data.industry || [],
                    backgroundColor: 'rgba(158, 158, 158, 0.1)',
                    borderColor: COLORS.neutral,
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointBackgroundColor: COLORS.neutral
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        font: { size: 10 }
                    }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        font: { size: 8 }
                    },
                    pointLabels: {
                        font: { size: 9 }
                    }
                }
            }
        }
    });
}

/**
 * Table sorting function
 */
function sortTable(tableId, column, dataType) {
    dataType = dataType || 'string';
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const sorted = rows.sort(function(a, b) {
        let aVal = a.cells[column].textContent.trim();
        let bVal = b.cells[column].textContent.trim();
        
        // Remove currency symbols and commas for numeric comparison
        if (dataType === 'number') {
            aVal = parseFloat(aVal.replace(/[\$,]/g, '')) || 0;
            bVal = parseFloat(bVal.replace(/[\$,]/g, '')) || 0;
            return aVal - bVal;
        }
        
        return aVal.localeCompare(bVal);
    });
    
    // Toggle sort direction
    if (table.dataset.sortCol == column && table.dataset.sortDir === 'asc') {
        sorted.reverse();
        table.dataset.sortDir = 'desc';
    } else {
        table.dataset.sortDir = 'asc';
    }
    table.dataset.sortCol = column;
    
    // Re-append sorted rows
    sorted.forEach(function(row) { tbody.appendChild(row); });
}

/**
 * Lazy load charts on scroll
 */
function lazyLoadCharts() {
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const ticker = entry.target.id.replace('stock-', '');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.stock-card-enhanced').forEach(function(card) {
        observer.observe(card);
    });
}

// Export functions for global use
window.initializeCharts = initializeCharts;
window.sortTable = sortTable;
window.lazyLoadCharts = lazyLoadCharts;
