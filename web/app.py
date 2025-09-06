"""
Flask Web App para Trading Bot
Interface web completa com dashboard, gráficos e gestão
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys

# Adiciona path do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import db_manager
from core.api_manager import api_manager
from core.portfolio import portfolio_manager

app = Flask(__name__)
CORS(app)

# Configuração
app.config['SECRET_KEY'] = 'trading-bot-secret-key-2025'
app.config['JSON_SORT_KEYS'] = False

@app.route('/')
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard.html')

@app.route('/portfolio')
def portfolio():
    """Página da carteira"""
    return render_template('portfolio.html')

@app.route('/charts')
def charts():
    """Página de gráficos"""
    return render_template('charts.html')

@app.route('/settings')
def settings():
    """Página de configurações"""
    return render_template('settings.html')

# === API ROUTES ===

@app.route('/api/status')
def api_status():
    """Estado geral do sistema"""
    try:
        portfolio_stats = portfolio_manager.get_portfolio_stats()
        api_status_data = api_manager.get_api_status()
        
        return jsonify({
            'status': 'running',
            'timestamp': portfolio_stats['last_updated'],
            'portfolio': {
                'balance': portfolio_stats['balance'],
                'currency': portfolio_stats['currency'],
                'can_trade': portfolio_stats['can_trade'],
                'open_trades': portfolio_stats['open_trades']
            },
            'apis': api_status_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio')
def api_portfolio():
    """Dados completos da carteira"""
    try:
        stats = portfolio_manager.get_portfolio_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/history')
def api_portfolio_history():
    """Histórico de trades"""
    try:
        limit = request.args.get('limit', 20, type=int)
        history = portfolio_manager.get_trade_history(limit)
        return jsonify({'trades': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets')
def api_assets():
    """Lista de instrumentos por categoria"""
    try:
        assets = {}
        
        asset_files = {
            'indices': 'assets/indices.txt',
            'stocks': 'assets/stocks.txt',
            'commodities': 'assets/commodities.txt',
            'crypto': 'assets/crypto.txt'
        }
        
        for category, filepath in asset_files.items():
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    assets[category] = []
                    for line in f:
                        if line.strip():
                            parts = line.strip().split(',', 1)
                            if len(parts) == 2:
                                symbol, name = parts
                                assets[category].append({
                                    'symbol': symbol.strip(),
                                    'name': name.strip()
                                })
        
        return jsonify(assets)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/<symbol>')
def api_market_data(symbol):
    """Dados de mercado para um símbolo"""
    try:
        interval = request.args.get('interval', '1D')
        
        # Valida intervalo
        if interval not in ['1m', '30m', '1D']:
            interval = '1D'
        
        data = api_manager.get_market_data(symbol, interval)
        
        if data is None:
            return jsonify({'error': f'Dados não disponíveis para {symbol}'}), 404
        
        # Adiciona informações extra
        current_price = api_manager.get_current_price(symbol)
        if current_price:
            data['current_price'] = current_price
            
            # Calcula variação se houver dados
            if data['data'] and len(data['data']) > 0:
                last_close = data['data'][-1]['close']
                if len(data['data']) > 1:
                    prev_close = data['data'][-2]['close']
                    change = current_price - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close > 0 else 0
                    
                    data['change'] = round(change, 4)
                    data['change_percent'] = round(change_percent, 2)
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/<symbol>/price')
def api_current_price(symbol):
    """Preço atual de um símbolo"""
    try:
        price = api_manager.get_current_price(symbol)
        
        if price is None:
            return jsonify({'error': f'Preço não disponível para {symbol}'}), 404
        
        return jsonify({
            'symbol': symbol,
            'price': price,
            'timestamp': portfolio_manager.get_portfolio_stats()['last_updated']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trade', methods=['POST'])
def api_execute_trade():
    """Executa um trade"""
    try:
        data = request.get_json()
        
        required_fields = ['symbol', 'side', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        trade_id = portfolio_manager.execute_trade(
            symbol=data['symbol'],
            side=data['side'],
            amount=float(data['amount']),
            justification=data.get('justification', ''),
            strategy=data.get('strategy', 'manual')
        )
        
        if trade_id:
            return jsonify({
                'success': True,
                'trade_id': trade_id,
                'message': f'Trade executado com sucesso'
            })
        else:
            return jsonify({'error': 'Erro ao executar trade'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/trade/<int:trade_id>/close', methods=['POST'])
def api_close_trade(trade_id):
    """Fecha um trade"""
    try:
        data = request.get_json() or {}
        justification = data.get('justification', 'Fecho manual')
        
        success = portfolio_manager.close_trade(trade_id, justification)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Trade {trade_id} fechado com sucesso'
            })
        else:
            return jsonify({'error': 'Erro ao fechar trade'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/settings/portfolio', methods=['GET', 'POST'])
def api_portfolio_settings():
    """Configurações da carteira"""
    if request.method == 'POST':
        try:
            settings = request.get_json()
            portfolio_manager.update_settings(settings)
            return jsonify({'success': True, 'message': 'Configurações atualizadas'})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        # GET - retorna configurações atuais
        return jsonify({
            'max_trades_per_day': portfolio_manager.max_trades_per_day,
            'max_open_trades': portfolio_manager.max_open_trades,
            'daily_profit_target': portfolio_manager.daily_profit_target,
            'stop_loss_percentage': portfolio_manager.stop_loss_percentage,
            'take_profit_percentage': portfolio_manager.take_profit_percentage
        })

@app.route('/api/settings/api-keys', methods=['GET', 'POST'])
def api_keys_settings():
    """Gestão de API keys"""
    if request.method == 'POST':
        try:
            keys = request.get_json()
            api_manager.update_api_keys(keys)
            return jsonify({'success': True, 'message': 'API keys atualizadas'})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        # GET - retorna estado das APIs (sem mostrar as keys)
        status = api_manager.get_api_status()
        return jsonify(status)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)