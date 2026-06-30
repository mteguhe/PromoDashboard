# filepath: scraper/config.py

FEED_SOURCES = [
    {
        "name": "Detik Travel",
        "url": "https://rss.detik.com/index.php/travel",
        "category": "flight",
        "selector": "article.detail, .detail__body-text"
    },
    {
        "name": "Katalog Promosi",
        "url": "https://katalogpromosi.com/feed/",
        "category": "food",
        "selector": ".entry-content, article.post, .post-content"
    },
    {
        "name": "Antara News Lifestyle",
        "url": "https://www.antaranews.com/rss/lifestyle.xml",
        "category": "food",
        "selector": "article.post, .post-content, .entry-content"
    },
    {
        "name": "Jadwal Event",
        "url": "https://jadwalevent.web.id/feed",
        "category": "event",
        "selector": ".entry-content, article.post, .post-content"
    }
]
