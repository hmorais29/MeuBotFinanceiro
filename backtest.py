import pandas as pd

# Função para limpar preços (converter '875.93K' para float)
def clean_price(price_str):
    if isinstance(price_str, str):
        if 'K' in price_str:
            return float(price_str.replace('K', '')) * 1000
        return float(price_str)
    return price_str

# Classe para gerir posições
class Position:
    def __init__(self, entry_price, entry_date):
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.quantity = 0
        self.exit_price = None
        self.exit_date = None

    def close_position(self, exit_price, exit_date):
        self.exit_price = exit_price
        self.exit_date = exit_date
        return (exit_price - self.entry_price) * self.quantity

# Função de backtesting
def run_backtest(data):
    position = None
    for index, row in data.iterrows():
        if position is None and row['Mudança'] < -3.0:  # Condição de entrada (queda > 3%)
            position = Position(row['Preço'], row['Data'])
            position.quantity = 100  # Quantidade fictícia de unidades
            print(f"Entrada em {row['Data']} a {row['Preço']}")
        elif position and row['Mudança'] > 1.0:  # Condição de saída (subida > 1%)
            profit = position.close_position(row['Preço'], row['Data'])
            print(f"Saída em {row['Data']} a {row['Preço']} com lucro: {profit}")
            position = None
    if position:
        print("Erro: Posição aberta no final do backtest")

# Função para carregar e preparar os dados
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        df['Preço'] = df['Preço'].apply(clean_price)
        # Certifica-te de que 'Mudança' está em formato numérico
        df['Mudança'] = df['Mudança'].str.rstrip('%').astype('float') / 100.0
        return df
    except Exception as e:
        print(f"Erro ao carregar {file_path}: {e}")
        return None

# Exemplo de uso com os dados fornecidos manualmente
if __name__ == "__main__":
    # Dados manuais como exemplo (podes substituir por leitura de CSV)
    data = {
        'Data': ['2021-05-07', '2021-05-06', '2021-05-05', '2021-05-04', '2021-05-03',
                 '2021-04-30', '2021-04-29', '2021-04-28', '2021-04-27', '2021-04-26',
                 '2021-04-23', '2021-04-22', '2021-04-21', '2021-04-20', '2021-04-19',
                 '2021-04-16', '2021-04-15', '2021-04-14', '2021-04-13', '2021-04-12',
                 '2021-04-09', '2021-04-08', '2021-04-07', '2021-04-06', '2021-04-05',
                 '2021-04-01', '2021-03-26', '2021-03-25', '2021-03-24', '2021-03-23',
                 '2021-03-22', '2021-03-19', '2021-03-18', '2021-03-17', '2021-03-16',
                 '2021-03-15', '2021-03-12', '2021-03-11', '2021-03-10', '2021-03-09',
                 '2021-03-08', '2021-03-05', '2021-03-04', '2021-03-03', '2021-03-02',
                 '2021-03-01', '2021-02-26', '2021-02-25', '2021-02-24', '2021-02-23'],
        'Preço': [422.12, 419.07, 415.75, 415.62, 418.2, 417.3, 420.06, 417.4, 417.52,
                  417.61, 416.74, 412.27, 416.07, 412.17, 415.21, 417.26, 415.87, 411.45,
                  412.86, 411.64, 411.49, 408.52, 406.59, 406.12, 406.36, 400.61, 395.98,
                  389.7, 387.52, 389.5, 392.59, 389.48, 391.48, 397.26, 395.91, 396.41,
                  394.06, 393.53, 389.58, 387.17, 381.72, 383.63, 376.7, 381.42, 386.54,
                  389.58, 380.36, 382.33, 391.77, 387.5],
        'Mudança': [1.6470814871893742, 0.912637256790604, 0.1131766518975215,
                    0.081872471585444, 0.7031400500866923, 0.48641880177230756,
                    1.1510306299364357, 0.5104989404738982, 0.539395106915818,
                    0.5610672317472648, 0.35157002504335305, -0.7248121749181254,
                    0.19023309574263642, -0.7488923136197161, -0.016856097091117603,
                    0.47678674629166307, 0.14207281833944133, -0.922269312271235,
                    -0.5827393565786841, -0.8765170487381975, -0.9126372567905904,
                    -1.627817376228085, -2.092564053168946, -2.2057407050664537,
                    -2.147948372182614, -3.5325563475245523, 0.050533124463097046,
                    -1.536206983677797, -2.087018040325431, -1.5867401081408796,
                    -0.8060033351862141, -1.5917934205871835, -1.086462175956328,
                    0.3739451210268377, 0.03284653090101883, 0.15917934205873271,
                    -0.4345848703825283, -0.5684976502097124, -1.5665268583556495,
                    -2.1754510081358225, -3.5524786497549004, 0.0, -1.8064280687120422,
                    -0.5760759064723769, 0.7585433881604736, 1.5509735943487184,
                    -0.8523838073143346, -0.33886818027787485, 2.1218361442014406,
                    1.0087845059041276]
    }

    # Criar DataFrame
    df = pd.DataFrame(data)
    df['Data'] = pd.to_datetime(df['Data'])
    df = df.sort_values('Data')  # Ordenar por data

    # Executar backtest
    run_backtest(df)

    # Exemplo de leitura de CSV (descomenta e ajusta o caminho)
    # file_path = 'C:\\Users\\helde\\MeuBotFinanceiro\\MSFT.csv'
    # df_csv = load_data(file_path)
    # if df_csv is not None:
    #     run_backtest(df_csv)