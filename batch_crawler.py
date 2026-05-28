import os
import sys
from datetime import datetime
from urllib.parse import urlparse
import pandas as pd
from crawler import WebCrawler


def get_settings():
    """Запрашивает у пользователя настройки краулера"""
    print("\n" + "=" * 60)
    print("НАСТРОЙКИ КРАУЛЕРА")
    print("=" * 60)

    # Максимальное количество страниц
    while True:
        try:
            max_pages = input("Максимальное количество страниц для одного сайта (по умолчанию 50): ").strip()
            if not max_pages:
                max_pages = 50
                break
            max_pages = int(max_pages)
            if max_pages > 0:
                break
            else:
                print("Пожалуйста, введите положительное число")
        except ValueError:
            print("Пожалуйста, введите корректное число")

    # Задержка между запросами
    while True:
        try:
            delay = input("Задержка между запросами в секундах (по умолчанию 0.5): ").strip()
            if not delay:
                delay = 0.5
                break
            delay = float(delay)
            if delay >= 0:
                break
            else:
                print("Пожалуйста, введите неотрицательное число")
        except ValueError:
            print("Пожалуйста, введите корректное число")

    # Таймаут
    while True:
        try:
            timeout = input("Таймаут ожидания ответа от сервера в секундах (по умолчанию 10): ").strip()
            if not timeout:
                timeout = 10
                break
            timeout = int(timeout)
            if timeout > 0:
                break
            else:
                print("Пожалуйста, введите положительное число")
        except ValueError:
            print("Пожалуйста, введите корректное число")

    # Максимальная глубина
    while True:
        try:
            max_depth = input("Максимальная глубина обхода (0 - только главная страница, по умолчанию 20): ").strip()
            if not max_depth:
                max_depth = 20
                break
            max_depth = int(max_depth)
            if max_depth >= 0:
                break
            else:
                print("Пожалуйста, введите неотрицательное число")
        except ValueError:
            print("Пожалуйста, введите корректное число")

    # Ограничение доменом
    same_domain_input = input("Ограничиваться только этим доменом? (y/n, по умолчанию y): ").strip().lower()
    same_domain_only = same_domain_input != 'n'

    return {
        'max_pages': max_pages,
        'delay': delay,
        'timeout': timeout,
        'max_depth': max_depth,
        'same_domain_only': same_domain_only
    }


def load_domains(filename: str = "domains.txt"):
    """Загружает список доменов из файла (по одному на строку)"""
    if not os.path.exists(filename):
        print(f"\n[ОШИБКА] Файл {filename} не найден!")
        print("Создайте файл domains.txt с сайтами (по одному на строку)")
        print("Пример:")
        print("  https://jinr.ru")
        print("  https://google.com")
        return []

    with open(filename, 'r', encoding='utf-8') as f:
        domains = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if not line.startswith(('http://', 'https://')):
                    line = 'https://' + line
                domains.append(line)

    print(f"\n[OK] Загружено сайтов: {len(domains)}")
    return domains


def create_date_folder():
    """Создаёт папку с текущей датой"""
    date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    folder_name = f"results_{date_str}"
    os.makedirs(folder_name, exist_ok=True)
    os.makedirs(os.path.join(folder_name, "csv"), exist_ok=True)
    return folder_name


def crawl_site(site_url: str, folder: str, settings: dict, index: int, total: int):
    """Запускает краулер для одного сайта с переданными настройками"""
    print("\n" + "=" * 70)
    print(f"[{index}/{total}] Обработка сайта: {site_url}")
    print("=" * 70)

    domain = urlparse(site_url).netloc.replace('.', '_')

    try:
        crawler = WebCrawler(
            start_url=site_url,
            max_pages=settings['max_pages'],
            delay=settings['delay'],
            same_domain_only=settings['same_domain_only'],
            timeout=settings['timeout'],
            max_depth=settings['max_depth']
        )

        crawler.crawl()

        if crawler.links_data:
            csv_path = os.path.join(folder, "csv", f"{domain}.csv")
            df = crawler.save_to_csv(csv_path)
            print(f"[OK] Сохранено: {csv_path}")
            return df
        else:
            print(f"[ПРЕДУПРЕЖДЕНИЕ] Для {site_url} не получено данных")
            return None

    except Exception as e:
        print(f"[ОШИБКА] При обработке {site_url}: {e}")
        return None


def collect_broken_links(all_results):
    """Собирает все битые ссылки из всех результатов"""
    broken_data = []

    for result in all_results:
        if result is not None and len(result) > 0:
            broken = result[
                (result['status_code'] >= 400) |
                (result['status_code'] == 0)
                ].copy()

            if len(broken) > 0:
                broken_data.append(broken)

    if broken_data:
        return pd.concat(broken_data, ignore_index=True)
    else:
        return pd.DataFrame()


def save_broken_links(broken_df, folder: str):
    """Сохраняет битые ссылки в отдельный файл"""
    if len(broken_df) == 0:
        print("\n[+] Битых ссылок не найдено!")
        return None

    broken_df = broken_df.sort_values('status_code')

    # CSV
    broken_path = os.path.join(folder, "broken_links.csv")
    broken_df.to_csv(broken_path, index=False, encoding='utf-8-sig')

    # TXT
    txt_path = os.path.join(folder, "broken_links.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("СПИСОК БИТЫХ ССЫЛОК (по всем сайтам)\n")
        f.write(f"Дата проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        for status in sorted(broken_df['status_code'].unique()):
            status_df = broken_df[broken_df['status_code'] == status]
            status_name = {
                404: "Не найдено (404)",
                408: "Таймаут (408)",
                500: "Ошибка сервера (500)",
                503: "Нет соединения (503)",
                0: "Неизвестная ошибка"
            }.get(status, f"Код {status}")

            f.write(f"\n--- {status_name} ({len(status_df)} ссылок) ---\n")
            for _, row in status_df.iterrows():
                f.write(f"  {row['source_url']}\n")
                if row['error_message']:
                    f.write(f"    Ошибка: {row['error_message']}\n")

    print(f"\n[!] Найдено битых ссылок: {len(broken_df)}")
    print(f"[OK] Сохранено: {broken_path}")
    print(f"[OK] Сохранено: {txt_path}")

    return broken_path


def print_summary(all_results, broken_df):
    """Выводит итоговую статистику"""
    print("\n" + "=" * 70)
    print("ИТОГОВАЯ СТАТИСТИКА ПО ВСЕМ САЙТАМ")
    print("=" * 70)

    total_pages = 0
    total_ok = 0
    total_broken = 0

    for result in all_results:
        if result is not None:
            total_pages += len(result)
            total_ok += len(result[result['status_code'] == 200])
            total_broken += len(result[result['status_code'] >= 400])

    if total_pages > 0:
        print(f"\nВсего проверено страниц: {total_pages}")
        print(f"  - Успешных (200): {total_ok} ({total_ok * 100 // total_pages}%)")
        print(f"  - Битых: {total_broken} ({total_broken * 100 // total_pages}%)")
    else:
        print("\nНет данных для статистики")

    if len(broken_df) > 0:
        print(f"\nРаспределение битых ссылок по кодам:")
        for status, count in broken_df['status_code'].value_counts().sort_index().items():
            status_name = {
                404: "Не найдено",
                408: "Таймаут",
                500: "Ошибка сервера",
                503: "Нет соединения",
                0: "Неизвестная ошибка"
            }.get(status, f"Код {status}")
            print(f"  {status} ({status_name}): {count}")


def print_broken_links_console(broken_df):
    """Выводит битые ссылки в консоль"""
    if len(broken_df) == 0:
        return

    print("\n" + "=" * 70)
    print("СПИСОК БИТЫХ ССЫЛОК:")
    print("=" * 70)

    for _, row in broken_df.iterrows():
        status = row['status_code']
        url = row['source_url']
        error = row['error_message']

        if status == 404:
            print(f"  [404] {url}")
        elif status == 408:
            print(f"  [408] {url} (таймаут)")
        elif status == 503:
            print(f"  [503] {url} (нет соединения)")
        elif status >= 500:
            print(f"  [{status}] {url} (ошибка сервера)")
        else:
            print(f"  [{status}] {url}")

        if error and error not in ['', 'success']:
            print(f"      -> {error}")


def main():
    print("=" * 70)
    print("МАССОВЫЙ ВЕБ-КРАУЛЕР")
    print("Обработка списка сайтов из файла domains.txt")
    print("=" * 70)

    # 1. Запрашиваем настройки у пользователя
    settings = get_settings()

    # 2. Показываем введённые настройки
    print("\n" + "=" * 60)
    print("УСТАНОВЛЕННЫЕ НАСТРОЙКИ")
    print("=" * 60)
    print(f"  Максимум страниц на сайт: {settings['max_pages']}")
    print(f"  Задержка между запросами: {settings['delay']} сек")
    print(f"  Таймаут ожидания ответа: {settings['timeout']} сек")
    print(f"  Максимальная глубина: {settings['max_depth']}")
    print(f"  Только свой домен: {'Да' if settings['same_domain_only'] else 'Нет'}")

    # 3. Загружаем список сайтов
    domains = load_domains("domains.txt")
    if not domains:
        print("\n[ОШИБКА] Нет сайтов для обработки!")
        print("Создайте файл domains.txt в папке с программой")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)

    # 4. Создаём папку для результатов
    results_folder = create_date_folder()
    print(f"\n[OK] Результаты будут сохранены в: {results_folder}")

    # 5. Обрабатываем каждый сайт
    all_results = []
    for i, site in enumerate(domains, 1):
        df = crawl_site(site, results_folder, settings, i, len(domains))
        all_results.append(df)

    # 6. Собираем все битые ссылки
    broken_df = collect_broken_links(all_results)

    # 7. Сохраняем битые ссылки
    if len(broken_df) > 0:
        save_broken_links(broken_df, results_folder)
        print_broken_links_console(broken_df)
    else:
        print("\n[+] Отлично! Битых ссылок не найдено!")

    # 8. Итоговая статистика
    print_summary(all_results, broken_df)

    print("\n" + "=" * 70)
    print("ГОТОВО!")
    print(f"Результаты сохранены в папке: {results_folder}")
    print("=" * 70)
    input("\nНажмите Enter для выхода...")


if __name__ == '__main__':
    main()