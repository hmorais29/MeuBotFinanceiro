"""
Gestor da Carteira Virtual
Gere saldo, operações e estatísticas da carteira
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from core.database import db_manager
from core.api_manager import api_manager


class PortfolioManager:
    def __init__(self):
        self.currency = "EUR"  # Moeda padrão
        self.max_trades_per_day = 5
        self.max_open_trades = 1
        self.stop_loss_percentage = 5.0  # 5%
        self.take_profit_percentage = 5.0  # 5%
        self.daily_profit_target = 5.0  # 5% - para automaticamente parar trading
    
    def get_balance(self) -> float:
        """Obtém saldo atual da carteira"""
        return db_manager.get_portfolio_balance()
    
    def deposit(self, amount: float, description: str = "Depósito manual") -> bool:
        """Adiciona fundos à carteira"""
        try:
            if amount <= 0:
                raise ValueError("Valor deve ser positivo")
            
            db_manager.deposit_funds(amount, description)
            
            # Log da operação
            db_manager.add_log(
                'INFO', 
                f'Depósito de €{amount:.2f} realizado',
                'portfolio',
                {'amount': amount, 'description': description}
            )
            
            return True
            
        except Exception as e:
            db_manager.add_log('ERROR', f'Erro ao depositar: {e}', 'portfolio')
            return False
    
    def withdraw(self, amount: float, description: str = "Levantamento manual") -> bool:
        """Remove fundos da carteira"""
        try:
            if amount <= 0:
                raise ValueError("Valor deve ser positivo")
            
            current_balance = self.get_balance()
            if amount > current_balance:
                raise ValueError(f"Fundos insuficientes. Saldo: €{current_balance:.2f}")
            
            db_manager.withdraw_funds(amount, description)
            
            # Log da operação
            db_manager.add_log(
                'INFO', 
                f'Levantamento de €{amount:.2f} realizado',
                'portfolio',
                {'amount': amount, 'description': description}
            )
            
            return True
            
        except Exception as e:
            db_manager.add_log('ERROR', f'Erro ao levantar: {e}', 'portfolio')
            return False
    
    def can_trade(self) -> Dict[str, Any]:
        """Verifica se pode fazer trading baseado nas regras"""
        # Obtém estatísticas do dia
        today_trades = self._get_today_trades()
        open_trades = db_manager.get_open_trades()
        today_profit = self._get_today_profit()
        
        can_trade = True
        reasons = []
        
        # Verifica limite de trades por dia
        if len(today_trades) >= self.max_trades_per_day:
            can_trade = False
            reasons.append(f"Limite diário de {self.max_trades_per_day} trades atingido")
        
        # Verifica limite de trades abertos
        if len(open_trades) >= self.max_open_trades:
            can_trade = False
            reasons.append(f"Máximo de {self.max_open_trades} trade(s) aberto(s)")
        
        # Verifica se atingiu target de lucro diário
        if today_profit >= self.daily_profit_target:
            can_trade = False
            reasons.append(f"Target de lucro diário ({self.daily_profit_target}%) atingido")
        
        return {
            'can_trade': can_trade,
            'reasons': reasons,
            'today_trades': len(today_trades),
            'open_trades': len(open_trades),
            'today_profit_percentage': today_profit
        }
    
    def execute_trade(self, symbol: str, side: str, amount: float, 
                     justification: str = "", strategy: str = "manual") -> Optional[int]:
        """
        Executa um trade virtual
        
        Args:
            symbol: Símbolo do instrumento (ex: AAPL)
            side: BUY ou SELL
            amount: Valor em euros a investir
            justification: Justificação para o trade
            strategy: Nome da estratégia utilizada
            
        Returns:
            ID do trade se sucesso, None se erro
        """
        try:
            # Verifica se pode fazer trading
            can_trade_check = self.can_trade()
            if not can_trade_check['can_trade']:
                raise ValueError(f"Não é possível fazer trading: {'; '.join(can_trade_check['reasons'])}")
            
            # Verifica saldo
            current_balance = self.get_balance()
            if amount > current_balance:
                raise ValueError(f"Fundos insuficientes. Saldo: €{current_balance:.2f}")
            
            # Obtém preço atual
            current_price = api_manager.get_current_price(symbol)
            if current_price is None:
                raise ValueError(f"Não foi possível obter preço de {symbol}")
            
            # Calcula quantidade
            quantity = amount / current_price
            
            # Dados do trade
            trade_data = {
                'symbol': symbol,
                'side': side.upper(),
                'quantity': quantity,
                'entry_price': current_price,
                'justification': justification or f"Trade {side} de {symbol}",
                'strategy': strategy
            }
            
            # Guarda trade na base de dados
            trade_id = db_manager.save_trade(trade_data)
            
            # Atualiza saldo (deduz valor investido)
            new_balance = current_balance - amount
            db_manager.update_portfolio_balance(
                new_balance,
                f"Trade {side} {symbol} - Investimento: €{amount:.2f}"
            )
            
            # Log da operação
            db_manager.add_log(
                'INFO',
                f'Trade executado: {side} {symbol} por €{amount:.2f} a €{current_price:.4f}',
                'portfolio',
                {
                    'trade_id': trade_id,
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': current_price,
                    'quantity': quantity
                }
            )
            
            return trade_id
            
        except Exception as e:
            db_manager.add_log('ERROR', f'Erro ao executar trade: {e}', 'portfolio')
            return None
    
    def close_trade(self, trade_id: int, justification: str = "") -> bool:
        """Fecha um trade aberto"""
        try:
            open_trades = db_manager.get_open_trades()
            trade = next((t for t in open_trades if t['id'] == trade_id), None)
            
            if not trade:
                raise ValueError(f"Trade {trade_id} não encontrado ou já fechado")
            
            # Obtém preço atual
            current_price = api_manager.get_current_price(trade['symbol'])
            if current_price is None:
                raise ValueError(f"Não foi possível obter preço de {trade['symbol']}")
            
            # Fecha trade na base de dados (já atualiza saldo automaticamente)
            pnl = db_manager.close_trade(trade_id, current_price, justification)
            
            # Log da operação
            db_manager.add_log(
                'INFO',
                f'Trade fechado: {trade["symbol"]} - P&L: €{pnl:.2f}',
                'portfolio',
                {
                    'trade_id': trade_id,
                    'symbol': trade['symbol'],
                    'exit_price': current_price,
                    'pnl': pnl
                }
            )
            
            return True
            
        except Exception as e:
            db_manager.add_log('ERROR', f'Erro ao fechar trade: {e}', 'portfolio')
            return False
    
    def get_portfolio_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas completas da carteira"""
        basic_stats = db_manager.get_portfolio_stats()
        
        # Adiciona estatísticas extra
        open_trades = db_manager.get_open_trades()
        today_trades = self._get_today_trades()
        today_profit = self._get_today_profit()
        can_trade_info = self.can_trade()
        
        # Calcula valor das posições abertas
        open_positions_value = 0.0
        for trade in open_trades:
            current_price = api_manager.get_current_price(trade['symbol'])
            if current_price:
                position_value = trade['quantity'] * current_price
                open_positions_value += position_value
        
        return {
            # Dados básicos da carteira
            'balance': basic_stats['balance'],
            'total_deposited': basic_stats['total_deposited'],
            'total_withdrawn': basic_stats['total_withdrawn'],
            'currency': self.currency,  # Adiciona moeda padrão
            
            # Estatísticas de trading
            'total_pnl': basic_stats['total_pnl'],
            'total_trades': basic_stats['total_trades'],
            'open_trades': basic_stats['open_trades'],
            'closed_trades': basic_stats['closed_trades'],
            'win_rate': basic_stats['win_rate'],
            
            # Estatísticas do dia
            'today_trades': len(today_trades),
            'today_profit_percentage': today_profit,
            
            # Posições abertas
            'open_positions_value': open_positions_value,
            'open_positions': open_trades,
            
            # Estado do trading
            'can_trade': can_trade_info['can_trade'],
            'trading_restrictions': can_trade_info['reasons'],
            
            # Configurações
            'max_trades_per_day': self.max_trades_per_day,
            'max_open_trades': self.max_open_trades,
            'daily_profit_target': self.daily_profit_target,
            
            # Metadados
            'created_at': basic_stats.get('created_at', ''),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_trade_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtém histórico de trades"""
        return db_manager.get_trade_history(limit)
    
    def get_open_trades(self) -> List[Dict[str, Any]]:
        """Obtém trades abertos"""
        return db_manager.get_open_trades()
    
    def _get_today_trades(self) -> List[Dict[str, Any]]:
        """Obtém trades de hoje"""
        # Por simplicidade, vamos obter todos os trades recentes
        # Em produção, faria uma query específica para hoje
        all_trades = db_manager.get_trade_history(50)
        today = datetime.now().date()
        
        today_trades = []
        for trade in all_trades:
            # Parse da data de entrada
            try:
                trade_date = datetime.fromisoformat(trade['entry_time'].replace('Z', '+00:00')).date()
                if trade_date == today:
                    today_trades.append(trade)
            except:
                # Se não conseguir fazer parse, assume que é de hoje
                today_trades.append(trade)
        
        return today_trades
    
    def _get_today_profit(self) -> float:
        """Calcula lucro percentual de hoje"""
        today_trades = self._get_today_trades()
        
        if not today_trades:
            return 0.0
        
        total_pnl = sum(trade.get('pnl', 0) for trade in today_trades if trade['status'] == 'CLOSED')
        initial_balance = self.get_balance() - total_pnl  # Aproximação
        
        if initial_balance <= 0:
            return 0.0
        
        return (total_pnl / initial_balance) * 100
    
    def update_settings(self, settings: Dict[str, Any]):
        """Atualiza configurações do portfolio"""
        if 'max_trades_per_day' in settings:
            self.max_trades_per_day = int(settings['max_trades_per_day'])
        
        if 'max_open_trades' in settings:
            self.max_open_trades = int(settings['max_open_trades'])
        
        if 'daily_profit_target' in settings:
            self.daily_profit_target = float(settings['daily_profit_target'])
        
        if 'stop_loss_percentage' in settings:
            self.stop_loss_percentage = float(settings['stop_loss_percentage'])
        
        if 'take_profit_percentage' in settings:
            self.take_profit_percentage = float(settings['take_profit_percentage'])
        
        # Guarda configurações na base de dados
        db_manager.set_setting('portfolio_settings', {
            'max_trades_per_day': self.max_trades_per_day,
            'max_open_trades': self.max_open_trades,
            'daily_profit_target': self.daily_profit_target,
            'stop_loss_percentage': self.stop_loss_percentage,
            'take_profit_percentage': self.take_profit_percentage
        })


# Instância global
portfolio_manager = PortfolioManager()