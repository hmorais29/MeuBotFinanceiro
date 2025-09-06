#!/usr/bin/env python3
"""
run.py - Trading Bot Autónomo
Ponto de entrada principal para desenvolvimento e produção
"""

import os
import sys
import argparse
from pathlib import Path

# Adiciona o diretório raiz ao Python path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

def create_directories():
    """Cria diretórios necessários se não existirem"""
    directories = [
        'data',
        'data/cache',
        'data/backups',
        'logs',
        'assets'
    ]
    
    for directory in directories:
        dir_path = ROOT_DIR / directory
        dir_path.mkdir(exist_ok=True)
        print(f"📁 Diretório verificado: {directory}")

def create_asset_files():
    """Cria ficheiros de assets se não existirem"""
    assets = {
        'assets/indices.txt': [
            '^GSPC,S&P 500',
            '^DJI,Dow Jones Industrial Average',
            '^IXIC,NASDAQ Composite',
            '^RUT,Russell 2000',
            '^FTSE,FTSE 100',
            '^GDAXI,DAX',
            '^FCHI,CAC 40',
            '^N225,Nikkei 225',
            '^HSI,Hang Seng Index',
            '^AXJO,ASX 200'
        ],
        'assets/stocks.txt': [
            'AAPL,Apple Inc.',
            'MSFT,Microsoft Corporation',
            'GOOGL,Alphabet Inc.',
            'AMZN,Amazon.com Inc.',
            'TSLA,Tesla Inc.',
            'META,Meta Platforms Inc.',
            'NVDA,NVIDIA Corporation',
            'BRK-B,Berkshire Hathaway',
            'JNJ,Johnson & Johnson',
            'V,Visa Inc.'
        ],
        'assets/commodities.txt': [
            'GC=F,Gold',
            'SI=F,Silver',
            'CL=F,Crude Oil WTI',
            'BZ=F,Brent Crude Oil',
            'NG=F,Natural Gas',
            'HG=F,Copper',
            'PL=F,Platinum',
            'PA=F,Palladium',
            'ZC=F,Corn',
            'ZS=F,Soybeans'
        ],
        'assets/crypto.txt': [
            'BTC-USD,Bitcoin',
            'ETH-USD,Ethereum',
            'BNB-USD,Binance Coin',
            'XRP-USD,XRP',
            'ADA-USD,Cardano',
            'SOL-USD,Solana',
            'DOGE-USD,Dogecoin',
            'DOT-USD,Polkadot',
            'AVAX-USD,Avalanche',
            'MATIC-USD,Polygon'
        ]
    }
    
    for filepath, content in assets.items():
        file_path = ROOT_DIR / filepath
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content) + '\n')
            print(f"📄 Ficheiro criado: {filepath}")
        else:
            print(f"📄 Ficheiro já existe: {filepath}")

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    required_modules = [
        'flask',
        'flask_cors',
        'requests',
        'sqlite3'  # Built-in no Python
    ]
    
    missing = []
    for module in required_modules:
        try:
            if module == 'sqlite3':
                import sqlite3
            elif module == 'flask_cors':
                from flask_cors import CORS
            else:
                __import__(module)
            print(f"✅ {module} - OK")
        except ImportError:
            missing.append(module)
            print(f"❌ {module} - FALTA")
    
    if missing:
        print(f"\n🚨 Instala as dependências em falta:")
        print(f"pip install {' '.join(missing)}")
        return False
    return True

def init_database():
    """Inicializa a base de dados"""
    try:
        from core.database import db_manager
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
        
        print("✅ Base de dados inicializada com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar base de dados: {e}")
        return False

def run_web_app(host='127.0.0.1', port=5000, debug=True):
    """Executa a aplicação web Flask"""
    try:
        # Importa a app do módulo web
        from web.app import app
        
        print("\n" + "="*50)
        print("🚀 Trading Bot Autónomo - A iniciar...")
        print("="*50)
        print(f"📊 Dashboard: http://{host}:{port}")
        print(f"📈 Gráficos: http://{host}:{port}/charts")
        print(f"💰 Carteira: http://{host}:{port}/portfolio")
        print(f"⚙️  Configurações: http://{host}:{port}/settings")
        print("="*50)
        print("💡 Pressiona Ctrl+C para parar")
        print("="*50 + "\n")
        
        # Executa a app
        app.run(
            debug=debug,
            host=host,
            port=port,
            use_reloader=debug,
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ Erro ao importar aplicação web: {e}")
        print("Verifica se todos os módulos estão criados corretamente")
        return False
    except Exception as e:
        print(f"❌ Erro ao executar aplicação: {e}")
        return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Trading Bot Autónomo')
    parser.add_argument('--host', default='127.0.0.1', help='Host da aplicação')
    parser.add_argument('--port', type=int, default=5000, help='Porto da aplicação')
    parser.add_argument('--no-debug', action='store_true', help='Desativa modo debug')
    parser.add_argument('--check-only', action='store_true', help='Apenas verifica setup')
    
    args = parser.parse_args()
    
    print("🤖 Trading Bot Autónomo - Setup")
    print("-" * 40)
    
    # 1. Criar diretórios
    create_directories()
    
    # 2. Criar ficheiros de assets
    create_asset_files()
    
    # 3. Verificar dependências
    if not check_dependencies():
        print("\n❌ Setup incompleto. Instala as dependências primeiro.")
        return False
    
    # 4. Inicializar base de dados
    if not init_database():
        print("\n❌ Falha na inicialização da base de dados.")
        return False
    
    if args.check_only:
        print("\n✅ Setup completo! A aplicação está pronta.")
        return True
    
    # 5. Executar aplicação web
    debug_mode = not args.no_debug
    return run_web_app(args.host, args.port, debug_mode)

if __name__ == '__main__':
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Trading Bot parado pelo utilizador")
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        sys.exit(1)