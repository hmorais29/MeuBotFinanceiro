#!/usr/bin/env python3
"""
Trading Bot Autónomo - Aplicação Principal
Ponto de entrada da aplicação Flask com interface web completa
"""

import os
import sys

# Adiciona path da app web
sys.path.append(os.path.join(os.path.dirname(__file__), 'web'))

from web.app import app
from core.database import db_manager

if __name__ == '__main__':
    # Inicializa base de dados
    print("🔧 A inicializar base de dados...")
    db_manager.init_database()
    
    # Configura API keys padrão se não existirem
    existing_keys = db_manager.get_api_keys()
    if not existing_keys:
        default_keys = {
            'finnhub': 'd2mb0n9r01qq6fopqje0d2mb0n9r01qq6fopqjeg',
            'twelve_data': 'cd4c76b8401747faa066d1ee8a0ad97a',
            'alpha_vantage': 'YK3EAJ4G4DT1LEQ4',
            'newsapi': '141cfc70afd14c8ba34d71b0d85fbbdd'
        }
        db_manager.save_api_keys(default_keys)
        print("🔑 API keys padrão configuradas")
    
    print("🚀 A iniciar Trading Bot...")
    print("📊 Dashboard disponível em: http://127.0.0.1:5000")
    print("📈 Gráficos disponíveis em: http://127.0.0.1:5000/charts")
    print("💰 Carteira disponível em: http://127.0.0.1:5000/portfolio")
    
    # Debug mode para desenvolvimento
    app.run(debug=True, host='127.0.0.1', port=5000)