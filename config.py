"""
config.py - Configuração principal do Trading Bot
"""

import os
from datetime import datetime

class Config:
    """Configuração base da aplicação"""
    
    # Configurações da Aplicação
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'trading-bot-secret-key-2024'
    DEBUG = True
    
    # Base de Dados
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'trading_bot.db')
    DATABASE_BACKUP_PATH = os.path.join(os.path.dirname(__file__), 'data', 'backups')
    
    # Carteira Virtual
    INITIAL_BALANCE = 100000.0  # €100,000
    CURRENCY = 'EUR'
    
    # API Keys - Substitui pelas tuas keys reais
    API_KEYS = {
        'FINNHUB': 'd2mb0n9r01qq6fopqje0d2mb0n9r01qq6fopqjeg',
        'TWELVE_DATA': 'cd4c76b8401747faa066d1ee8a0ad97a',
        'ALPHA_VANTAGE': 'YK3EAJ4G4DT1LEQ4',
        'NEWS_API': '141cfc70afd14c8ba34d71b0d85fbbdd',
        'REDDIT_CLIENT_ID': '',  # Adiciona quando obtiveres
        'REDDIT_CLIENT_SECRET': '',  # Adiciona quando obtiveres
        'TWITTER_BEARER_TOKEN': ''  # Adiciona quando obtiveres
    }
    
    # URLs das APIs
    API_URLS = {
        'FINNHUB': 'https://finnhub.io/api/v1',
        'TWELVE_DATA': 'https://api.twelvedata.com',
        'ALPHA_VANTAGE': 'https://www.alphavantage.co/query',
        'NEWS_API': 'https://newsapi.org/v2',
        'REDDIT': 'https://www.reddit.com',
        'TWITTER': 'https://api.twitter.com/2'
    }
    
    # Configurações de Trading
    TRADING_RULES = {
        'MAX_TRADES_PER_DAY': 5,
        'MAX_ACTIVE_POSITIONS': 1,
        'PROFIT_TARGET_EXIT': 0.05,  # 5% lucro para encerrar dia
        'DEFAULT_STOP_LOSS': 0.02,   # 2% stop loss
        'DEFAULT_TAKE_PROFIT': 0.05, # 5% take profit
        'MIN_TRADE_AMOUNT': 1000.0,  # Mínimo €1000 por trade
        'MAX_TRADE_AMOUNT': 10000.0  # Máximo €10000 por trade
    }
    
    # Configurações de Gráficos
    CHART_CONFIG = {
        'MAX_CANDLES': 100,
        'DEFAULT_INTERVAL': '1D',
        'AVAILABLE_INTERVALS': ['1m', '5m', '15m', '30m', '1H', '1D'],
        'MAX_SIMULTANEOUS_CHARTS': 2
    }
    
    # Configurações de Assets
    ASSETS_CONFIG = {
        'MAX_ACTIVE_INSTRUMENTS': 2,
        'CATEGORIES': ['indices', 'stocks', 'commodities', 'crypto'],
        'FILES': {
            'indices': 'assets/indices.txt',
            'stocks': 'assets/stocks.txt', 
            'commodities': 'assets/commodities.txt',
            'crypto': 'assets/crypto.txt'
        }
    }
    
    # Configurações de Cache
    CACHE_CONFIG = {
        'PRICE_CACHE_SECONDS': 30,      # Cache preços por 30 segundos
        'NEWS_CACHE_MINUTES': 15,       # Cache notícias por 15 minutos
        'SENTIMENT_CACHE_MINUTES': 30   # Cache sentimento por 30 minutos
    }
    
    # Logging
    LOGGING_CONFIG = {
        'LOG_LEVEL': 'INFO',
        'LOG_FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'LOG_FILES': {
            'MAIN': 'logs/trading.log',
            'API': 'logs/api_calls.log',
            'ERROR': 'logs/errors.log'
        },
        'MAX_LOG_SIZE': 10 * 1024 * 1024,  # 10MB
        'BACKUP_COUNT': 5
    }
    
    # Web Interface
    WEB_CONFIG = {
        'HOST': '0.0.0.0',
        'PORT': 5000,
        'THREADED': True,
        'AUTO_RELOAD': True
    }
    
    # Configurações de Sentimento
    SENTIMENT_CONFIG = {
        'KEYWORDS_TO_TRACK': [
            'stock market', 'trading', 'finance', 'economy', 
            'bull market', 'bear market', 'recession', 'inflation'
        ],
        'SENTIMENT_THRESHOLD': 0.1,  # Threshold para considerar sentimento
        'MAX_NEWS_ARTICLES': 50,
        'MAX_SOCIAL_POSTS': 100
    }
    
    # Rate Limiting
    RATE_LIMITS = {
        'FINNHUB_PER_MINUTE': 60,
        'TWELVE_DATA_PER_MINUTE': 8,  # Tier gratuito
        'ALPHA_VANTAGE_PER_MINUTE': 5,
        'NEWS_API_PER_HOUR': 1000
    }

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    TESTING = False
    
    # Configurações mais restritivas para produção
    TRADING_RULES = {
        'MAX_TRADES_PER_DAY': 3,
        'MAX_ACTIVE_POSITIONS': 1,
        'PROFIT_TARGET_EXIT': 0.03,  # 3% mais conservador
        'DEFAULT_STOP_LOSS': 0.015,  # 1.5% stop loss mais apertado
        'DEFAULT_TAKE_PROFIT': 0.03, # 3% take profit
        'MIN_TRADE_AMOUNT': 2000.0,  # Mínimo €2000 por trade
        'MAX_TRADE_AMOUNT': 5000.0   # Máximo €5000 por trade
    }

class TestingConfig(Config):
    """Configuração para testes"""
    DEBUG = True
    TESTING = True
    DATABASE_PATH = ':memory:'  # Base de dados em memória para testes
    INITIAL_BALANCE = 10000.0   # Saldo menor para testes

# Configuração activa (muda conforme ambiente)
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Retorna a configuração baseada na variável de ambiente"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)

# Utilitários de configuração
def update_api_key(provider: str, key: str):
    """Actualiza uma API key específica"""
    if provider.upper() in Config.API_KEYS:
        Config.API_KEYS[provider.upper()] = key
        return True
    return False

def get_api_key(provider: str) -> str:
    """Obtém uma API key específica"""
    return Config.API_KEYS.get(provider.upper(), '')

def get_asset_file_path(category: str) -> str:
    """Obtém o caminho do ficheiro de assets para uma categoria"""
    return Config.ASSETS_CONFIG['FILES'].get(category, '')