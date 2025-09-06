"""
Gestor de APIs para dados de mercado e notícias
Suporta múltiplas fontes com fallback automático
"""
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

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
        # Ordem de preferência das APIs
        apis_to_try = ['yfinance', 'finnhub', 'twelve_data', 'alpha_vantage']
        
        for api_name in apis_to_try:
            if not self._check_rate_limit(api_name):
                continue
                
            try:
                if api_name == 'yfinance':
                    return self._get_yfinance_data(symbol, interval)
                elif api_name == 'finnhub':
                    return self._get_finnhub_data(symbol, interval)
                elif api_name == 'twelve_data':
                    return self._get_twelve_data(symbol, interval)
                elif api_name == 'alpha_vantage':
                    return self._get_alpha_vantage_data(symbol, interval)
                    
            except Exception as e:
                print(f"Erro na API {api_name}: {e}")
                continue
        
        return None
    
    def _get_yfinance_data(self, symbol: str, interval: str) -> Optional[Dict]:
        """Obtém dados via yfinance"""
        try:
            import yfinance as yf
            
            # Mapeia intervalos
            yf_intervals = {
                '1m': '1m',
                '30m': '30m',
                '1D': '1d'
            }
            
            if interval not in yf_intervals:
                interval = '1d'
            
            ticker = yf.Ticker(symbol)
            
            # Período baseado no intervalo
            period_map = {
                '1m': '1d',    # 1 dia para dados de 1min
                '30m': '5d',   # 5 dias para dados de 30min
                '1d': '1y'     # 1 ano para dados diários
            }
            
            period = period_map.get(interval, '1y')
            hist = ticker.history(period=period, interval=yf_intervals[interval])
            
            if hist.empty:
                return None
            
            # Limita a 100 velas
            hist = hist.tail(100)
            
            # Converte para formato padrão
            data = {
                'symbol': symbol,
                'interval': interval,
                'data': []
            }
            
            for timestamp, row in hist.iterrows():
                data['data'].append({
                    'timestamp': int(timestamp.timestamp()),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']) if 'Volume' in row else 0
                })
            
            self._record_api_call('yfinance')
            return data
            
        except Exception as e:
            raise Exception(f"Erro yfinance: {e}")
    
    def _get_finnhub_data(self, symbol: str, interval: str) -> Optional[Dict]:
        """Obtém dados via Finnhub"""
        if 'finnhub' not in self.api_keys:
            return None
            
        try:
            # Mapeia intervalos
            finnhub_intervals = {
                '1m': '1',
                '30m': '30',
                '1D': 'D'
            }
            
            if interval not in finnhub_intervals:
                return None
            
            # Calcula timestamps
            end_time = int(time.time())
            
            if interval == '1m':
                start_time = end_time - (100 * 60)  # 100 minutos
            elif interval == '30m':
                start_time = end_time - (100 * 30 * 60)  # 100 * 30 minutos
            else:
                start_time = end_time - (100 * 24 * 60 * 60)  # 100 dias
            
            url = f"https://finnhub.io/api/v1/stock/candle"
            params = {
                'symbol': symbol,
                'resolution': finnhub_intervals[interval],
                'from': start_time,
                'to': end_time,
                'token': self.api_keys['finnhub']
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            json_data = response.json()
            
            if json_data.get('s') != 'ok':
                return None
            
            # Converte para formato padrão
            data = {
                'symbol': symbol,
                'interval': interval,
                'data': []
            }
            
            for i in range(len(json_data['t'])):
                data['data'].append({
                    'timestamp': json_data['t'][i],
                    'open': json_data['o'][i],
                    'high': json_data['h'][i],
                    'low': json_data['l'][i],
                    'close': json_data['c'][i],
                    'volume': json_data['v'][i]
                })
            
            self._record_api_call('finnhub')
            return data
            
        except Exception as e:
            raise Exception(f"Erro Finnhub: {e}")
    
    def _get_twelve_data(self, symbol: str, interval: str) -> Optional[Dict]:
        """Obtém dados via Twelve Data"""
        if 'twelve_data' not in self.api_keys:
            return None
            
        # Implementação similar às outras APIs
        # Por agora, retorna None para focar nas principais
        return None
    
    def _get_alpha_vantage_data(self, symbol: str, interval: str) -> Optional[Dict]:
        """Obtém dados via Alpha Vantage"""
        if 'alpha_vantage' not in self.api_keys:
            return None
            
        # Implementação similar às outras APIs
        # Por agora, retorna None para focar nas principais
        return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Obtém preço atual de um instrumento"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            
            # Tenta obter preço actual
            info = ticker.info
            current_price = info.get('currentPrice')
            
            if current_price:
                return float(current_price)
            
            # Fallback: último preço de fecho
            hist = ticker.history(period='1d')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
                
            return None
            
        except Exception as e:
            print(f"Erro ao obter preço atual de {symbol}: {e}")
            return None
    
    def get_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Obtém notícias relacionadas com um instrumento"""
        if 'newsapi' not in self.api_keys:
            return []
        
        try:
            # Implementação básica - pode ser expandida
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': symbol,
                'sortBy': 'publishedAt',
                'pageSize': limit,
                'apiKey': self.api_keys['newsapi']
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for article in data.get('articles', []):
                articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'source': article.get('source', {}).get('name', '')
                })
            
            self._record_api_call('newsapi')
            return articles
            
        except Exception as e:
            print(f"Erro ao obter notícias: {e}")
            return []
    
    def get_api_status(self) -> Dict[str, Any]:
        """Retorna estado das APIs"""
        status = {}
        
        for api_name in self.limits.keys():
            remaining_calls = self.limits[api_name]
            
            if api_name in self.last_calls:
                recent_calls = len([
                    call for call in self.last_calls[api_name]
                    if time.time() - call < 60
                ])
                remaining_calls = max(0, self.limits[api_name] - recent_calls)
            
            status[api_name] = {
                'has_key': api_name in self.api_keys,
                'remaining_calls': remaining_calls,
                'limit': self.limits[api_name]
            }
        
        return status
    
    def update_api_keys(self, keys: Dict[str, str]):
        """Actualiza as API keys"""
        self.api_keys.update(keys)
        db_manager.save_api_keys(keys)


# Instância global
api_manager = APIManager()