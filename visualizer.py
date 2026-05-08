# visualizer_simple.py - упрощенная версия без графа
import pandas as pd


class GraphVisualizer:
    def __init__(self, csv_file: str):
        self.df = pd.read_csv(csv_file)

    def visualize(self, output_file: str = 'graphs/link_graph.html'):
        """Пропускаем визуализацию, так как это упрощенная версия"""
        print("Визуализация графа пропущена (упрощенная версия)")
        # Создаем простой HTML файл с информацией
        html_content = f"""
        <html>
        <head><title>Статистика краулера</title></head>
        <body>
            <h1>Результаты обхода сайта jinr.ru</h1>
            <h2>Статистика</h2>
            <p>Всего ссылок: {len(self.df)}</p>
            <p>Успешных (200): {len(self.df[self.df['status_code'] == 200])}</p>
            <p>Не найдено (404): {len(self.df[self.df['status_code'] == 404])}</p>
            <p>Ошибок сервера: {len(self.df[self.df['status_code'] >= 500])}</p>
            <h2>Посмотреть данные</h2>
            <p>CSV файл сохранен в data/links_data.csv</p>
        </body>
        </html>
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Статистика сохранена в {output_file}")

    def print_statistics(self):
        """Вывод статистики"""
        print("\n" + "=" * 50)
        print("СТАТИСТИКА ПО ССЫЛКАМ")
        print("=" * 50)
        print(f"Всего проверено ссылок: {len(self.df)}")
        print(f"Успешных (200): {len(self.df[self.df['status_code'] == 200])}")
        print(f"Не найдено (404): {len(self.df[self.df['status_code'] == 404])}")
        print(f"Ошибок сервера (5xx): {len(self.df[self.df['status_code'] >= 500])}")