import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque
import time
import os
import sys


class CrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jinr.ru Веб Краулер")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Переменные для хранения данных
        self.crawler_instance = None
        self.crawling_thread = None
        self.is_crawling = False

        # Настройка стиля
        self.setup_styles()

        # Создание интерфейса
        self.create_widgets()

    def setup_styles(self):
        """Настройка стилей интерфейса"""
        style = ttk.Style()
        style.theme_use('clam')

        # Настройка цветов
        self.bg_color = "#f0f0f0"
        self.root.configure(bg=self.bg_color)

    def create_widgets(self):
        """Создание всех виджетов интерфейса"""
        # Главный контейнер с прокруткой
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Настройка весов для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)

        # Заголовок
        title_label = ttk.Label(main_frame, text="Веб Краулер для Jinr.ru",
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))

        # Рамка с настройками
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки обхода", padding="10")
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)

        # Стартовый URL
        ttk.Label(settings_frame, text="Стартовый URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.start_url_var = tk.StringVar(value="https://jinr.ru")
        self.start_url_entry = ttk.Entry(settings_frame, textvariable=self.start_url_var, width=50)
        self.start_url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        # Максимальное количество страниц
        ttk.Label(settings_frame, text="Максимум страниц:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.max_pages_var = tk.IntVar(value=100)
        self.max_pages_spinbox = ttk.Spinbox(settings_frame, from_=1, to=1000,
                                             textvariable=self.max_pages_var, width=20)
        self.max_pages_spinbox.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Задержка между запросами
        ttk.Label(settings_frame, text="Задержка (секунды):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.delay_var = tk.DoubleVar(value=0.5)
        self.delay_spinbox = ttk.Spinbox(settings_frame, from_=0.1, to=5.0, increment=0.1,
                                         textvariable=self.delay_var, width=20)
        self.delay_spinbox.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Максимальная глубина
        ttk.Label(settings_frame, text="Максимальная глубина:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.max_depth_var = tk.IntVar(value=5)
        self.max_depth_spinbox = ttk.Spinbox(settings_frame, from_=1, to=10,
                                             textvariable=self.max_depth_var, width=20)
        self.max_depth_spinbox.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # Кнопки управления
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, pady=(10, 10))

        self.start_button = ttk.Button(buttons_frame, text="▶ Старт", command=self.start_crawling)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(buttons_frame, text="⏹ Стоп", command=self.stop_crawling, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=5)

        self.save_button = ttk.Button(buttons_frame, text="💾 Сохранить результаты",
                                      command=self.save_results, state='disabled')
        self.save_button.grid(row=0, column=2, padx=5)

        # Прогресс бар
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                            maximum=100, length=400)
        self.progress_bar.grid(row=3, column=0, pady=(10, 10), sticky=(tk.W, tk.E))

        # Статус
        self.status_label = ttk.Label(main_frame, text="Готов к работе", font=('Arial', 10))
        self.status_label.grid(row=4, column=0, pady=(0, 10))

        # Рамка с логом
        log_frame = ttk.LabelFrame(main_frame, text="Лог работы", padding="5")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Рамка со статистикой
        stats_frame = ttk.LabelFrame(main_frame, text="Текущая статистика", padding="5")
        stats_frame.grid(row=6, column=0, sticky=(tk.W, tk.E))
        stats_frame.columnconfigure(1, weight=1)

        self.stats_vars = {}
        stats_labels = [
            ("Обработано страниц:", "processed"),
            ("Успешных (200):", "success"),
            ("Ошибок (4xx/5xx):", "errors"),
            ("Найдено ссылок:", "links_found"),
            ("Текущая глубина:", "current_depth")
        ]

        for i, (label, key) in enumerate(stats_labels):
            ttk.Label(stats_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            self.stats_vars[key] = tk.StringVar(value="0")
            ttk.Label(stats_frame, textvariable=self.stats_vars[key]).grid(row=i, column=1, sticky=tk.W, pady=2,
                                                                           padx=(10, 0))

        # Результаты
        self.results_df = None

    def log_message(self, message, level="INFO"):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_tags = {
            "INFO": "black",
            "SUCCESS": "green",
            "WARNING": "orange",
            "ERROR": "red"
        }

        self.log_text.insert(tk.END, f"[{timestamp}] {level}: {message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.tag_config("INFO", foreground="black")
        self.log_text.tag_config("SUCCESS", foreground="green")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("ERROR", foreground="red")

        self.root.update_idletasks()

    def update_stats(self, processed, success, errors, links_found, current_depth):
        """Обновление статистики"""
        self.stats_vars["processed"].set(str(processed))
        self.stats_vars["success"].set(str(success))
        self.stats_vars["errors"].set(str(errors))
        self.stats_vars["links_found"].set(str(links_found))
        self.stats_vars["current_depth"].set(str(current_depth))

        if self.max_pages_var.get() > 0:
            progress = (processed / self.max_pages_var.get()) * 100
            self.progress_var.set(min(progress, 100))

    def start_crawling(self):
        """Запуск краулинга в отдельном потоке"""
        if self.is_crawling:
            messagebox.showwarning("Предупреждение", "Краулинг уже выполняется!")
            return

        # Очистка лога и статистики
        self.log_text.delete(1.0, tk.END)
        self.results_df = None

        # Получение настроек
        start_url = self.start_url_var.get().strip()
        if not start_url:
            messagebox.showerror("Ошибка", "Введите стартовый URL!")
            return

        max_pages = self.max_pages_var.get()
        delay = self.delay_var.get()
        max_depth = self.max_depth_var.get()

        # Блокировка кнопок
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.save_button.config(state='disabled')
        self.is_crawling = True

        # Запуск в отдельном потоке
        self.crawling_thread = threading.Thread(
            target=self.run_crawler,
            args=(start_url, max_pages, delay, max_depth),
            daemon=True
        )
        self.crawling_thread.start()

    def stop_crawling(self):
        """Остановка краулинга"""
        if self.crawler_instance:
            self.crawler_instance.stop_crawling = True
            self.log_message("Остановка краулинга...", "WARNING")

    def run_crawler(self, start_url, max_pages, delay, max_depth):
        """Запуск краулера"""
        try:
            crawler = CrawlerWithGUI(self, start_url, max_pages, delay, max_depth)
            self.crawler_instance = crawler
            self.results_df = crawler.crawl()

            if self.results_df is not None and len(self.results_df) > 0:
                self.save_button.config(state='normal')
                self.log_message(f"Краулинг завершен! Обработано {len(self.results_df)} страниц", "SUCCESS")
            else:
                self.log_message("Краулинг завершен без результатов", "WARNING")

        except Exception as e:
            self.log_message(f"Ошибка: {str(e)}", "ERROR")
        finally:
            self.is_crawling = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.crawler_instance = None

    def save_results(self):
        """Сохранение результатов в CSV"""
        if self.results_df is None or self.results_df.empty:
            messagebox.showwarning("Предупреждение", "Нет данных для сохранения!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"crawler_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if filename:
            try:
                self.results_df.to_csv(filename, index=False, encoding='utf-8-sig')
                self.log_message(f"Результаты сохранены в {filename}", "SUCCESS")
                messagebox.showinfo("Успех", f"Результаты сохранены в:\n{filename}")
            except Exception as e:
                self.log_message(f"Ошибка сохранения: {str(e)}", "ERROR")
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")


class CrawlerWithGUI:
    """Класс краулера с поддержкой GUI"""

    def __init__(self, gui, start_url, max_pages, delay, max_depth):
        self.gui = gui
        self.start_url = self.normalize_url(start_url)
        self.base_domain = urlparse(self.start_url).netloc
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.stop_crawling = False

        # Множества для отслеживания
        self.visited_urls = set()
        self.queued_urls = set()
        self.failed_urls = set()
        self.queue = deque()
        self.links_data = []

        # Сессия
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def normalize_url(self, url):
        """Нормализация URL"""
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]

        path = parsed.path
        if path.endswith('/') and len(path) > 1:
            path = path[:-1]
        if not path:
            path = '/'

        return urlunparse((parsed.scheme, netloc, path, '', '', ''))

    def is_valid_url(self, url):
        """Проверка валидности URL"""
        parsed = urlparse(url)
        if 'jinr.ru' not in parsed.netloc:
            return False

        excluded = ['.pdf', '.jpg', '.png', '.zip', '.doc', '.mp4']
        if any(url.lower().endswith(ext) for ext in excluded):
            return False

        return True

    def extract_links(self, url, html, current_depth):
        """Извлечение ссылок"""
        if current_depth >= self.max_depth:
            return set()

        soup = BeautifulSoup(html, 'html.parser')
        links = set()

        for tag in soup.find_all('a', href=True):
            href = tag.get('href', '').strip()
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue

            full_url = urljoin(url, href)
            normalized = self.normalize_url(full_url)

            if self.is_valid_url(normalized):
                links.add((normalized, current_depth + 1))

        return links

    def crawl(self):
        """Основной метод краулинга"""
        self.queue.append((self.start_url, 0))
        self.queued_urls.add(self.start_url)

        self.gui.log_message(f"Начинаем обход: {self.start_url}", "INFO")
        self.gui.log_message(f"Максимум страниц: {self.max_pages}, Глубина: {self.max_depth}", "INFO")

        processed = 0
        success_count = 0
        error_count = 0
        total_links = 0

        while self.queue and processed < self.max_pages and not self.stop_crawling:
            url, depth = self.queue.popleft()

            if url in self.visited_urls:
                continue

            self.gui.log_message(f"Обработка [{processed + 1}/{self.max_pages}]: {url} (глубина {depth})", "INFO")

            try:
                response = self.session.get(url, timeout=10, allow_redirects=True)
                status_code = response.status_code

                links = set()
                if status_code == 200:
                    links = self.extract_links(url, response.text, depth)
                    total_links += len(links)

                    new_links = 0
                    for link_url, link_depth in links:
                        if link_url not in self.visited_urls and link_url not in self.queued_urls:
                            self.queue.append((link_url, link_depth))
                            self.queued_urls.add(link_url)
                            new_links += 1

                    self.gui.log_message(f"  Найдено ссылок: {len(links)}, добавлено новых: {new_links}", "INFO")
                    success_count += 1
                else:
                    error_count += 1
                    self.gui.log_message(f"  Ошибка HTTP {status_code}", "WARNING")

                self.links_data.append({
                    'source_url': url,
                    'depth': depth,
                    'status_code': status_code,
                    'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'links_found': len(links)
                })

                processed += 1
                self.visited_urls.add(url)

                # Обновление статистики в GUI
                self.gui.update_stats(processed, success_count, error_count, total_links, depth)

                time.sleep(self.delay)

            except Exception as e:
                error_count += 1
                self.gui.log_message(f"  Ошибка: {str(e)[:100]}", "ERROR")
                self.links_data.append({
                    'source_url': url,
                    'depth': depth,
                    'status_code': 0,
                    'check_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'links_found': 0
                })
                processed += 1
                self.visited_urls.add(url)

        if self.stop_crawling:
            self.gui.log_message("Краулинг остановлен пользователем", "WARNING")

        return pd.DataFrame(self.links_data)


def main():
    root = tk.Tk()
    app = CrawlerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()