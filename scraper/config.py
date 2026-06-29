# filepath: scraper/config.py

FEED_SOURCES = [
    {
        "name": "Detik Travel",
        "url": "https://rss.detik.com/index.php/travel",
        "category": "flight",
        "selector": "article.detail, .detail__body-text"
    },
    {
        "name": "Detik Food",
        "url": "https://rss.detik.com/index.php/food",
        "category": "food",
        "selector": "article.detail, .detail__body-text"
    },
    {
        "name": "Antara News Lifestyle",
        "url": "https://www.antaranews.com/rss/lifestyle.xml",
        "category": "food",
        "selector": "article.post, .post-content, .entry-content"
    }
]
