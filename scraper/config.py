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

OTA_SOURCES = [
    # Penerbangan — OTA yang terkonfirmasi dapat di-scrape
    {
        "name": "Airpaz Promo Penerbangan",
        "url": "https://www.airpaz.com/en/promo",
        "category": "flight",
        "platform": "Airpaz",
        "selector": "a[href*='/promo/view/']",
        "wait_ms": 3000,
    },
    {
        "name": "Traveloka Promo Penerbangan",
        "url": "https://www.traveloka.com/id-id/promotion?productType=FLIGHT",
        "category": "flight",
        "platform": "Traveloka",
        "selector": "a[href*='/id-id/promotion/detail'], a[href*='/promotion/detail']",
        "wait_ms": 5000,
    },
    {
        "name": "Trip.com Promo Penerbangan",
        "url": "https://id.trip.com/flights/cheapflights/",
        "category": "flight",
        "platform": "Trip.com",
        "selector": "[class*='FlightCard'], [class*='flight-card'], a[class*='deal'], li[class*='flight']",
        "wait_ms": 4000,
    },
    # Hotel
    {
        "name": "Traveloka Promo Hotel",
        "url": "https://www.traveloka.com/id-id/hotel/promotion",
        "category": "hotel",
        "platform": "Traveloka",
        "selector": "a[href*='/id-id/hotel/promotion/detail'], a[href*='/hotel/promotion/detail']",
        "wait_ms": 5000,
    },
    {
        "name": "Booking.com Deals Hotel",
        "url": "https://www.booking.com/deals.html",
        "category": "hotel",
        "platform": "Booking.com",
        "selector": "[data-testid='deal-card'], [class*='DealCard'], article[class*='deal']",
        "wait_ms": 4000,
    },
    {
        "name": "Agoda Last Minute Hotel",
        "url": "https://www.agoda.com/id-id/deals/hotel",
        "category": "hotel",
        "platform": "Agoda",
        "selector": "[data-selenium='hotel-item'], [class*='PropertyCard'], li[class*='hotel']",
        "wait_ms": 5000,
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
