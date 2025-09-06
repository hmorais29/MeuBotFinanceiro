"""
Gestor da Base de Dados SQLite
Gere todas as operações de persistência de dados
"""
import sqlite3
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str = "data/trading_bot.db"):
        self.db_path = db_path
        
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Inicializa base de dados
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexões à base de dados"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acesso por nome de coluna
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Inicializa todas as tabelas necessárias"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de configurações gerais
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de API keys
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    provider TEXT PRIMARY KEY,
                    api_key TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela da carteira
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    balance REAL NOT NULL DEFAULT 100000.0,
                    total_deposited REAL DEFAULT 100000.0,
                    total_withdrawn REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de trades
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
                    quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_time TIMESTAMP,
                    status TEXT DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED')),
                    pnl REAL DEFAULT 0.0,
                    pnl_percentage REAL DEFAULT 0.0,
                    justification TEXT,
                    strategy TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de movimentos da carteira
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL CHECK (type IN ('DEPOSIT', 'WITHDRAWAL', 'TRADE')),
                    amount REAL NOT NULL,
                    description TEXT,
                    balance_before REAL NOT NULL,
                    balance_after REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de logs do sistema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR')),
                    message TEXT NOT NULL,
                    module TEXT,
                    extra_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Inicializa carteira se não existir
            cursor.execute("SELECT COUNT(*) FROM portfolio")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO portfolio (balance, total_deposited) 
                    VALUES (100000.0, 100000.0)
                """)
                
                # Log inicial
                cursor.execute("""
                    INSERT INTO portfolio_movements 
                    (type, amount, description, balance_before, balance_after)
                    VALUES ('DEPOSIT', 100000.0, 'Depósito inicial', 0.0, 100000.0)
                """)
    
    # === Métodos para API Keys ===
    def get_api_keys(self) -> Dict[str, str]:
        """Obtém todas as API keys ativas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT provider, api_key 
                FROM api_keys 
                WHERE is_active = 1
            """)
            
            return {row['provider']: row['api_key'] for row in cursor.fetchall()}
    
    def save_api_keys(self, keys: Dict[str, str]):
        """Guarda ou atualiza API keys"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for provider, api_key in keys.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO api_keys 
                    (provider, api_key, updated_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (provider, api_key))
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Obtém uma API key específica"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT api_key FROM api_keys 
                WHERE provider = ? AND is_active = 1
            """, (provider,))
            
            row = cursor.fetchone()
            return row['api_key'] if row else None
    
    # === Métodos para Carteira ===
    def get_portfolio_balance(self) -> float:
        """Obtém saldo atual da carteira"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT balance FROM portfolio 
                ORDER BY id DESC LIMIT 1
            """)
            
            row = cursor.fetchone()
            return float(row['balance']) if row else 100000.0
    
    def update_portfolio_balance(self, new_balance: float, description: str = ""):
        """Atualiza saldo da carteira"""
        current_balance = self.get_portfolio_balance()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Atualiza saldo
            cursor.execute("""
                UPDATE portfolio 
                SET balance = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = (SELECT MAX(id) FROM portfolio)
            """, (new_balance,))
            
            # Regista movimento
            cursor.execute("""
                INSERT INTO portfolio_movements 
                (type, amount, description, balance_before, balance_after)
                VALUES ('TRADE', ?, ?, ?, ?)
            """, (new_balance - current_balance, description, current_balance, new_balance))
    
    def deposit_funds(self, amount: float, description: str = "Depósito"):
        """Adiciona fundos à carteira"""
        current_balance = self.get_portfolio_balance()
        new_balance = current_balance + amount
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Atualiza carteira
            cursor.execute("""
                UPDATE portfolio 
                SET balance = ?, total_deposited = total_deposited + ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT MAX(id) FROM portfolio)
            """, (new_balance, amount))
            
            # Regista movimento
            cursor.execute("""
                INSERT INTO portfolio_movements 
                (type, amount, description, balance_before, balance_after)
                VALUES ('DEPOSIT', ?, ?, ?, ?)
            """, (amount, description, current_balance, new_balance))
    
    def withdraw_funds(self, amount: float, description: str = "Levantamento"):
        """Remove fundos da carteira"""
        current_balance = self.get_portfolio_balance()
        
        if amount > current_balance:
            raise ValueError("Fundos insuficientes")
        
        new_balance = current_balance - amount
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Atualiza carteira
            cursor.execute("""
                UPDATE portfolio 
                SET balance = ?, total_withdrawn = total_withdrawn + ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT MAX(id) FROM portfolio)
            """, (new_balance, amount))
            
            # Regista movimento
            cursor.execute("""
                INSERT INTO portfolio_movements 
                (type, amount, description, balance_before, balance_after)
                VALUES ('WITHDRAWAL', ?, ?, ?, ?)
            """, (amount, description, current_balance, new_balance))
    
    def get_portfolio_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas da carteira"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Estatísticas gerais
            cursor.execute("""
                SELECT balance, total_deposited, total_withdrawn, created_at
                FROM portfolio 
                ORDER BY id DESC LIMIT 1
            """)
            portfolio = cursor.fetchone()
            
            if not portfolio:
                return {
                    'balance': 100000.0,
                    'total_deposited': 100000.0,
                    'total_withdrawn': 0.0,
                    'total_pnl': 0.0,
                    'total_trades': 0,
                    'open_trades': 0,
                    'win_rate': 0.0
                }
            
            # Estatísticas de trading
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_trades,
                    COUNT(CASE WHEN status = 'CLOSED' AND pnl > 0 THEN 1 END) as winning_trades,
                    COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_trades,
                    COALESCE(SUM(pnl), 0) as total_pnl
                FROM trades
            """)
            trade_stats = cursor.fetchone()
            
            win_rate = 0.0
            if trade_stats['closed_trades'] > 0:
                win_rate = (trade_stats['winning_trades'] / trade_stats['closed_trades']) * 100
            
            return {
                'balance': float(portfolio['balance']),
                'total_deposited': float(portfolio['total_deposited']),
                'total_withdrawn': float(portfolio['total_withdrawn']),
                'total_pnl': float(trade_stats['total_pnl']),
                'total_trades': trade_stats['total_trades'],
                'open_trades': trade_stats['open_trades'],
                'closed_trades': trade_stats['closed_trades'],
                'win_rate': round(win_rate, 2),
                'created_at': portfolio['created_at']
            }
    
    # === Métodos para Trades ===
    def save_trade(self, trade_data: Dict[str, Any]) -> int:
        """Guarda um novo trade"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trades 
                (symbol, side, quantity, entry_price, justification, strategy)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                trade_data['symbol'],
                trade_data['side'],
                trade_data['quantity'],
                trade_data['entry_price'],
                trade_data.get('justification', ''),
                trade_data.get('strategy', 'manual')
            ))
            
            return cursor.lastrowid
    
    def close_trade(self, trade_id: int, exit_price: float, justification: str = ""):
        """Fecha um trade existente"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Obtém dados do trade
            cursor.execute("""
                SELECT symbol, side, quantity, entry_price 
                FROM trades WHERE id = ? AND status = 'OPEN'
            """, (trade_id,))
            
            trade = cursor.fetchone()
            if not trade:
                raise ValueError(f"Trade {trade_id} não encontrado ou já fechado")
            
            # Calcula P&L
            if trade['side'] == 'BUY':
                pnl = (exit_price - trade['entry_price']) * trade['quantity']
            else:  # SELL
                pnl = (trade['entry_price'] - exit_price) * trade['quantity']
            
            pnl_percentage = (pnl / (trade['entry_price'] * trade['quantity'])) * 100
            
            # Atualiza trade
            cursor.execute("""
                UPDATE trades SET 
                    exit_price = ?,
                    exit_time = CURRENT_TIMESTAMP,
                    status = 'CLOSED',
                    pnl = ?,
                    pnl_percentage = ?,
                    justification = CASE 
                        WHEN justification = '' THEN ?
                        ELSE justification || ' | ' || ?
                    END
                WHERE id = ?
            """, (exit_price, pnl, pnl_percentage, justification, justification, trade_id))
            
            # Atualiza saldo da carteira
            current_balance = self.get_portfolio_balance()
            new_balance = current_balance + pnl
            self.update_portfolio_balance(
                new_balance, 
                f"Fecho de trade {trade['symbol']} - P&L: €{pnl:.2f}"
            )
            
            return pnl
    
    def get_open_trades(self) -> List[Dict[str, Any]]:
        """Obtém todos os trades abertos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trades 
                WHERE status = 'OPEN'
                ORDER BY entry_time DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtém histórico de trades"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trades 
                ORDER BY entry_time DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # === Métodos para Settings ===
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Obtém uma configuração"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row['value'])
                except json.JSONDecodeError:
                    return row['value']
            
            return default
    
    def set_setting(self, key: str, value: Any):
        """Define uma configuração"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Converte para JSON se necessário
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value_str))
    
    # === Métodos para Logs ===
    def add_log(self, level: str, message: str, module: str = "", extra_data: Dict = None):
        """Adiciona entrada ao log do sistema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_logs (level, message, module, extra_data)
                VALUES (?, ?, ?, ?)
            """, (
                level.upper(),
                message,
                module,
                json.dumps(extra_data) if extra_data else None
            ))
    
    def get_logs(self, level: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtém logs do sistema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if level:
                cursor.execute("""
                    SELECT * FROM system_logs 
                    WHERE level = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (level.upper(), limit))
            else:
                cursor.execute("""
                    SELECT * FROM system_logs 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]


# Instância global
db_manager = DatabaseManager()