# Trading Bot Autónomo 🤖📈

Bot de trading 100% autónomo para análise técnica e sentimento de mercado.

## 🚀 Funcionalidades

- Carteira virtual com €100,000 iniciais
- Análise técnica com Pine Script
- Análise de sentimento (notícias, redes sociais)
- Interface web moderna
- Gestão de risco automática
- Múltiplos ativos: índices, ações, commodities, crypto

## 🛠 Instalação

```bash
pip install -r requirements.txt
python run.py
```

## 📊 APIs Suportadas

- Finnhub
- Twelve Data  
- Alpha Vantage
- NewsAPI
- Reddit
- Twitter

## 🏗 Estrutura

```
trading_bot/
├── core/           # Módulos principais
├── data_providers/ # APIs de dados
├── web/            # Interface web
├── strategies/     # Estratégias de trading
├── assets/         # Configuração de ativos
└── data/           # Base de dados e cache
```

## 📝 Configuração

1. Adiciona as tuas API keys em `config.py`
2. Edita os ativos em `assets/*.txt`
3. Executa `python run.py`

## 🎯 Roadmap

- [x] Estrutura base
- [ ] Base de dados
- [ ] APIs de mercado
- [ ] Interface web
- [ ] Trading simulado
- [ ] Estratégias técnicas
- [ ] Análise sentimento
- [ ] Autonomia completa

---
Developed with ❤️ for autonomous trading
