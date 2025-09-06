#!/usr/bin/env python3
"""
Script para atualizar a estrutura da base de dados existente
"""

import sqlite3
import os

def fix_database():
    db_path = "data/trading_bot.db"
    
    print(f"🔧 A corrigir base de dados: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ Base de dados não encontrada!")
        return
    
    # Backup da DB atual
    backup_path = f"{db_path}.backup"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"💾 Backup criado: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica estrutura atual da tabela portfolio
        cursor.execute("PRAGMA table_info(portfolio)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Colunas atuais da portfolio: {columns}")
        
        # Adiciona colunas em falta
        if 'total_deposited' not in columns:
            print("➕ A adicionar coluna 'total_deposited'")
            cursor.execute("ALTER TABLE portfolio ADD COLUMN total_deposited REAL DEFAULT 100000.0")
        
        if 'total_withdrawn' not in columns:
            print("➕ A adicionar coluna 'total_withdrawn'")
            cursor.execute("ALTER TABLE portfolio ADD COLUMN total_withdrawn REAL DEFAULT 0.0")
        
        # Atualiza registos existentes
        cursor.execute("UPDATE portfolio SET total_deposited = 100000.0 WHERE total_deposited IS NULL")
        cursor.execute("UPDATE portfolio SET total_withdrawn = 0.0 WHERE total_withdrawn IS NULL")
        
        # Cria tabelas em falta se necessário
        
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
        
        # Tabela de configurações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de logs
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
        
        # Adiciona API keys padrão se não existirem
        cursor.execute("SELECT COUNT(*) FROM api_keys")
        if cursor.fetchone()[0] == 0:
            print("🔑 A adicionar API keys padrão")
            api_keys = [
                ('finnhub', 'd2mb0n9r01qq6fopqje0d2mb0n9r01qq6fopqjeg'),
                ('twelve_data', 'cd4c76b8401747faa066d1ee8a0ad97a'),
                ('alpha_vantage', 'YK3EAJ4G4DT1LEQ4'),
                ('newsapi', '141cfc70afd14c8ba34d71b0d85fbbdd')
            ]
            
            cursor.executemany("""
                INSERT INTO api_keys (provider, api_key) 
                VALUES (?, ?)
            """, api_keys)
        
        conn.commit()
        print("✅ Base de dados corrigida com sucesso!")
        
        # Verifica se funciona
        cursor.execute("SELECT * FROM portfolio LIMIT 1")
        portfolio = cursor.fetchone()
        print(f"📊 Portfolio atual: {portfolio}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()