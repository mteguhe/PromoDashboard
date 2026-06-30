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
    },
    {
        "name": "Female Daily Fashion",
        "url": "https://femaledaily.com/feed",
        "category": "fashion",
        "selector": ".entry-content, .post-content, article"
    },
    {
        "name": "Detik Hot",
        "url": "https://rss.detik.com/index.php/hot",
        "category": "entertainment",
        "selector": "article.detail, .detail__body-text"
    },
]

PORTAL_SOURCES = [
    {
        "name": "Traveloka Promo",
        "url": "https://www.traveloka.com/id-id/promotion",
        "category": "flight",
        "selector": "a[data-testid='promotion-card'], .promotion-card, article.promo",
    },
    {
        "name": "Tiket.com Deals",
        "url": "https://www.tiket.com/promo",
        "category": "flight",
        "selector": ".promo-card, .deal-card, article.promo-item",
    },
    {
        "name": "Zalora Sale",
        "url": "https://www.zalora.co.id/sale/",
        "category": "fashion",
        "selector": ".catalogue__list article, .product-card, .promo-item",
    },
    {
        "name": "Loket Event",
        "url": "https://www.loket.com/event",
        "category": "event",
        "selector": ".event-card, .event-item, article.event",
    },
    {
        "name": "GoFood Promo",
        "url": "https://gofood.co.id/jakarta/promo",
        "category": "food",
        "selector": ".promo-card, .promotion-card, article.promo",
    },
]

SOCIAL_ACCOUNTS = [
    {
        "name": "Traveloka",
        "url": "https://www.threads.net/@traveloka",
        "category": "flight",
        "platform": "threads",
        "selector": "article, [data-pressable-container], .x9f619",
    },
    {
        "name": "Shopee Indonesia",
        "url": "https://www.threads.net/@shopee_id",
        "category": "food",
        "platform": "threads",
        "selector": "article, [data-pressable-container]",
    },
    {
        "name": "Zalora Indonesia",
        "url": "https://www.threads.net/@zaloraid",
        "category": "fashion",
        "platform": "threads",
        "selector": "article, [data-pressable-container]",
    },
    {
        "name": "Loket",
        "url": "https://www.threads.net/@loket.com",
        "category": "event",
        "platform": "threads",
        "selector": "article, [data-pressable-container]",
    },
]
