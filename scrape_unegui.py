"""
unegui.mn-ээс орон сууцны зарын мэдээлэл цуглуулах скрипт.

Ашиглах:
    pip install -r requirements.txt
    python scrape_unegui.py --pages 50 --out data/listings.csv
"""

import argparse
import csv
import re
import time
from pathlib import Path
from typing import Optional

import cloudscraper
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://www.unegui.mn"
LIST_PATH = "/l-hdlh/l-hdlh-zarna/oron-suuts-zarna/"

REQUEST_DELAY = 1.5  # секунд — серверт ачаалал өгөхгүйн тулд
TIMEOUT = 30


def make_scraper():
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "darwin", "mobile": False}
    )


def parse_price(text: str) -> Optional[float]:
    """'250 сая ₮' гэх мэт текстийг тооруу хөрвүүлнэ. Үр дүн: төгрөг."""
    if not text:
        return None
    t = text.lower().replace(",", ".").strip()
    nums = re.findall(r"[\d.]+", t)
    if not nums:
        return None
    val = float(nums[0])
    if "тэр" in t or "bln" in t:
        return val * 1_000_000_000
    if "сая" in t or "mln" in t:
        return val * 1_000_000
    return val


def parse_int(text: str) -> Optional[int]:
    if not text:
        return None
    nums = re.findall(r"\d+", text)
    return int(nums[0]) if nums else None


def parse_float(text: str) -> Optional[float]:
    if not text:
        return None
    nums = re.findall(r"[\d.]+", text.replace(",", "."))
    return float(nums[0]) if nums else None


def get_attr(soup: BeautifulSoup, label: str) -> Optional[str]:
    """Зарын дэлгэрэнгүй хэсгээс шинж чанарыг олно (ж: 'Талбай:')."""
    for li in soup.select("ul.chars-column li"):
        key = li.select_one(".key-chars")
        val = li.select_one(".value-chars, a.value-chars")
        if key and label.lower() in key.get_text(strip=True).lower():
            return val.get_text(strip=True) if val else None
    return None


def parse_listing_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.select("a.advert__content-title, a.mask"):
        href = a.get("href")
        if href and "/adv/" in href:
            full = href if href.startswith("http") else BASE_URL + href
            links.append(full)
    return list(dict.fromkeys(links))  # давхцлыг арилгана


def parse_rooms_from_title(title: str) -> Optional[int]:
    """'3 өрөө байр' гэх мэт гарчгаас өрөөний тоог авна."""
    if not title:
        return None
    m = re.search(r"(\d+)\s*өр(өө)?", title.lower())
    return int(m.group(1)) if m else None


def split_location(loc: str) -> tuple[Optional[str], Optional[str]]:
    """'Сүхбаатар, Сүхбаатар, Хороо 6' → ('Сүхбаатар', 'Хороо 6')"""
    if not loc:
        return None, None
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    district = parts[0] if parts else None
    khoroo = parts[-1] if len(parts) > 1 else None
    return district, khoroo


def parse_listing(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    title_el = soup.select_one("h1.title-announcement, h1")
    title = title_el.get_text(strip=True) if title_el else None

    price_el = soup.select_one(".announcement-price__cost, [itemprop='price']")
    price_raw = price_el.get_text(" ", strip=True) if price_el else None

    location_el = soup.select_one(".announcement-meta__location, span[itemprop='address']")
    location = location_el.get_text(" ", strip=True) if location_el else None
    district, khoroo = split_location(location)

    date_el = soup.select_one(".date-meta")
    date_text = date_el.get_text(" ", strip=True) if date_el else None

    area_raw = get_attr(soup, "Талбай")
    floor_raw = get_attr(soup, "Хэдэн давхарт")
    total_floor_raw = get_attr(soup, "Барилгын давхар")
    year_raw = get_attr(soup, "Ашиглалтанд")
    balcony_raw = get_attr(soup, "Тагт")
    garage_raw = get_attr(soup, "Гараж")
    window_raw = get_attr(soup, "Цонх:")  # 'Цонх:' vs 'Цонхны тоо:' зөрүү
    window_count_raw = get_attr(soup, "Цонхны тоо")
    door_raw = get_attr(soup, "Хаалга")
    floor_material_raw = get_attr(soup, "Шал")
    payment_raw = get_attr(soup, "Төлбөрийн нөхцөл")
    elevator_raw = get_attr(soup, "Цахилгаан шат")
    progress_raw = get_attr(soup, "Барилгын явц")

    return {
        "url": url,
        "title": title,
        "price_raw": price_raw,
        "price_mnt": parse_price(price_raw) if price_raw else None,
        "location": location,
        "district": district,
        "khoroo": khoroo,
        "date_posted": date_text,
        "area_m2": parse_float(area_raw) if area_raw else None,
        "rooms": parse_rooms_from_title(title),
        "floor": parse_int(floor_raw) if floor_raw else None,
        "total_floors": parse_int(total_floor_raw) if total_floor_raw else None,
        "year_built": parse_int(year_raw) if year_raw else None,
        "balcony": balcony_raw,
        "garage": garage_raw,
        "window_type": window_raw,
        "window_count": parse_int(window_count_raw) if window_count_raw else None,
        "door_type": door_raw,
        "floor_material": floor_material_raw,
        "payment_terms": payment_raw,
        "elevator": elevator_raw,
        "construction_status": progress_raw,
    }


def scrape(pages: int, out_path: Path, start_page: int = 1):
    scraper = make_scraper()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "url", "title", "price_raw", "price_mnt", "location", "district", "khoroo",
        "date_posted", "area_m2", "rooms", "floor", "total_floors", "year_built",
        "balcony", "garage", "window_type", "window_count", "door_type",
        "floor_material", "payment_terms", "elevator", "construction_status",
    ]

    seen_urls: set[str] = set()
    if out_path.exists():
        with out_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            seen_urls = {row["url"] for row in reader if row.get("url")}
        print(f"Өмнөх файлаас {len(seen_urls)} зарыг алгасна.")

    write_header = not out_path.exists()
    with out_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        # 1. Бүх хуудаснаас зарын линк цуглуулна
        all_links: list[str] = []
        for page in range(start_page, start_page + pages):
            url = f"{BASE_URL}{LIST_PATH}?page={page}"
            try:
                resp = scraper.get(url, timeout=TIMEOUT)
                if resp.status_code != 200:
                    print(f"[{page}] HTTP {resp.status_code}, алгасав")
                    continue
                links = parse_listing_links(resp.text)
                if not links:
                    print(f"[{page}] зар олдсонгүй — зогсооно")
                    break
                all_links.extend(links)
                print(f"[{page}] {len(links)} зар олдов")
            except Exception as e:
                print(f"[{page}] алдаа: {e}")
            time.sleep(REQUEST_DELAY)

        all_links = [u for u in dict.fromkeys(all_links) if u not in seen_urls]
        print(f"Нийт {len(all_links)} шинэ зар татна.")

        # 2. Зар тус бүрийн дэлгэрэнгүйг татна
        for url in tqdm(all_links, desc="Зар татаж байна"):
            try:
                resp = scraper.get(url, timeout=TIMEOUT)
                if resp.status_code != 200:
                    continue
                row = parse_listing(resp.text, url)
                writer.writerow(row)
                f.flush()
            except Exception as e:
                print(f"Алдаа {url}: {e}")
            time.sleep(REQUEST_DELAY)

    print(f"\nДууссан → {out_path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pages", type=int, default=20, help="Хэдэн жагсаалтын хуудас уншихыг сонгоно")
    p.add_argument("--start", type=int, default=1, help="Эхлэх хуудасны дугаар")
    p.add_argument("--out", type=str, default="data/listings.csv", help="Гаралтын CSV зам")
    args = p.parse_args()
    scrape(pages=args.pages, out_path=Path(args.out), start_page=args.start)


if __name__ == "__main__":
    main()
