import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
from datetime import datetime
import time
import logging
from typing import Set, Dict, List, Tuple
from collections import deque
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WebCrawler:
    def __init__(self, start_url: str, max_pages: int = 100, delay: float = 1.0,
                 same_domain_only: bool = True):
        """
        Инициализация веб-краулера

        Args:
            start_url: Начальный URL для обхода
            max_pages: Максимальное количество страниц для проверки
            delay: Задержка между запросами в секундах
            same_domain_only: Ограничиваться ли только тем же доменом
        """
        self.start_url = start_url
        self.base_domain = urlparse(start_url).netloc
        self.max_pages = max_pages
        self.delay = delay
        self.same_domain_only = same_domain_only

        # Множества для отслеживания посещенных и запланированных URL
        self.visited_urls: Set[str] = set()  # Уже обработанные URL
        self.queued_urls: Set[str] = set()  # URL уже в очереди
        self.queue = deque()  # Очередь для обхода

        self.links_data: List[Dict] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def normalize_url(self, url: str) -> str:
        """
        Нормализация URL для сравнения
        Удаляет якоря, параметры, приводит к единому формату
        """
        if not url:
            return url

        parsed = urlparse(url)

        # Удаляем якорь
        url_without_fragment = parsed._replace(fragment='')

        # Удаляем параметры (обычно после ? или ;)
        url_without_params = url_without_fragment._replace(query='', params='')

        # Нормализуем путь
        path = url_without_params.path
        # Убираем слеш в конце, если это не корень
        if path != '/' and path.endswith('/'):
            path = path[:-1]
        # Добавляем слеш в начало, если путь пустой
        if not path:
            path = '/'

        normalized = url_without_params._replace(path=path)

        # Приводим к нижнему регистру для сравнения (кроме схемы)
        normalized_str = f"{normalized.scheme}://{normalized.netloc.lower()}{normalized.path}"

        return normalized_str

    def is_valid_url(self, url: str) -> Tuple[bool, str]:
        """
        Проверка, должен ли URL быть обработан
        Возвращает (должен_ли_обрабатывать, причина_пропуска)
        """
        if not url:
            return False, "Пустой URL"

        parsed = urlparse(url)

        # Проверка схемы
        if parsed.scheme not in ['http', 'https']:
            return False, f"Неверная схема: {parsed.scheme}"

        # Проверка домена
        if self.same_domain_only:
            if self.base_domain not in parsed.netloc:
                return False, f"Внешний домен: {parsed.netloc}"

        # Исключаем определенные расширения файлов
        excluded_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp',
                               '.zip', '.rar', '.7z', '.doc', '.docx', '.xls',
                               '.xlsx', '.ppt', '.pptx', '.mp3', '.mp4', '.avi',
                               '.mov', '.wmv', '.iso', '.tar', '.gz', '.exe', '.msi']

        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in excluded_extensions):
            return False, f"Исключенный тип файла"

        # Исключаем специальные URL
        excluded_patterns = [
            r'logout', r'signout', r'delete', r'remove',
            r'javascript:', r'mailto:', r'tel:', r'sms:',
            r'#', r'\?action=delete', r'\?do=delete'
        ]

        url_lower = url.lower()
        if any(re.search(pattern, url_lower) for pattern in excluded_patterns):
            return False, "Специальный URL"

        return True, "OK"

    def get_status_code(self, url: str) -> Tuple[int, str]:
        """Получение статуса URL"""
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            return response.status_code, 'success'
        except requests.exceptions.Timeout:
            return 408, 'timeout'
        except requests.exceptions.ConnectionError:
            return 503, 'connection_error'
        except requests.exceptions.TooManyRedirects:
            return 310, 'too_many_redirects'
        except Exception as e:
            return 500, f'error: {str(e)[:50]}'

    def extract_links(self, url: str, html: str) -> Set[str]:
        """Извлечение ссылок из HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()

        # Ищем все теги a с href
        for tag in soup.find_all('a', href=True):
            href = tag.get('href', '').strip()
            if not href:
                continue

            # Преобразуем относительную ссылку в абсолютную
            full_url = urljoin(url, href)

            # Нормализуем URL
            normalized_url = self.normalize_url(full_url)

            # Проверяем, должен ли URL быть обработан
            is_valid, reason = self.is_valid_url(normalized_url)
            if is_valid:
                links.add(normalized_url)
            else:
                logger.debug(f"Пропущена ссылка {normalized_url}: {reason}")

        return links

    def calculate_depth(self, url: str) -> int:
        """Расчет глубины ссылки от start_url"""
        if url == self.start_url:
            return 0

        # Получаем пути
        start_path = urlparse(self.start_url).path
        current_path = urlparse(url).path

        # Убираем слеши в начале и конце
        start_path = start_path.strip('/')
        current_path = current_path.strip('/')

        if not current_path:
            return 1

        # Считаем количество сегментов пути
        start_segments = len([s for s in start_path.split('/') if s]) if start_path else 0
        current_segments = len([s for s in current_path.split('/') if s])

        depth = max(0, current_segments - start_segments)
        return min(depth, 20)  # Ограничиваем максимальную глубину

    def add_to_queue(self, url: str):
        """Безопасное добавление URL в очередь"""
        normalized_url = self.normalize_url(url)

        # Проверка на дубликаты
        if normalized_url in self.visited_urls:
            logger.debug(f"URL уже обработан: {normalized_url}")
            return False

        if normalized_url in self.queued_urls:
            logger.debug(f"URL уже в очереди: {normalized_url}")
            return False

        # Проверка лимитов
        if len(self.visited_urls) + len(self.queued_urls) >= self.max_pages * 2:
            logger.warning("Достигнут лимит URL в очереди")
            return False

        # Добавляем в очередь
        self.queue.append(normalized_url)
        self.queued_urls.add(normalized_url)
        logger.debug(f"Добавлен в очередь: {normalized_url}")
        return True

    def crawl(self):
        """Основной метод краулинга с защитой от бесконечной рекурсии"""
        # Добавляем стартовый URL в очередь
        self.add_to_queue(self.start_url)

        processed_count = 0
        max_retries = 3

        while self.queue and processed_count < self.max_pages:
            url = self.queue.popleft()

            # Убираем из множества запланированных
            self.queued_urls.discard(url)

            # Пропускаем, если уже обработан (на всякий случай)
            if url in self.visited_urls:
                logger.debug(f"Пропускаем уже обработанный URL: {url}")
                continue

            logger.info(f"Обработка [{processed_count + 1}/{self.max_pages}]: {url}")
            logger.info(f"Очередь: {len(self.queue)} URL, Посещено: {len(self.visited_urls)}")

            # Получение статуса и содержимого
            status_code = None
            error_msg = ''
            links = set()

            # Попытки загрузки с повторными попытками
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, timeout=10, allow_redirects=True)
                    status_code = response.status_code

                    # Если страница загружена успешно, извлекаем ссылки
                    if status_code == 200:
                        links = self.extract_links(url, response.text)
                        logger.info(
                            f"Найдено ссылок: {len(links)} (уникальных: {len([l for l in links if l not in self.visited_urls and l not in self.queued_urls])})")

                        # Добавляем новые ссылки в очередь
                        new_links_count = 0
                        for link in links:
                            if self.add_to_queue(link):
                                new_links_count += 1
                        logger.info(f"Добавлено новых ссылок в очередь: {new_links_count}")

                    break  # Успешно загрузили, выходим из цикла попыток

                except requests.exceptions.Timeout:
                    if attempt == max_retries - 1:
                        status_code = 408
                        error_msg = 'timeout'
                        logger.warning(f"Таймаут после {max_retries} попыток: {url}")
                    else:
                        logger.debug(f"Повторная попытка {attempt + 1} для {url}")
                        time.sleep(2)

                except requests.exceptions.ConnectionError:
                    if attempt == max_retries - 1:
                        status_code = 503
                        error_msg = 'connection_error'
                        logger.warning(f"Ошибка соединения: {url}")
                    else:
                        time.sleep(2)

                except Exception as e:
                    if attempt == max_retries - 1:
                        status_code = 500
                        error_msg = f'error: {str(e)[:50]}'
                        logger.error(f"Ошибка при обработке {url}: {e}")
                    else:
                        time.sleep(2)

            # Сохранение данных
            self.links_data.append({
                'source_url': url,
                'status_code': status_code if status_code else 0,
                'error_message': error_msg,
                'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'links_found': len(links),
                'depth': self.calculate_depth(url)
            })

            # Отмечаем URL как обработанный
            self.visited_urls.add(url)
            processed_count += 1

            # Сохраняем промежуточные результаты каждые 10 страниц
            if len(self.links_data) % 10 == 0:
                self.save_to_csv('data/links_data_temp.csv')
                logger.info(f"💾 Сохранен промежуточный результат ({len(self.links_data)} страниц)")

            # Вежливый краулинг
            time.sleep(self.delay)

        # Итоговая статистика
        logger.info(f"\n{'=' * 60}")
        logger.info(f"КРАУЛИНГ ЗАВЕРШЕН")
        logger.info(f"{'=' * 60}")
        logger.info(f"✅ Обработано страниц: {len(self.links_data)}")
        logger.info(f"📊 Уникальных URL в очереди: {len(self.visited_urls)}")
        logger.info(f"🔗 Всего найдено ссылок: {sum(item['links_found'] for item in self.links_data)}")
        logger.info(f"⏭️  Осталось в очереди: {len(self.queue)}")

    def save_to_csv(self, filename: str = 'data/links_data.csv'):
        """Сохранение данных в CSV"""
        if not self.links_data:
            logger.warning("Нет данных для сохранения")
            return None

        df = pd.DataFrame(self.links_data)

        # Сортируем по глубине и статусу
        df = df.sort_values(['depth', 'status_code'], ascending=[True, True])

        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"💾 Данные сохранены в {filename} (всего записей: {len(df)})")

        # Дополнительная статистика
        stats_file = filename.replace('.csv', '_stats.txt')
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write(f"Статистика краулера\n")
            f.write(f"{'=' * 60}\n")
            f.write(f"Начальный URL: {self.start_url}\n")
            f.write(f"Домен: {self.base_domain}\n")
            f.write(f"Всего страниц: {len(df)}\n")
            f.write(f"Успешных (200): {len(df[df['status_code'] == 200])}\n")
            f.write(f"Не найдено (404): {len(df[df['status_code'] == 404])}\n")
            f.write(f"Ошибок сервера: {len(df[df['status_code'] >= 500])}\n")
            f.write(f"Таймаутов: {len(df[df['status_code'] == 408])}\n")
            f.write(f"Средняя глубина: {df['depth'].mean():.2f}\n")
            f.write(f"Максимальная глубина: {df['depth'].max()}\n")

        return df