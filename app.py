from flask import Flask, render_template, request
import asyncio
from backtest import run_backtest_async, suggest_portfolio

app = Flask(__name__)

# Configurar loop de eventos globalmente
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route('/', methods=['GET', 'POST'])
def index():
    tickers = ['MSFT', 'SPY', 'COMP', 'AAPL']  # Lista de tickers disponíveis
    result = ""
    portfolio = []
    if request.method == 'POST':
        ticker = request.form['ticker']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        capital = float(request.form.get('capital', 10000))
        take_profit = float(request.form.get('take_profit', 5))
        stop_loss = float(request.form.get('stop_loss', -3))
        # Usar o loop configurado
        result = loop.run_until_complete(run_backtest_async(ticker, start_date, end_date, capital, take_profit, stop_loss))
        portfolio = suggest_portfolio(capital)
    return render_template('index.html', result=result, portfolio=portfolio, tickers=tickers)

if __name__ == '__main__':
    app.run(debug=True)