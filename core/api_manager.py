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
        # Ordem de preferência das APIs - Finnhub primeiro devido aos problemas do yfinance
        apis_to_try = ['finnhub', 'twelve_data', 'alpha_vantage', 'yfinance']
        
        for api_name in apis_to_try:
            # Pula APIs sem chave (exceto yfinance que é gratuito)
            if api_name != 'yfinance' and api_name not in self.api_keys:
                db_manager.add_log('DEBUG', f"API {api_name} não tem chave configurada, a pular", 'api_manager')
                continue
                
            if not self._check_rate_limit(api_name):
                db_manager.add_log('DEBUG', f"API {api_name} atingiu rate limit, a pular", 'api_manager')
                continue
                
            try:
                db_manager.add_log('DEBUG', f"Tentando obter dados via {api_name} para {symbol}", 'api_manager')
                
                if api_name == 'yfinance':
                    data = self._get_yfinance_data(symbol, interval)
                elif api_name == 'finnhub':
                    data = self._get_finnhub_data(symbol, interval)
                elif api_name == 'twelve_data':
                    data = self._get_twelve_data(symbol, interval)
                elif api_name == 'alpha_vantage':
                    data = self._get_alpha_vantage_data(symbol, interval)
                
                if data and data.get('data') and len(data['data']) > 0:
                    db_manager.add_log('INFO', f"Dados obtidos com sucesso via {api_name} para {symbol} ({len(data['data'])} velas)", 'api_manager')
                    return data
                else:
                    db_manager.add_log('WARNING', f"API {api_name} retornou dados vazios para {symbol}", 'api_manager')
                    continue
                    
            except Exception as e:
                db_manager.add_log('ERROR', f"Erro na API {api_name} para {symbol}: {e}", 'api_manager')
                continue
        
        db_manager.add_log('ERROR', f"Todas as APIs falharam para {symbol}", 'api_manager')
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
            
        try:
            # Mapeia intervalos
            td_intervals = {
                '1m': '1min',
                '30m': '30min',
                '1D': '1day'
            }
            
            if interval not in td_intervals:
                return None
            
            url = "https://api.twelvedata.com/time_series"
            params = {
                'symbol': symbol,
                'interval': td_intervals[interval],
                'outputsize': '100',
                'apikey': self.api_keys['twelve_data']
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            json_data = response.json()
            
            if 'values' not in json_data:
                return None
            
            # Converte para formato padrão
            data = {
                'symbol': symbol,
                'interval': interval,
                'data': []
            }
            
            # Os dados vêm em ordem decrescente, precisamos inverter
            for item in reversed(json_data['values']):
                try:
                    timestamp = int(datetime.fromisoformat(item['datetime']).timestamp())
                    data['data'].append({
                        'timestamp': timestamp,
                        'open': float(item['open']),
                        'high': float(item['high']),
                        'low': float(item['low']),
                        'close': float(item['close']),
                        'volume': int(item.get('volume', 0))
                    })
                except (ValueError, KeyError) as e:
                    continue
            
            self._record_api_call('twelve_data')
            return data if data['data'] else None
            
        except Exception as e:
            raise Exception(f"Erro Twelve Data: {e}")
    
    def _get_alpha_vantage_data(self, symbol: str, interval: str) -> Optional[Dict]:
        """Obtém dados via Alpha Vantage"""
        if 'alpha_vantage' not in self.api_keys:
            return None
            
        try:
            # Mapeia intervalos e funções
            if interval == '1D':
                function = 'TIME_SERIES_DAILY'
                interval_param = None
            else:
                function = 'TIME_SERIES_INTRADAY'
                av_intervals = {
                    '1m': '1min',
                    '30m': '30min'
                }
                interval_param = av_intervals.get(interval)
                if not interval_param:
                    return None
            
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': self.api_keys['alpha_vantage']
            }
            
            if interval_param:
                params['interval'] = interval_param
            
            url = "https://www.alphavantage.co/query"
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            json_data = response.json()
            
            # Encontra a chave dos dados temporais
            time_series_key = None
            for key in json_data.keys():
                if 'Time Series' in key:
                    time_series_key = key
                    break
            
            if not time_series_key or time_series_key not in json_data:
                return None
            
            time_series = json_data[time_series_key]
            
            # Converte para formato padrão
            data = {
                'symbol': symbol,
                'interval': interval,
                'data': []
            }
            
            # Ordena as datas e pega as últimas 100
            sorted_dates = sorted(time_series.keys())[-100:]
            
            for date_str in sorted_dates:
                item = time_series[date_str]
                try:
                    timestamp = int(datetime.fromisoformat(date_str).timestamp())
                    data['data'].append({
                        'timestamp': timestamp,
                        'open': float(item['1. open']),
                        'high': float(item['2. high']),
                        'low': float(item['3. low']),
                        'close': float(item['4. close']),
                        'volume': int(item.get('5. volume', 0))
                    })
                except (ValueError, KeyError) as e:
                    continue
            
            self._record_api_call('alpha_vantage')
            return data if data['data'] else None
            
        except Exception as e:
            raise Exception(f"Erro Alpha Vantage: {e}")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Obtém preço atual de um instrumento"""
        # Tenta yfinance primeiro (mais rápido e confiável)
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            
            # Tenta obter preço atual
            info = ticker.info
            current_price = info.get('currentPrice')
            
            if current_price:
                return float(current_price)
            
            # Fallback: último preço de fecho
            hist = ticker.history(period='1d', interval='1m')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
                
        except Exception as e:
            db_manager.add_log('WARNING', f"Erro ao obter preço via yfinance para {symbol}: {e}", 'api_manager')
        
        # Fallback para Finnhub
        if 'finnhub' in self.api_keys and self._check_rate_limit('finnhub'):
            try:
                url = "https://finnhub.io/api/v1/quote"
                params = {
                    'symbol': symbol,
                    'token': self.api_keys['finnhub']
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                current_price = data.get('c')  # Current price
                
                if current_price:
                    self._record_api_call('finnhub')
                    return float(current_price)
                    
            except Exception as e:
                db_manager.add_log('WARNING', f"Erro ao obter preço via Finnhub para {symbol}: {e}", 'api_manager')
        
        # Fallback para Twelve Data
        if 'twelve_data' in self.api_keys and self._check_rate_limit('twelve_data'):
            try:
                url = "https://api.twelvedata.com/price"
                params = {
                    'symbol': symbol,
                    'apikey': self.api_keys['twelve_data']
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                price = data.get('price')
                
                if price:
                    self._record_api_call('twelve_data')
                    return float(price)
                    
            except Exception as e:
                db_manager.add_log('WARNING', f"Erro ao obter preço via Twelve Data para {symbol}: {e}", 'api_manager')
        
        return None
    
    def get_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Obtém notícias relacionadas com um instrumento"""
        all_news = []
        
        # NewsAPI
        if 'newsapi' in self.api_keys and self._check_rate_limit('newsapi'):
            news = self._get_newsapi_news(symbol, limit // 2)
            all_news.extend(news)
        
        # Finnhub News
        if 'finnhub' in self.api_keys and self._check_rate_limit('finnhub'):
            news = self._get_finnhub_news(symbol, limit // 2)
            all_news.extend(news)
        
        # Remove duplicados e ordena por data
        seen_urls = set()
        unique_news = []
        
        for article in all_news:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_news.append(article)
        
        # Ordena por data (mais recente primeiro)
        unique_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        return unique_news[:limit]
    
    def _get_newsapi_news(self, symbol: str, limit: int) -> List[Dict]:
        """Obtém notícias via NewsAPI"""
        try:
            # Mapeia símbolos para nomes de empresas conhecidas
            company_names = {
                'AAPL': 'Apple',
                'MSFT': 'Microsoft',
                'GOOGL': 'Google',
                'AMZN': 'Amazon',
                'TSLA': 'Tesla',
                'META': 'Meta Facebook',
                'NVDA': 'NVIDIA',
                'BTC-USD': 'Bitcoin',
                'ETH-USD': 'Ethereum'
            }
            
            query = company_names.get(symbol, symbol)
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'sortBy': 'publishedAt',
                'pageSize': limit,
                'language': 'en',
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
                    'source': article.get('source', {}).get('name', 'NewsAPI'),
                    'sentiment': 'neutral'  # Pode ser melhorado com análise de sentimento
                })
            
            self._record_api_call('newsapi')
            return articles
            
        except Exception as e:
            db_manager.add_log('ERROR', f"Erro ao obter notícias via NewsAPI: {e}", 'api_manager')
            return []
    
    def _get_finnhub_news(self, symbol: str, limit: int) -> List[Dict]:
        """Obtém notícias via Finnhub"""
        try:
            # Data de há 7 dias
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            
            url = "https://finnhub.io/api/v1/company-news"
            params = {
                'symbol': symbol,
                'from': from_date,
                'to': to_date,
                'token': self.api_keys['finnhub']
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for article in data[:limit]:
                # Converte timestamp para ISO format
                published_at = datetime.fromtimestamp(article.get('datetime', 0)).isoformat()
                
                articles.append({
                    'title': article.get('headline', ''),
                    'description': article.get('summary', ''),
                    'url': article.get('url', ''),
                    'published_at': published_at,
                    'source': 'Finnhub',
                    'sentiment': article.get('sentiment', 'neutral')
                })
            
            self._record_api_call('finnhub')
            return articles
            
        except Exception as e:
            db_manager.add_log('ERROR', f"Erro ao obter notícias via Finnhub: {e}", 'api_manager')
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
                'limit': self.limits[api_name],
                'status': 'active' if api_name in self.api_keys and remaining_calls > 0 else 'inactive'
            }
        
        return status
    
    def update_api_keys(self, keys: Dict[str, str]):
        """Atualiza as API keys"""
        # Remove chaves vazias
        clean_keys = {k: v for k, v in keys.items() if v and v.strip()}
        
        self.api_keys.update(clean_keys)
        db_manager.save_api_keys(clean_keys)
        
        # Log da atualização
        db_manager.add_log(
            'INFO', 
            f'API keys atualizadas: {list(clean_keys.keys())}', 
            'api_manager'
        )
    
    def test_api_connection(self, provider: str) -> Dict[str, Any]:
        """Testa a conexão com uma API específica"""
        if provider not in self.api_keys:
            return {
                'success': False,
                'error': 'API key não configurada'
            }
        
        try:
            if provider == 'finnhub':
                # Testa com símbolo simples
                url = "https://finnhub.io/api/v1/quote"
                params = {
                    'symbol': 'AAPL',
                    'token': self.api_keys[provider]
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'c' in data:  # Current price exists
                    return {'success': True, 'message': 'Conexão bem-sucedida'}
                else:
                    return {'success': False, 'error': 'Resposta inválida da API'}
            
            elif provider == 'twelve_data':
                url = "https://api.twelvedata.com/price"
                params = {
                    'symbol': 'AAPL',
                    'apikey': self.api_keys[provider]
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'price' in data:
                    return {'success': True, 'message': 'Conexão bem-sucedida'}
                else:
                    return {'success': False, 'error': 'Resposta inválida da API'}
            
            elif provider == 'alpha_vantage':
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': 'AAPL',
                    'apikey': self.api_keys[provider]
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'Global Quote' in data:
                    return {'success': True, 'message': 'Conexão bem-sucedida'}
                else:
                    return {'success': False, 'error': 'Resposta inválida da API'}
            
            elif provider == 'newsapi':
                url = "https://newsapi.org/v2/top-headlines"
                params = {
                    'country': 'us',
                    'pageSize': 1,
                    'apiKey': self.api_keys[provider]
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == 'ok':
                    return {'success': True, 'message': 'Conexão bem-sucedida'}
                else:
                    return {'success': False, 'error': 'Resposta inválida da API'}
            
            else:
                return {'success': False, 'error': 'Provider não suportado'}
        
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Timeout na conexão'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'Erro de rede: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Erro inesperado: {str(e)}'}


# Instância global
api_manager = APIManager()