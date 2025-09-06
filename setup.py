#!/usr/bin/env python3
"""
Script para criar automaticamente a estrutura de pastas e ficheiros do Trading Bot
Executa este script na pasta raiz do teu projeto para gerar toda a estrutura
"""

import os

def create_directory_structure():
    """Cria toda a estrutura de pastas"""
    
    directories = [
        "core",
        "data_providers", 
        "web/static/css",
        "web/static/js", 
        "web/static/img",
        "web/templates",
        "strategies/default_strategies",
        "assets",
        "data/cache",
        "data/backups", 
        "logs",
        "tests",
        "utils",
        "docker",
        "docs"
    ]
    
    print("📁 Criando estrutura de pastas...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✓ {directory}/")

def create_init_files():
    """Cria ficheiros __init__.py"""
    
    init_dirs = [
        "core",
        "data_providers", 
        "web",
        "strategies",
        "tests",
        "utils"
    ]
    
    print("\n🐍 Criando ficheiros __init__.py...")
    for directory in init_dirs:
        init_file = os.path.join(directory, "__init__.py")
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(f'"""\nMódulo {directory} do Trading Bot\n"""\n')
        print(f"   ✓ {init_file}")

def create_asset_files():
    """Cria ficheiros de configuração de ativos"""
    
    assets = {
        "indices.txt": [
            "^GSPC,S&P 500",
            "^DJI,Dow Jones Industrial Average", 
            "^IXIC,NASDAQ Composite",
            "^RUT,Russell 2000",
            "^FTSE,FTSE 100",
            "^GDAXI,DAX",
            "^FCHI,CAC 40", 
            "^N225,Nikkei 225",
            "^HSI,Hang Seng Index",
            "^AXJO,ASX 200"
        ],
        "stocks.txt": [
            "AAPL,Apple Inc.",
            "MSFT,Microsoft Corporation",
            "GOOGL,Alphabet Inc.",
            "AMZN,Amazon.com Inc.", 
            "TSLA,Tesla Inc.",
            "META,Meta Platforms Inc.",
            "NVDA,NVIDIA Corporation",
            "BRK-B,Berkshire Hathaway",
            "JNJ,Johnson & Johnson",
            "V,Visa Inc."
        ],
        "commodities.txt": [
            "GC=F,Gold",
            "SI=F,Silver", 
            "CL=F,Crude Oil WTI",
            "BZ=F,Brent Crude Oil",
            "NG=F,Natural Gas",
            "HG=F,Copper",
            "PL=F,Platinum",
            "PA=F,Palladium", 
            "ZC=F,Corn",
            "ZS=F,Soybeans"
        ],
        "crypto.txt": [
            "BTC-USD,Bitcoin",
            "ETH-USD,Ethereum",
            "BNB-USD,Binance Coin",
            "XRP-USD,XRP",
            "ADA-USD,Cardano",
            "SOL-USD,Solana", 
            "DOGE-USD,Dogecoin",
            "DOT-USD,Polkadot",
            "AVAX-USD,Avalanche",
            "MATIC-USD,Polygon"
        ]
    }
    
    print("\n💰 Criando ficheiros de ativos...")
    for filename, content in assets.items():
        filepath = os.path.join("assets", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(content) + "\n")
        print(f"   ✓ assets/{filename}")

def create_core_files():
    """Cria ficheiros principais vazios"""
    
    files = [
        "app.py",
        "run.py", 
        "config.py",
        "requirements.txt",
        "core/database.py",
        "core/api_manager.py",
        "core/portfolio.py", 
        "core/trading_engine.py",
        "core/risk_manager.py",
        "core/sentiment_analyzer.py",
        "data_providers/base_provider.py",
        "data_providers/finnhub_provider.py",
        "data_providers/twelvedata_provider.py",
        "data_providers/alpha_vantage_provider.py", 
        "data_providers/news_provider.py",
        "web/app.py",
        "web/routes.py",
        "strategies/base_strategy.py",
        "strategies/technical_indicators.py",
        "strategies/pine_script_parser.py",
        "utils/logger.py",
        "utils/validators.py", 
        "utils/formatters.py",
        "utils/helpers.py"
    ]
    
    print("\n📄 Criando ficheiros principais...")
    for filepath in files:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f'"""\n{os.path.basename(filepath)} - Trading Bot\nTODO: Implementar\n"""\n')
        print(f"   ✓ {filepath}")

def create_web_files():
    """Cria ficheiros da interface web"""
    
    web_files = {
        "web/templates/base.html": "<!-- Template base HTML -->",
        "web/templates/dashboard.html": "<!-- Dashboard principal -->", 
        "web/templates/portfolio.html": "<!-- Gestão de carteira -->",
        "web/templates/settings.html": "<!-- Configurações -->",
        "web/templates/charts.html": "<!-- Gráficos -->",
        "web/static/css/style.css": "/* CSS principal */",
        "web/static/js/main.js": "// JavaScript principal",
        "web/static/js/charts.js": "// Gráficos JavaScript", 
        "web/static/js/portfolio.js": "// Gestão carteira JavaScript"
    }
    
    print("\n🌐 Criando ficheiros web...")
    for filepath, content in web_files.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        print(f"   ✓ {filepath}")

def create_docker_files():
    """Cria ficheiros Docker"""
    
    dockerfile_content = """# Dockerfile para Trading Bot
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "run.py"]
"""

    compose_content = """version: '3.8'
services:
  trading-bot:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
"""
    
    print("\n🐳 Criando ficheiros Docker...")
    
    with open("docker/Dockerfile", "w", encoding="utf-8") as f:
        f.write(dockerfile_content)
    print("   ✓ docker/Dockerfile")
    
    with open("docker/docker-compose.yml", "w", encoding="utf-8") as f:
        f.write(compose_content)
    print("   ✓ docker/docker-compose.yml")

def create_readme():
    """Cria ficheiro README principal"""
    
    readme_content = """# Trading Bot Autónomo 🤖📈

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
"""
    
    print("\n📖 Criando README...")
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("   ✓ README.md")

def main():
    """Função principal"""
    print("🚀 TRADING BOT - SETUP AUTOMÁTICO")
    print("=" * 40)
    
    create_directory_structure()
    create_init_files()
    create_asset_files()
    create_core_files()
    create_web_files() 
    create_docker_files()
    create_readme()
    
    print("\n" + "=" * 40)
    print("✅ ESTRUTURA CRIADA COM SUCESSO!")
    print("\n📋 Próximos passos:")
    print("   1. cd no directório do projeto")
    print("   2. pip install -r requirements.txt")
    print("   3. Edita config.py com as tuas API keys")
    print("   4. python run.py")
    print("\n🎯 Estrutura completa criada para o teu Trading Bot!")

if __name__ == "__main__":
    main()