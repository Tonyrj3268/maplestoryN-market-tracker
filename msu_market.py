# msu_market.py
from decimal import ROUND_HALF_UP, Decimal
from statistics import mean, median

import cloudscraper
from tabulate import tabulate

WEI_PER_ETHER = Decimal("1000000000000000000")  # 1 Ether = 10^18 Wei


def fetch_items(item_name: str):
    url = "https://msu.io/marketplace/api/marketplace/explore/items"
    payload = {
        "filter": {
            "name": item_name.lower(),
            "categoryNo": 0,
            "classes": ["thief"],
            "price": {"min": 0, "max": 10000000000},
            "level": {"min": 0, "max": 250},
            "starforce": {"min": 0, "max": 25},
            "potential": {"min": 0, "max": 4},
            "bonusPotential": {"min": 0, "max": 4},
        },
        "sorting": "ExploreSorting_LOWEST_PRICE",
        "paginationParam": {"pageNo": 1, "pageSize": 135},
    }

    scraper = cloudscraper.create_scraper()
    response = scraper.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def compute_price_stats(items: list):
    prices = []
    for item in items:
        price_wei_str = item.get("salesInfo", {}).get("priceWei")
        if price_wei_str:
            price_wei = Decimal(price_wei_str)
            price_ether = (price_wei / WEI_PER_ETHER).quantize(
                Decimal("0.000000000000000001"), rounding=ROUND_HALF_UP
            )
            prices.append(price_ether)

    if not prices:
        return None

    prices.sort()

    lowest_price = prices[0]
    second_lowest_price = prices[1] if len(prices) > 1 else None
    avg_price = Decimal(mean(prices)) if prices else Decimal("0")
    median_price = Decimal(median(prices)) if prices else Decimal("0")

    price_gap_percent = None
    if second_lowest_price:
        price_gap_percent = (
            (second_lowest_price - lowest_price) / second_lowest_price * 100
        ).quantize(Decimal("0.01"))

    median_discount_percent = None
    if median_price > 0:
        median_discount_percent = (
            (median_price - lowest_price) / median_price * 100
        ).quantize(Decimal("0.01"))

    avg_discount_percent = None
    if avg_price > 0:
        avg_discount_percent = ((avg_price - lowest_price) / avg_price * 100).quantize(
            Decimal("0.01")
        )

    should_buy = False
    if price_gap_percent and median_discount_percent:
        if price_gap_percent > 10 and median_discount_percent > 20:
            should_buy = True

    return {
        "lowest_price": lowest_price,
        "second_lowest_price": second_lowest_price,
        "avg_price": avg_price,
        "median_price": median_price,
        "price_gap_percent": price_gap_percent,
        "median_discount_percent": median_discount_percent,
        "avg_discount_percent": avg_discount_percent,
        "should_buy": should_buy,
    }


def format_price_table(item_name: str, stats: dict):
    if not stats:
        return f"**{item_name}**\n沒有找到任何價格資訊。"

    headers = ["指標", "數值"]
    rows = [
        ["最低價 (Ether)", str(stats["lowest_price"])],
        [
            "第二低價 (Ether)",
            (
                str(stats["second_lowest_price"])
                if stats["second_lowest_price"]
                else "N/A"
            ),
        ],
        [
            "平均價 (Ether)",
            str(
                stats["avg_price"].quantize(
                    Decimal("0.000000000000000001"), rounding=ROUND_HALF_UP
                )
            ),
        ],
        [
            "中位數 (Ether)",
            str(
                stats["median_price"].quantize(
                    Decimal("0.000000000000000001"), rounding=ROUND_HALF_UP
                )
            ),
        ],
        [
            "最低價相對第二低價差距(%)",
            (
                f"{stats['price_gap_percent']}%"
                if stats["price_gap_percent"] is not None
                else "N/A"
            ),
        ],
        [
            "最低價相對中位數折扣(%)",
            (
                f"{stats['median_discount_percent']}%"
                if stats["median_discount_percent"] is not None
                else "N/A"
            ),
        ],
        [
            "最低價相對平均價折扣(%)",
            (
                f"{stats['avg_discount_percent']}%"
                if stats["avg_discount_percent"] is not None
                else "N/A"
            ),
        ],
        ["建議", "建議入手" if stats["should_buy"] else "不建議入手"],
    ]

    table_str = tabulate(rows, headers=headers, tablefmt="grid")
    return f"**{item_name}**\n```{table_str}```"
