import os
import sys
from crawler import WebCrawler


def get_user_input():
    """Получение параметров от пользователя"""
    print("=" * 60)
    print("ВЕБ-КРАУЛЕР")
    print("=" * 60)

    # Ввод URL
    while True:
        url = input("\nВведите URL для обхода (например, https://jinr.ru): ").strip()
        if url.startswith(('http://', 'https://')):
            break
        else:
            url = 'https://' + url
            break

    # Ввод количества страниц
    while True:
        try:
            max_pages = input(f"Максимальное количество страниц (по умолчанию 100): ").strip()
            if not max_pages:
                max_pages = 100
                break
            max_pages = int(max_pages)
            if max_pages > 0:
                break
            else:
                print("Пожалуйста, введите положительное число")
        except ValueError:
            print("Пожалуйста, введите корректное число")

    # Ввод задержки
    while True:
        try:
            delay = input(f"Задержка между запросами в секундах (по умолчанию 0.5): ").strip()
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

    # Вопрос об ограничении доменом
    same_domain = input(
        f"Ограничиваться только доменом {urlparse(url).netloc}? (y/n, по умолчанию y): ").strip().lower()
    same_domain_only = same_domain != 'n'

    return url, max_pages, delay, same_domain_only


def main():
    # Создание директорий
    os.makedirs('data', exist_ok=True)
    os.makedirs('graphs', exist_ok=True)

    # Получение параметров
    start_url, max_pages, delay, same_domain_only = get_user_input()

    # Запуск краулера
    print("\n" + "=" * 60)
    print("НАЧАЛО ОБХОДА САЙТА")
    print("=" * 60)
    print(f"📍 Стартовый URL: {start_url}")
    print(f"📄 Максимум страниц: {max_pages}")
    print(f"⏱️  Задержка: {delay} сек")
    print(f"🔒 Только этот домен: {'Да' if same_domain_only else 'Нет'}")
    print("\nНачинаем обход...\n")

    crawler = WebCrawler(
        start_url=start_url,
        max_pages=max_pages,
        delay=delay,
        same_domain_only=same_domain_only
    )

    crawler.crawl()

    # Сохранение результатов
    if crawler.links_data:
        # Создаем имя файла на основе домена
        domain = crawler.base_domain.replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/{domain}_{timestamp}.csv'

        df = crawler.save_to_csv(filename)

        # Вывод статистики
        print("\n" + "=" * 60)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 60)
        print(f"✅ Всего обработано страниц: {len(df)}")
        print(f"✅ Успешных (200): {len(df[df['status_code'] == 200])}")
        print(f"❌ Не найдено (404): {len(df[df['status_code'] == 404])}")
        print(f"⚠️  Ошибок сервера (5xx): {len(df[df['status_code'] >= 500])}")
        print(f"⏱️  Таймаутов: {len(df[df['status_code'] == 408])}")
        print(f"📊 Средняя глубина: {df['depth'].mean():.2f}")
        print(f"🔗 Среднее количество ссылок: {df['links_found'].mean():.2f}")

        # Показываем глубину обхода
        max_depth = df['depth'].max()
        print(f"\n📊 Глубина обхода:")
        for depth in range(max_depth + 1):
            count = len(df[df['depth'] == depth])
            print(f"   Глубина {depth}: {count} страниц")

        # Показываем топ страниц
        print("\n" + "=" * 60)
        print("ТОП-5 СТРАНИЦ ПО КОЛИЧЕСТВУ ССЫЛОК")
        print("=" * 60)
        top_pages = df.nlargest(5, 'links_found')[['source_url', 'links_found', 'depth']]
        for idx, row in top_pages.iterrows():
            print(f"  {row['links_found']} ссылок - {row['source_url'][:80]} (глубина: {row['depth']})")

        # Визуализация
        try:
            from visualizer import GraphVisualizer
            print("\n" + "=" * 60)
            print("СОЗДАНИЕ ГРАФА СВЯЗЕЙ")
            print("=" * 60)
            visualizer = GraphVisualizer(filename)
            visualizer.visualize('graphs/graph_{}.html'.format(domain))
            print("✅ Граф связей создан")
        except Exception as e:
            print(f"⚠️ Визуализация графа пропущена: {e}")

        print("\n" + "=" * 60)
        print("ГОТОВО!")
        print("=" * 60)
        print(f"📄 CSV файл: {filename}")
        print(f"📊 Граф: graphs/graph_{domain}.html")
    else:
        print("\n❌ Не удалось обработать ни одной страницы")


if __name__ == '__main__':
    from urllib.parse import urlparse
    from datetime import datetime

    main()