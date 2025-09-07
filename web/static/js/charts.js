// Charts JavaScript - Trading Bot
// Funcionalidades específicas para gráficos e visualização de dados

const ChartManager = {
    // Configurações padrão dos gráficos
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            intersect: false,
            mode: 'index'
        },
        elements: {
            point: {
                radius: 0,
                hoverRadius: 6,
                hitRadius: 10
            },
            line: {
                tension: 0.2
            }
        },
        scales: {
            y: {
                beginAtZero: false,
                position: 'right',
                ticks: {
                    callback: function(value) {
                        return '€' + parseFloat(value).toFixed(4);
                    },
                    color: '#666',
                    font: {
                        size: 11
                    }
                },
                grid: {
                    color: 'rgba(0,0,0,0.1)',
                    drawBorder: false
                }
            },
            x: {
                ticks: {
                    maxTicksLimit: 10,
                    color: '#666',
                    font: {
                        size: 11
                    }
                },
                grid: {
                    color: 'rgba(0,0,0,0.05)',
                    drawBorder: false
                }
            }
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                align: 'start',
                labels: {
                    usePointStyle: true,
                    pointStyle: 'line',
                    font: {
                        size: 12,
                        weight: 'bold'
                    },
                    color: '#333'
                }
            },
            tooltip: {
                enabled: true,
                backgroundColor: 'rgba(0,0,0,0.8)',
                titleColor: 'white',
                bodyColor: 'white',
                borderColor: 'rgba(255,255,255,0.2)',
                borderWidth: 1,
                cornerRadius: 6,
                displayColors: false,
                callbacks: {
                    title: function(tooltipItems) {
                        return tooltipItems[0].label;
                    },
                    label: function(context) {
                        const value = parseFloat(context.parsed.y).toFixed(4);
                        return `${context.dataset.label}: €${value}`;
                    }
                }
            }
        },
        animation: {
            duration: 500,
            easing: 'easeInOutQuart'
        }
    },

    // Paleta de cores para diferentes instrumentos
    colorPalette: [
        {
            border: '#3498db',
            background: 'rgba(52, 152, 219, 0.1)',
            positive: '#27ae60',
            negative: '#e74c3c'
        },
        {
            border: '#9b59b6',
            background: 'rgba(155, 89, 182, 0.1)',
            positive: '#27ae60',
            negative: '#e74c3c'
        },
        {
            border: '#f39c12',
            background: 'rgba(243, 156, 18, 0.1)',
            positive: '#27ae60',
            negative: '#e74c3c'
        }
    ],

    // Criar gráfico de linha padrão
    createLineChart(canvas, data, symbol, interval) {
        const ctx = canvas.getContext('2d');
        
        // Preparar dados
        const chartData = this.prepareLineData(data, symbol, interval);
        
        // Opções específicas para linha
        const options = {
            ...this.defaultOptions,
            scales: {
                ...this.defaultOptions.scales,
                y: {
                    ...this.defaultOptions.scales.y,
                    title: {
                        display: true,
                        text: 'Preço (€)',
                        color: '#666',
                        font: {
                            size: 12,
                            weight: 'bold'
                        }
                    }
                }
            }
        };

        return new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: options
        });
    },

    // Criar gráfico de velas (candlestick)
    createCandlestickChart(canvas, data, symbol, interval) {
        const ctx = canvas.getContext('2d');
        
        // Preparar dados OHLC
        const candleData = this.prepareCandlestickData(data, symbol, interval);
        
        // Chart.js não suporta candlestick nativamente
        // Por agora, usamos um gráfico de linha com cores baseadas na tendência
        return this.createTrendLineChart(canvas, data, symbol, interval);
    },

    // Criar gráfico de linha com cores baseadas na tendência
    createTrendLineChart(canvas, data, symbol, interval) {
        const ctx = canvas.getContext('2d');
        
        const prices = data.data.map(d => d.close);
        const labels = this.formatLabels(data.data, interval);
        
        // Determinar cor baseada na tendência geral
        const firstPrice = prices[0];
        const lastPrice = prices[prices.length - 1];
        const isPositive = lastPrice >= firstPrice;
        
        const colors = this.colorPalette[0];
        
        const chartData = {
            labels: labels,
            datasets: [{
                label: `${symbol} (${interval})`,
                data: prices,
                borderColor: isPositive ? colors.positive : colors.negative,
                backgroundColor: isPositive ? 
                    'rgba(39, 174, 96, 0.1)' : 'rgba(231, 76, 60, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.2,
                pointRadius: 0,
                pointHoverRadius: 5,
                pointBackgroundColor: isPositive ? colors.positive : colors.negative,
                pointBorderColor: 'white',
                pointBorderWidth: 2
            }]
        };

        const options = {
            ...this.defaultOptions,
            plugins: {
                ...this.defaultOptions.plugins,
                tooltip: {
                    ...this.defaultOptions.plugins.tooltip,
                    callbacks: {
                        ...this.defaultOptions.plugins.tooltip.callbacks,
                        afterBody: function(tooltipItems) {
                            const index = tooltipItems[0].dataIndex;
                            const point = data.data[index];
                            
                            return [
                                `Abertura: €${point.open.toFixed(4)}`,
                                `Máximo: €${point.high.toFixed(4)}`,
                                `Mínimo: €${point.low.toFixed(4)}`,
                                `Volume: ${point.volume.toLocaleString('pt-PT')}`
                            ];
                        }
                    }
                }
            }
        };

        return new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: options
        });
    },

    // Preparar dados para gráfico de linha
    prepareLineData(data, symbol, interval) {
        const labels = this.formatLabels(data.data, interval);
        const prices = data.data.map(d => d.close);
        
        return {
            labels: labels,
            datasets: [{
                label: `${symbol} (${interval})`,
                data: prices,
                borderColor: this.colorPalette[0].border,
                backgroundColor: this.colorPalette[0].background,
                borderWidth: 2,
                fill: true,
                tension: 0.2
            }]
        };
    },

    // Preparar dados para candlestick
    prepareCandlestickData(data, symbol, interval) {
        return data.data.map(d => ({
            x: new Date(d.timestamp * 1000),
            o: d.open,
            h: d.high,
            l: d.low,
            c: d.close
        }));
    },

    // Formatar labels baseado no intervalo
    formatLabels(dataPoints, interval) {
        return dataPoints.map(d => {
            const date = new Date(d.timestamp * 1000);
            
            switch(interval) {
                case '1m':
                    return date.toLocaleTimeString('pt-PT', {
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                    
                case '30m':
                    return date.toLocaleTimeString('pt-PT', {
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                    
                case '1D':
                default:
                    return date.toLocaleDateString('pt-PT', {
                        day: '2-digit',
                        month: '2-digit'
                    });
            }
        });
    },

    // Calcular estatísticas dos dados
    calculateStats(data) {
        const prices = data.map(d => d.close);
        const volumes = data.map(d => d.volume || 0);
        
        const min = Math.min(...prices);
        const max = Math.max(...prices);
        const first = prices[0];
        const last = prices[prices.length - 1];
        const change = last - first;
        const changePercent = (change / first) * 100;
        
        const avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;
        
        return {
            min: min,
            max: max,
            first: first,
            last: last,
            change: change,
            changePercent: changePercent,
            avgVolume: avgVolume,
            dataPoints: prices.length
        };
    },

    // Adicionar indicadores técnicos simples
    addMovingAverage(chart, data, period = 20) {
        if (!chart || !data || data.length < period) return;
        
        const prices = data.map(d => d.close);
        const ma = [];
        
        for (let i = period - 1; i < prices.length; i++) {
            const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
            ma.push(sum / period);
        }
        
        // Preencher com nulls no início
        const fullMA = new Array(period - 1).fill(null).concat(ma);
        
        // Adicionar dataset
        chart.data.datasets.push({
            label: `MA(${period})`,
            data: fullMA,
            borderColor: '#f39c12',
            backgroundColor: 'transparent',
            borderWidth: 1,
            pointRadius: 0,
            tension: 0
        });
        
        chart.update();
    },

    // Limpar canvas em caso de erro
    clearCanvas(canvas, errorMessage = 'Erro ao carregar dados') {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Desenhar mensagem de erro
        ctx.font = '16px Arial';
        ctx.fillStyle = '#e74c3c';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Ícone de erro
        ctx.fillText('⚠️', canvas.width/2, canvas.height/2 - 25);
        
        // Texto principal
        ctx.fillText('Erro ao carregar gráfico', canvas.width/2, canvas.height/2);
        
        // Detalhes do erro
        ctx.font = '12px Arial';
        ctx.fillStyle = '#666';
        ctx.fillText(errorMessage, canvas.width/2, canvas.height/2 + 20);
        
        // Sugestão
        ctx.fillText('Verifica a ligação à internet e tenta novamente', canvas.width/2, canvas.height/2 + 35);
    },

    // Mostrar loading no canvas
    showLoading(canvas, message = 'A carregar dados...') {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Fundo semi-transparente
        ctx.fillStyle = 'rgba(248, 249, 250, 0.9)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Texto de loading
        ctx.font = '16px Arial';
        ctx.fillStyle = '#3498db';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Spinner animado (usando CSS animation seria melhor)
        ctx.fillText('⟳', canvas.width/2, canvas.height/2 - 15);
        
        ctx.font = '14px Arial';
        ctx.fillStyle = '#666';
        ctx.fillText(message, canvas.width/2, canvas.height/2 + 10);
    },

    // Obter configurações otimizadas para dispositivos móveis
    getMobileOptions() {
        return {
            ...this.defaultOptions,
            scales: {
                y: {
                    ...this.defaultOptions.scales.y,
                    ticks: {
                        ...this.defaultOptions.scales.y.ticks,
                        font: {
                            size: 10
                        },
                        maxTicksLimit: 6
                    }
                },
                x: {
                    ...this.defaultOptions.scales.x,
                    ticks: {
                        ...this.defaultOptions.scales.x.ticks,
                        font: {
                            size: 10
                        },
                        maxTicksLimit: 6
                    }
                }
            },
            plugins: {
                ...this.defaultOptions.plugins,
                legend: {
                    ...this.defaultOptions.plugins.legend,
                    labels: {
                        ...this.defaultOptions.plugins.legend.labels,
                        font: {
                            size: 11
                        }
                    }
                }
            }
        };
    },

    // Redimensionar gráfico para diferentes tamanhos de ecrã
    resizeChart(chart) {
        if (!chart) return;
        
        const isMobile = window.innerWidth < 768;
        
        if (isMobile && chart.options !== this.getMobileOptions()) {
            chart.options = this.getMobileOptions();
            chart.update();
        } else if (!isMobile && chart.options === this.getMobileOptions()) {
            chart.options = this.defaultOptions;
            chart.update();
        }
    },

    // Exportar gráfico como imagem
    exportChart(chart, filename = 'grafico_trading_bot') {
        if (!chart) return;
        
        const canvas = chart.canvas;
        const url = canvas.toDataURL('image/png');
        
        // Criar link de download
        const link = document.createElement('a');
        link.download = `${filename}_${new Date().toISOString().split('T')[0]}.png`;
        link.href = url;
        link.click();
    },

    // Análise técnica simples
    technicalAnalysis: {
        // Calcular RSI (Relative Strength Index)
        calculateRSI(prices, period = 14) {
            if (prices.length < period + 1) return null;
            
            const changes = [];
            for (let i = 1; i < prices.length; i++) {
                changes.push(prices[i] - prices[i - 1]);
            }
            
            const gains = changes.map(change => change > 0 ? change : 0);
            const losses = changes.map(change => change < 0 ? -change : 0);
            
            // Média das primeiras 'period' observações
            let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
            let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;
            
            const rsi = [];
            
            for (let i = period; i < changes.length; i++) {
                const rs = avgGain / avgLoss;
                rsi.push(100 - (100 / (1 + rs)));
                
                // Smooth para próxima iteração
                avgGain = ((avgGain * (period - 1)) + gains[i]) / period;
                avgLoss = ((avgLoss * (period - 1)) + losses[i]) / period;
            }
            
            return rsi;
        },

        // Calcular MACD
        calculateMACD(prices, fast = 12, slow = 26, signal = 9) {
            if (prices.length < slow) return null;
            
            const emaFast = this.calculateEMA(prices, fast);
            const emaSlow = this.calculateEMA(prices, slow);
            
            if (!emaFast || !emaSlow) return null;
            
            const macdLine = [];
            const start = Math.max(emaFast.length, emaSlow.length) - Math.min(emaFast.length, emaSlow.length);
            
            for (let i = start; i < Math.min(emaFast.length, emaSlow.length); i++) {
                macdLine.push(emaFast[i] - emaSlow[i]);
            }
            
            const signalLine = this.calculateEMA(macdLine, signal);
            const histogram = [];
            
            if (signalLine) {
                for (let i = 0; i < signalLine.length; i++) {
                    histogram.push(macdLine[i + (macdLine.length - signalLine.length)] - signalLine[i]);
                }
            }
            
            return {
                macd: macdLine,
                signal: signalLine,
                histogram: histogram
            };
        },

        // Calcular EMA (Exponential Moving Average)
        calculateEMA(prices, period) {
            if (prices.length < period) return null;
            
            const multiplier = 2 / (period + 1);
            const ema = [];
            
            // Primeira EMA é a SMA
            let sum = 0;
            for (let i = 0; i < period; i++) {
                sum += prices[i];
            }
            ema.push(sum / period);
            
            // Calcular EMA para o resto
            for (let i = period; i < prices.length; i++) {
                const emaValue = (prices[i] * multiplier) + (ema[ema.length - 1] * (1 - multiplier));
                ema.push(emaValue);
            }
            
            return ema;
        },

        // Calcular Bollinger Bands
        calculateBollingerBands(prices, period = 20, stdDev = 2) {
            if (prices.length < period) return null;
            
            const sma = [];
            const upperBand = [];
            const lowerBand = [];
            
            for (let i = period - 1; i < prices.length; i++) {
                const slice = prices.slice(i - period + 1, i + 1);
                const mean = slice.reduce((a, b) => a + b, 0) / period;
                
                // Calcular desvio padrão
                const variance = slice.reduce((acc, price) => {
                    return acc + Math.pow(price - mean, 2);
                }, 0) / period;
                const stdDeviation = Math.sqrt(variance);
                
                sma.push(mean);
                upperBand.push(mean + (stdDev * stdDeviation));
                lowerBand.push(mean - (stdDev * stdDeviation));
            }
            
            return {
                sma: sma,
                upper: upperBand,
                lower: lowerBand
            };
        },

        // Determinar tendência simples
        getTrend(prices, lookback = 10) {
            if (prices.length < lookback) return 'NEUTRO';
            
            const recent = prices.slice(-lookback);
            const first = recent[0];
            const last = recent[recent.length - 1];
            const change = ((last - first) / first) * 100;
            
            if (change > 2) return 'ALTA';
            if (change < -2) return 'BAIXA';
            return 'NEUTRO';
        },

        // Encontrar suporte e resistência básicos
        findSupportResistance(prices, lookback = 20) {
            if (prices.length < lookback) return null;
            
            const recent = prices.slice(-lookback);
            const sorted = [...recent].sort((a, b) => a - b);
            
            // Aproximação simples
            const support = sorted[Math.floor(sorted.length * 0.2)]; // 20th percentile
            const resistance = sorted[Math.floor(sorted.length * 0.8)]; // 80th percentile
            
            return {
                support: support,
                resistance: resistance,
                current: recent[recent.length - 1]
            };
        }
    }
};

// Utilitários para formatação e conversão
const ChartUtils = {
    // Converter timestamp para data legível
    timestampToDate(timestamp, format = 'full') {
        const date = new Date(timestamp * 1000);
        
        switch(format) {
            case 'time':
                return date.toLocaleTimeString('pt-PT', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            case 'date':
                return date.toLocaleDateString('pt-PT');
            case 'datetime':
                return date.toLocaleString('pt-PT');
            case 'full':
            default:
                return date.toLocaleString('pt-PT', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
        }
    },

    // Formatar preços
    formatPrice(price, decimals = 4) {
        return new Intl.NumberFormat('pt-PT', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(price);
    },

    // Formatar percentagem
    formatPercentage(value, decimals = 2) {
        return new Intl.NumberFormat('pt-PT', {
            style: 'percent',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value / 100);
    },

    // Formatar volume
    formatVolume(volume) {
        if (volume >= 1000000) {
            return (volume / 1000000).toFixed(1) + 'M';
        } else if (volume >= 1000) {
            return (volume / 1000).toFixed(1) + 'K';
        }
        return volume.toLocaleString('pt-PT');
    },

    // Calcular cor baseada na mudança
    getChangeColor(change) {
        if (change > 0) return '#27ae60'; // Verde
        if (change < 0) return '#e74c3c'; // Vermelho
        return '#95a5a6'; // Cinzento neutro
    },

    // Validar dados de mercado
    validateMarketData(data) {
        if (!data || !Array.isArray(data.data)) {
            return { valid: false, error: 'Dados inválidos' };
        }
        
        if (data.data.length === 0) {
            return { valid: false, error: 'Sem dados disponíveis' };
        }
        
        // Verificar se cada ponto tem os campos necessários
        const requiredFields = ['timestamp', 'open', 'high', 'low', 'close'];
        for (const point of data.data) {
            for (const field of requiredFields) {
                if (point[field] === undefined || point[field] === null) {
                    return { valid: false, error: `Campo ${field} em falta` };
                }
            }
        }
        
        return { valid: true };
    },

    // Detectar tipo de instrumento baseado no símbolo
    detectInstrumentType(symbol) {
        if (symbol.includes('USD') || symbol.includes('BTC') || symbol.includes('ETH')) {
            return 'crypto';
        }
        if (symbol.startsWith('^')) {
            return 'index';
        }
        if (symbol.includes('=F')) {
            return 'commodity';
        }
        return 'stock';
    }
};

// Event listeners para responsividade
window.addEventListener('resize', () => {
    // Redimensionar gráficos quando a janela muda de tamanho
    if (window.TradingBot && window.TradingBot.state.charts) {
        Object.values(window.TradingBot.state.charts).forEach(chart => {
            if (chart) {
                ChartManager.resizeChart(chart);
            }
        });
    }
});

// Exportar para uso global
window.ChartManager = ChartManager;
window.ChartUtils = ChartUtils;