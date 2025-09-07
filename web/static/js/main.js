// Main JavaScript - Trading Bot
// Funcionalidades principais da aplicação

// Estado global da aplicação
const TradingBot = {
    state: {
        selectedInstruments: [],
        instruments: {},
        charts: {
            chart1: null,
            chart2: null
        },
        intervals: {
            chart1: '1D',
            chart2: '1D'
        }
    },

    // Inicialização da aplicação
    init() {
        console.log('🤖 Trading Bot iniciado');
        
        // Carrega dados iniciais
        this.loadInstruments();
        this.updateSystemStatus();
        this.setupEventListeners();
        
        // Atualiza status periodicamente
        setInterval(() => this.updateSystemStatus(), 30000);
    },

    // Configurar event listeners
    setupEventListeners() {
        // Pesquisa de instrumentos
        const searchInput = document.getElementById('search-instruments');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.filterInstruments(e.target.value));
        }

        // Botões de intervalo
        document.querySelectorAll('.interval-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleIntervalChange(e));
        });

        // Auto-refresh dos gráficos a cada 60 segundos
        setInterval(() => this.refreshCharts(), 60000);
    },

    // Carregar lista de instrumentos
    async loadInstruments() {
        const loadingEl = document.getElementById('instruments-loading');
        const errorEl = document.getElementById('instruments-error');
        const listEl = document.getElementById('instruments-list');

        try {
            console.log('📊 A carregar instrumentos...');
            
            const response = await fetch('/api/assets');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const instruments = await response.json();
            
            if (!instruments || Object.keys(instruments).length === 0) {
                throw new Error('Nenhum instrumento encontrado');
            }
            
            this.state.instruments = instruments;
            this.renderInstruments(instruments);
            
            // Mostrar lista
            if (loadingEl) loadingEl.style.display = 'none';
            if (errorEl) errorEl.style.display = 'none';
            if (listEl) listEl.style.display = 'block';
            
            console.log('✅ Instrumentos carregados:', Object.keys(instruments).length, 'categorias');
            
        } catch (error) {
            console.error('❌ Erro ao carregar instrumentos:', error);
            
            if (loadingEl) loadingEl.style.display = 'none';
            if (errorEl) {
                errorEl.style.display = 'block';
                errorEl.textContent = `Erro: ${error.message}`;
            }
        }
    },

    // Renderizar lista de instrumentos
    renderInstruments(instruments) {
        const listElement = document.getElementById('instruments-list');
        if (!listElement) return;

        const categories = {
            'indices': { name: 'Índices', icon: 'fa-chart-line' },
            'stocks': { name: 'Ações', icon: 'fa-building' },
            'commodities': { name: 'Commodities', icon: 'fa-coins' },
            'crypto': { name: 'Criptomoedas', icon: 'fa-bitcoin' }
        };

        let html = '';

        for (const [categoryKey, categoryData] of Object.entries(categories)) {
            if (instruments[categoryKey] && instruments[categoryKey].length > 0) {
                html += `
                    <div class="category-header" data-category="${categoryKey}">
                        <i class="fas ${categoryData.icon} me-2"></i>${categoryData.name}
                        <span class="badge bg-secondary ms-2">${instruments[categoryKey].length}</span>
                    </div>
                `;
                
                instruments[categoryKey].forEach(instrument => {
                    const isSelected = this.state.selectedInstruments.includes(instrument.symbol);
                    html += `
                        <div class="instrument-item ${isSelected ? 'selected' : ''}" 
                             data-symbol="${instrument.symbol}" 
                             data-name="${instrument.name}"
                             data-category="${categoryKey}">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <div class="fw-bold">${instrument.symbol}</div>
                                    <div class="text-muted small">${instrument.name}</div>
                                </div>
                                <div class="text-end">
                                    <i class="fas fa-plus text-primary" style="display: ${isSelected ? 'none' : 'inline'}"></i>
                                    <i class="fas fa-check text-success" style="display: ${isSelected ? 'inline' : 'none'}"></i>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
        }

        if (html === '') {
            html = '<div class="text-center text-muted p-3">Nenhum instrumento disponível</div>';
        }

        listElement.innerHTML = html;

        // Adicionar event listeners aos instrumentos
        listElement.querySelectorAll('.instrument-item').forEach(item => {
            item.addEventListener('click', () => {
                const symbol = item.dataset.symbol;
                const name = item.dataset.name;
                this.toggleInstrument(symbol, name);
            });
        });
    },

    // Alternar seleção de instrumento
    toggleInstrument(symbol, name) {
        const index = this.state.selectedInstruments.indexOf(symbol);
        
        if (index > -1) {
            // Remover instrumento
            this.state.selectedInstruments.splice(index, 1);
            console.log('🗑️ Removido instrumento:', symbol);
            
            // Destruir gráfico correspondente
            if (index === 0) {
                this.destroyChart('chart1');
                this.hideChart('chart1');
            } else if (index === 1) {
                this.destroyChart('chart2');
                this.hideChart('chart2');
            }
            
            // Reorganizar se necessário
            if (this.state.selectedInstruments.length === 1 && index === 0) {
                // Se removeu o primeiro e ainda há um segundo, move para o primeiro lugar
                const remaining = this.state.selectedInstruments[0];
                const remainingName = document.querySelector(`[data-symbol="${remaining}"]`).dataset.name;
                
                this.destroyChart('chart2');
                this.hideChart('chart2');
                
                this.loadChart(remaining, 'chart1', this.state.intervals.chart1);
                this.updateChartTitle('chart1', remaining, remainingName);
                this.showChart('chart1');
            }
            
        } else {
            // Adicionar instrumento (máximo 2)
            if (this.state.selectedInstruments.length >= 2) {
                this.showNotification('Máximo de 2 instrumentos. Remove um primeiro.', 'warning');
                return;
            }
            
            this.state.selectedInstruments.push(symbol);
            console.log('✅ Adicionado instrumento:', symbol);
            
            // Carregar gráfico
            const chartNum = this.state.selectedInstruments.length;
            const chartId = `chart${chartNum}`;
            
            this.loadChart(symbol, chartId, this.state.intervals[chartId]);
            this.updateChartTitle(chartId, symbol, name);
            this.showChart(chartId);
        }
        
        // Atualizar UI
        this.updateSelectedCount();
        this.updateNoChartsMessage();
        this.renderInstruments(this.state.instruments);
    },

    // Atualizar contador de selecionados
    updateSelectedCount() {
        const countEl = document.getElementById('selected-count');
        if (countEl) {
            countEl.textContent = `${this.state.selectedInstruments.length}/2`;
        }
    },

    // Atualizar mensagem quando não há gráficos
    updateNoChartsMessage() {
        const messageEl = document.getElementById('no-charts-message');
        if (messageEl) {
            const show = this.state.selectedInstruments.length === 0;
            messageEl.style.display = show ? 'block' : 'none';
        }
    },

    // Carregar dados do gráfico
    async loadChart(symbol, chartId, interval = '1D') {
        console.log(`📈 A carregar gráfico ${chartId} para ${symbol} (${interval})`);
        
        try {
            const response = await fetch(`/api/market/${symbol}?interval=${interval}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            if (!data.data || data.data.length === 0) {
                throw new Error('Sem dados disponíveis');
            }
            
            this.renderChart(data, chartId, symbol);
            this.updateCurrentPrice(chartId, data);
            
            console.log(`✅ Gráfico ${chartId} carregado com ${data.data.length} pontos`);
            
        } catch (error) {
            console.error(`❌ Erro ao carregar gráfico ${chartId}:`, error);
            this.showChartError(chartId, error.message);
        }
    },

    // Renderizar gráfico com Chart.js
    renderChart(data, chartId, symbol) {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        // Destruir gráfico existente
        this.destroyChart(chartId);
        
        // Preparar dados
        const chartData = this.prepareChartData(data, symbol);
        
        // Criar novo gráfico
        this.state.charts[chartId] = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: this.getChartOptions(symbol, data.interval)
        });
    },

    // Preparar dados para Chart.js
    prepareChartData(data, symbol) {
        const labels = data.data.map(d => {
            const date = new Date(d.timestamp * 1000);
            // Formato diferente baseado no intervalo
            if (data.interval === '1D') {
                return date.toLocaleDateString('pt-PT');
            } else {
                return date.toLocaleTimeString('pt-PT', {hour: '2-digit', minute:'2-digit'});
            }
        });
        
        const prices = data.data.map(d => d.close);
        
        // Determinar cor baseada na tendência
        const firstPrice = prices[0];
        const lastPrice = prices[prices.length - 1];
        const isPositive = lastPrice >= firstPrice;
        
        return {
            labels: labels,
            datasets: [{
                label: `${symbol} (${data.interval})`,
                data: prices,
                borderColor: isPositive ? '#27ae60' : '#e74c3c',
                backgroundColor: isPositive ? 'rgba(39, 174, 96, 0.1)' : 'rgba(231, 76, 60, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.2,
                pointRadius: 0,
                pointHoverRadius: 4
            }]
        };
    },

    // Opções do gráfico
    getChartOptions(symbol, interval) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '€' + value.toFixed(4);
                        }
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    ticks: {
                        maxTicksLimit: 8
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: €${context.parsed.y.toFixed(4)}`;
                        }
                    }
                }
            },
            animation: {
                duration: 750,
                easing: 'easeInOutQuart'
            }
        };
    },

    // Atualizar preço atual
    updateCurrentPrice(chartId, data) {
        const priceElement = document.getElementById(`${chartId}-price`);
        if (!priceElement || !data.current_price) return;

        let changeClass = '';
        let changeText = '';
        
        if (data.change !== undefined) {
            changeClass = data.change >= 0 ? 'positive' : 'negative';
            const changeSign = data.change >= 0 ? '+' : '';
            changeText = ` (${changeSign}€${data.change.toFixed(4)}, ${changeSign}${data.change_percent.toFixed(2)}%)`;
        }
        
        priceElement.innerHTML = `<span class="${changeClass}">€${data.current_price.toFixed(4)}${changeText}</span>`;
    },

    // Atualizar título do gráfico
    updateChartTitle(chartId, symbol, name) {
        const titleEl = document.getElementById(`${chartId}-title`);
        if (titleEl) {
            titleEl.textContent = `${symbol} - ${name}`;
        }
    },

    // Mostrar gráfico
    showChart(chartId) {
        const chartCard = document.getElementById(`${chartId}-card`);
        if (chartCard) {
            chartCard.style.display = 'block';
        }
    },

    // Esconder gráfico
    hideChart(chartId) {
        const chartCard = document.getElementById(`${chartId}-card`);
        if (chartCard) {
            chartCard.style.display = 'none';
        }
    },

    // Destruir gráfico
    destroyChart(chartId) {
        if (this.state.charts[chartId]) {
            this.state.charts[chartId].destroy();
            this.state.charts[chartId] = null;
        }
    },

    // Mostrar erro no gráfico
    showChartError(chartId, errorMessage) {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Estilo do erro
        ctx.font = '16px Arial';
        ctx.fillStyle = '#e74c3c';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Texto de erro
        ctx.fillText('❌ Erro ao carregar dados', canvas.width/2, canvas.height/2 - 10);
        ctx.font = '12px Arial';
        ctx.fillStyle = '#666';
        ctx.fillText(errorMessage, canvas.width/2, canvas.height/2 + 15);
    },

    // Lidar com mudança de intervalo
    handleIntervalChange(event) {
        const button = event.target;
        const interval = button.dataset.interval;
        const chartNum = button.dataset.chart;
        const chartId = `chart${chartNum}`;
        
        // Atualizar botões ativos
        const chartButtons = document.querySelectorAll(`[data-chart="${chartNum}"]`);
        chartButtons.forEach(btn => {
            btn.classList.remove('active', 'btn-secondary');
            btn.classList.add('btn-outline-secondary');
        });
        
        button.classList.remove('btn-outline-secondary');
        button.classList.add('btn-secondary', 'active');
        
        // Atualizar intervalo e recarregar gráfico
        this.state.intervals[chartId] = interval;
        const symbol = this.state.selectedInstruments[parseInt(chartNum) - 1];
        
        if (symbol) {
            this.loadChart(symbol, chartId, interval);
        }
    },

    // Filtrar instrumentos
    filterInstruments(searchTerm) {
        const items = document.querySelectorAll('.instrument-item');
        const categories = document.querySelectorAll('.category-header');
        
        searchTerm = searchTerm.toLowerCase().trim();
        
        if (!searchTerm) {
            // Mostrar tudo se não há pesquisa
            items.forEach(item => item.style.display = 'block');
            categories.forEach(cat => cat.style.display = 'block');
            return;
        }
        
        items.forEach(item => {
            const symbol = item.dataset.symbol.toLowerCase();
            const name = item.dataset.name.toLowerCase();
            const matches = symbol.includes(searchTerm) || name.includes(searchTerm);
            item.style.display = matches ? 'block' : 'none';
        });
        
        // Esconder categorias vazias
        categories.forEach(header => {
            const category = header.dataset.category;
            const categoryItems = document.querySelectorAll(`[data-category="${category}"].instrument-item`);
            const hasVisibleItems = Array.from(categoryItems).some(item => item.style.display !== 'none');
            header.style.display = hasVisibleItems ? 'block' : 'none';
        });
    },

    // Atualizar status do sistema
    async updateSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.error) {
                this.updateStatusIndicator(false, 'Erro');
                return;
            }
            
            // Atualizar saldo
            const balance = parseFloat(data.portfolio.balance) || 0;
            const balanceFormatted = new Intl.NumberFormat('pt-PT', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(balance);
            
            this.updateElement('balance-value', balanceFormatted);
            this.updateElement('portfolio-balance-main', '€' + balanceFormatted);
            
            // Atualizar estatísticas
            this.updateElement('open-trades', data.portfolio.open_trades || 0);
            
            // Atualizar status
            const canTrade = data.portfolio.can_trade;
            this.updateStatusIndicator(canTrade, canTrade ? 'Online' : 'Restrito');
            
        } catch (error) {
            console.error('❌ Erro ao atualizar status:', error);
            this.updateStatusIndicator(false, 'Offline');
        }
    },

    // Atualizar indicador de status
    updateStatusIndicator(isOnline, text) {
        const icon = document.getElementById('status-icon');
        const statusText = document.getElementById('status-text');
        
        if (icon) {
            icon.className = isOnline ? 'fas fa-circle status-online' : 'fas fa-circle status-offline';
        }
        
        if (statusText) {
            statusText.textContent = text;
        }
    },

    // Atualizar elemento por ID
    updateElement(id, content) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = content;
        }
    },

    // Mostrar notificação
    showNotification(message, type = 'info') {
        // Implementação simples com alert por agora
        // Pode ser substituído por um sistema de toast mais elegante
        console.log(`📢 ${type.toUpperCase()}: ${message}`);
        alert(message);
    },

    // Refresh todos os gráficos ativos
    refreshCharts() {
        this.state.selectedInstruments.forEach((symbol, index) => {
            const chartId = `chart${index + 1}`;
            const interval = this.state.intervals[chartId];
            if (this.state.charts[chartId]) {
                this.loadChart(symbol, chartId, interval);
            }
        });
    },

    // Utilitários de formatação
    formatCurrency(value) {
        return new Intl.NumberFormat('pt-PT', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 2
        }).format(value);
    },

    formatPercentage(value) {
        return new Intl.NumberFormat('pt-PT', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value / 100);
    }
};

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    TradingBot.init();
});

// Exportar para uso global
window.TradingBot = TradingBot;