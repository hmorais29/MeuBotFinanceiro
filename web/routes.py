@app.route('/api-status')
def api_status_page():
    return render_template('api_status.html')

@app.route('/news')
def news_dashboard():
    return render_template('news_dashboard.html')

@app.route('/api/news/<symbol>')
def get_news(symbol):
    news = api_manager.get_news(symbol, 10)
    return jsonify({'news': news})
