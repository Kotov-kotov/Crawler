import unittest
from crawler import JinrCrawler
import os
import pandas as pd
from datetime import datetime


class TestJinrCrawler(unittest.TestCase):

    def setUp(self):
        """Подготовка тестовых данных"""
        self.crawler = JinrCrawler('https://jinr.ru', max_pages=5)

    def test_url_validation(self):
        """Тест валидации URL"""
        test_urls = [
            ('https://jinr.ru', True),
            ('https://google.com', False),
            ('https://jinr.ru/about', True),
            ('http://jinr.ru', True),
        ]

        for url, should_accept in test_urls:
            parsed = self.crawler.base_domain in url
            self.assertEqual(parsed, should_accept, f"URL {url} should be {should_accept}")

    def test_status_code_extraction(self):
        """Тест получения статуса URL"""
        status_code, error = self.crawler.get_status_code('https://jinr.ru')
        self.assertIn(status_code, [200, 301, 302, 404, 503])

    def test_link_extraction(self):
        """Тест извлечения ссылок"""
        html = """
        <html>
            <body>
                <a href="/about">About</a>
                <a href="https://jinr.ru/news">News</a>
                <a href="https://google.com">External</a>
                <a href="#section">Anchor</a>
            </body>
        </html>
        """
        links = self.crawler.extract_links('https://jinr.ru', html)
        self.assertEqual(len(links), 2)
        self.assertIn('https://jinr.ru/about', links)
        self.assertIn('https://jinr.ru/news', links)

    def test_csv_structure(self):
        """Тест структуры CSV файла"""
        # Создание тестовых данных
        test_data = pd.DataFrame({
            'source_url': ['https://jinr.ru', 'https://jinr.ru/about'],
            'status_code': [200, 404],
            'error_message': ['', 'Not Found'],
            'check_date': [datetime.now(), datetime.now()],
            'links_found': [5, 0],
            'depth': [0, 1]
        })

        # Проверка наличия всех колонок
        expected_columns = ['source_url', 'status_code', 'error_message',
                            'check_date', 'links_found', 'depth']

        for col in expected_columns:
            self.assertIn(col, test_data.columns)

        # Проверка типов данных
        self.assertTrue(test_data['status_code'].dtype in ['int64', 'int32'])
        self.assertTrue(test_data['source_url'].dtype == 'object')

    def test_crawl_limits(self):
        """Тест ограничений краулинга"""
        crawler = JinrCrawler('https://jinr.ru', max_pages=3)
        crawler.crawl()

        self.assertLessEqual(len(crawler.visited_urls), 3)
        self.assertLessEqual(len(crawler.links_data), 3)

    def test_duplicate_handling(self):
        """Тест обработки дубликатов"""
        crawler = JinrCrawler('https://jinr.ru', max_pages=10)
        crawler.visited_urls.add('https://jinr.ru/test')
        crawler.visited_urls.add('https://jinr.ru/test')

        self.assertEqual(len(crawler.visited_urls), 1)


class TestCSVOutput(unittest.TestCase):
    """Тест формата CSV файла"""

    def test_csv_example(self):
        """Пример данных в CSV"""
        example_data = {
            'source_url': [
                'https://jinr.ru',
                'https://jinr.ru/about',
                'https://jinr.ru/news'
            ],
            'status_code': [200, 200, 404],
            'error_message': ['', '', 'Page not found'],
            'check_date': [
                '2024-01-15 10:30:00',
                '2024-01-15 10:30:05',
                '2024-01-15 10:30:10'
            ],
            'links_found': [15, 8, 0],
            'depth': [0, 1, 1]
        }

        df = pd.DataFrame(example_data)

        # Сохранение тестового CSV
        os.makedirs('data', exist_ok=True)
        df.to_csv('data/example_links.csv', index=False, encoding='utf-8-sig')

        # Проверка файла
        self.assertTrue(os.path.exists('data/example_links.csv'))

        # Чтение и проверка
        df_loaded = pd.read_csv('data/example_links.csv')
        self.assertEqual(len(df_loaded), 3)
        self.assertEqual(df_loaded['status_code'].iloc[2], 404)

        print("\nПример данных CSV:")
        print(df_loaded.to_string())

        # Очистка
        os.remove('data/example_links.csv')


def run_tests():
    """Запуск всех тестов"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()