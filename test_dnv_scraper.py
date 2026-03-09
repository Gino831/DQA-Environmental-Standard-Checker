from verify_standards import scrape_nema_store, selenium_driver
import json

url = "https://store.accuristech.com/standards/dnv-dnv-cg-0339?product_id=2842682"
print(f"Testing scraper for URL: {url}")

with selenium_driver() as driver:
    try:
        data = scrape_nema_store(url, driver)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
