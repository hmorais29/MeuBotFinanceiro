"""
Gestor de APIs para dados de mercado e notícias
Suporta múltiplas fontes com fallback automático
"""
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

# Importação condicional do yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
    print("✅ yfinance importado com sucesso")
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance não disponível - usando apenas APIs web")

from core.database import db_manager


class APIManager:
    def __init__(self):
        self.rate_limits = {}
        self.last_calls = {}
        
        # Carrega API keys da base de dados
        self.api_keys = db_manager.get_api_keys()
        
        # Rate limits por API (calls per minute)
        self.limits = {
            'finnhub': 60,
            'twelve_data': 8,
            'alpha_vantage': 5,
            'newsapi': 100,
            'yfinance': 2000  # Sem limite oficial, mas vamos ser conservadores
        }
        
        print(f"🔑 API Manager inicializado com {len(self.api_keys)} chaves")
    
    def _check_rate_limit(self, api_name: str) -> bool:
        """Verifica se podemos fazer uma chamada à API"""
        now = time.time()
        
        if api_name not in self.last_calls:
            self.last_calls[api_name] = []
        
        # Remove chamadas antigas (mais de 1 minuto)
        self.last_calls[api_name] = [
            call_time for call_time in self.last_calls[api_name] 
            if now - call_time < 60
        ]
        
        # Verifica se podemos fazer mais uma chamada
        if len(self.last_calls[api_name]) >= self.limits[api_name]:
            return False
        
        return True
    
    def _record_api_call(self, api_name: str):
        """Regista uma chamada à API para rate limiting"""
        if api_name not in self.last_calls:
            self.last_calls[api_name] = []
        
        self.last_calls[api_name].append(time.time())
    
    def get_market_data(self, symbol: str, interval: str = '1D') -> Optional[Dict]:
        """
        Obtém dados de mercado com fallback automático entre APIs
        
        Args:
            symbol: Símbolo do instrumento (ex: AAPL, ^GSPC)
            interval: Intervalo (1m, 30m, 1D)
            
        Returns:
            Dict com dados OHLCV ou None se falhar
        """
        print(f"📊 Obtendo dados para {symbol} ({interval})")
        
        # Ordem de preferência das APIs
        apis_to_try = []
        if YFINANCE_AVAILABLE:
            apis_to_try.append('yfinance')
        
        # Adicionar outras APIs se tiverem keys
        if 'finnhub' in self.api_keys:
            apis_to_try.append('finnhub')
        if 'twelve