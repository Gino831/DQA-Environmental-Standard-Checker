import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import os
import time
from contextlib import contextmanager

# ── HTTP Request Helper with Retry ──────────────────────────────────
DEFAULT_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def requests_with_retry(url, max_retries=2, timeout=15):
    """HTTP GET with retry logic for transient failures."""
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            return response
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt < max_retries:
                wait_time = 2 ** attempt  # exponential backoff: 1s, 2s
                print(f"  [Retry {attempt+1}/{max_retries}] {e.__class__.__name__}, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise


# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


# ââ Selenium Context Manager ââââââââââââââââââââââââââââââââââââââââââ
@contextmanager
def selenium_driver():
    """
    Context manager for Selenium WebDriver.
    Ensures the driver is always properly closed, even on exceptions.
    """
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--log-level=3')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        yield driver
    except Exception as e:
        print(f"Selenium driver error: {e}")
        yield None
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


# ââ Data Loading âââââââââââââââââââââââââââââââââââââââââââââ
def load_standards(base_path):
    """
    Loads standards from standards.json (preferred) or falls back to data.js parsing.
    """
    json_path = os.path.join(base_path, 'standards.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                standards = json.load(f)
            print(f"[LOAD] Loaded {len(standards)} standards from standards.json")
            return standards
        except Exception as e:
            print(f"[LOAD] Failed to read standards.json: {e}")

    data_path = os.path.join(base_path, 'data.js')
    if os.path.exists(data_path):
        try:
            standards = _parse_data_js(data_path)
            print(f"[LOAD] Loaded {len(standards)} standards from data.js (fallback)")
            return standards
        except Exception as e:
            print(f"[LOAD] Failed to parse data.js: {e}")

    print("[LOAD] No data source found!")
    return []


def _parse_data_js(file_path):
    """Parses standards from data.js - tries JSON extraction first, then regex fallback."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'window\.initialStandards\s*=\s*(\[.*\])\s*;', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    standards = []
    content = re.sub(r'(?m)^\s*//.*', '', content)
    chunks = content.split('{')
    for chunk in chunks:
        if '"id"' not in chunk and 'id:' not in chunk:
            continue
        std = {}
        def get_field(field_name, text):
            pattern = fr'(?:"{field_name}"|\b{field_name})\s*:\s*[\'"]([\\\'"]*)[\'"]'
            m = re.search(pattern, text)
            return m.group(1) if m else ''
        for field in ['id', 'name', 'cost', 'effectiveDate', 'expiryDate', 'sourceUrl', 'version']:
            std[field] = get_field(field, chunk)
        if std['id'] and std['name']:
            standards.append(std)
    return standards


# ââ Scrapers âââââââââââââââââââââââââââââââââââââââââââââââââ
def scrape_iec_page(url, driver):
    """Scrapes IEC webstore using Selenium."""
    if not driver:
        return {'error': 'Selenium driver not available'}
    try:
        driver.get(url)
        time.sleep(3)
        page_text = driver.find_element(By.TAG_NAME, "body").text
        data = {}
        lines = page_text.split('\n')

        for line in lines:
            line_lower = line.lower().strip()
            if 'publication date' in line_lower:
                match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
                if match:
                    data['publication_date'] = match.group(1)
            if 'stability date' in line_lower:
                match = re.search(r'(\d{4})', line)
                if match:
                    data['stability_date'] = match.group(1)
            if line_lower.startswith('edition') and 'amended' not in line_lower:
                match = re.search(r'(\d+\.?\d*)', line)
                if match:
                    data['edition'] = match.group(1)

        # Price scraping (3-layer fallback)
        price_found = None
        try:
            price_el = driver.find_element(By.CSS_SELECTOR, ".price-container .price, .product-price, span[itemprop='price']")
            if price_el:
                price_found = price_el.text.strip()
        except Exception:
            pass

        if not price_found:
            try:
                price_el = driver.find_element(By.XPATH, "//*[contains(text(), 'CHF') and string-length(text()) < 20]")
                if price_el:
                    price_found = price_el.text.strip()
            except Exception:
                pass

        if not price_found:
            price_match = re.search(r"CHF\s*([\d,\']+\.?\-?)", page_text)
            if price_match:
                price_found = f"CHF {price_match.group(1)}"

        if price_found:
            price_found = re.sub(r'\s+', ' ', price_found)
            data['price'] = price_found

        return data
    except Exception as e:
        return {'error': str(e)}


def scrape_ieee_page(url):
    """Scrapes IEEE page (static) with version comparison."""
    try:
        response = requests_with_retry(url)
        if response.status_code != 200:
            return {'error': f"HTTP {response.status_code}"}

        soup = BeautifulSoup(response.content, 'html.parser')
        data = {'source': 'IEEE', 'accessible': True}
        page_text = soup.get_text()

        title = soup.select_one('title')
        if title:
            title_text = title.get_text()
            match = re.search(r'IEEE\s+\d+[A-Za-z]*-(\d{4})', title_text)
            if match:
                data['version'] = match.group(1)

        edition_match = re.search(r'Edition\s+(\d+\.?\d*)', page_text, re.IGNORECASE)
        if edition_match:
            data['edition'] = edition_match.group(1)

        date_match = re.search(r'Published:\s*(\d{1,2}\s+\w+\s+\d{4})', page_text)
        if date_match:
            try:
                dt = datetime.strptime(date_match.group(1), '%d %B %Y')
                data['publication_date'] = dt.strftime('%Y-%m-%d')
            except Exception:
                pass

        return data
    except Exception as e:
        return {'error': str(e)}


def scrape_nema_store(url, driver):
    """Scrapes NEMA store using Selenium (bypass 403)."""
    if not driver:
        return {'error': 'Selenium driver not available'}
    try:
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        data = {'source': 'NEMA Store', 'accessible': True}

        title = soup.select_one('h1, .product-title, title')
        if title:
            match = re.search(r'(20\d{2})', title.get_text())
            if match:
                data['version'] = match.group(1)

        price_el = soup.select_one('.price, .product-price, [class*="price"]')
        if price_el:
            price_match = re.search(r'[\$\u20ac\u00a3]\s*[\d,]+\.?\d*', price_el.get_text(strip=True))
            if price_match:
                data['price'] = price_match.group(0)

        return data
    except Exception as e:
        return {'error': str(e)}


def scrape_bsi_knowledge(url, driver):
    """Scrapes BSI Knowledge using Selenium."""
    if not driver:
        return {'error': 'Selenium driver not available'}
    try:
        driver.get(url)
        time.sleep(5)
        page_text = driver.find_element(By.TAG_NAME, "body").text
        data = {'source': 'BSI Knowledge', 'accessible': True}

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        h1 = soup.select_one('h1')
        if h1:
            match = re.search(r':(\d{4})', h1.get_text(strip=True))
            if match:
                data['version'] = match.group(1)

        date_match = re.search(r'Published[:\s]*(\d{1,2}\s+\w+\s+\d{4})', page_text)
        if date_match:
            try:
                dt = datetime.strptime(date_match.group(1), '%d %b %Y')
                data['publication_date'] = dt.strftime('%Y-%m-%d')
            except Exception:
                pass

        price_match = re.search(r'Non-Member\s*(?:Total)?\s*[\u00a3$\u20ac]\s*([\d,\.]+)', page_text)
        if price_match:
            data['price'] = f"\u00a3{price_match.group(1)}"

        if 'Withdrawn' in page_text:
            data['status'] = 'Withdrawn'

        return data
    except Exception as e:
        return {'error': str(e)}


def scrape_smart_generic(url, standard_name):
    """Smart generic scraper - auto-detect version/price info."""
    try:
        response = requests_with_retry(url)
        if response.status_code != 200:
            return {'error': f"HTTP {response.status_code}", 'accessible': False}

        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()
        data = {'accessible': True, 'source': 'Smart Generic'}

        version_patterns = [
            (r'Issue\s+(\d+)', 'Issue'),
            (r'Edition\s+(\d+\.?\d*)', 'Ed.'),
            (r'Version\s+(\d+\.?\d*)', 'Ver.'),
            (r'Rev\.?\s*(\d+)', 'Rev.'),
            (r':\s*(20\d{2})\b', ''),
        ]
        for pattern, prefix in version_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                ver = match.group(1)
                data['version'] = f"{prefix} {ver}".strip() if prefix else ver
                data['edition'] = ver
                break

        price_patterns = [
            r'[\$\u20ac\u00a3\u00a5]\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:USD|EUR|GBP)',
        ]
        for pattern in price_patterns:
            match = re.search(pattern, page_text)
            if match:
                data['price'] = match.group(0)
                break

        return data
    except Exception as e:
        return {'error': str(e), 'accessible': False}


# ââ Unified Verification Logic âââââââââââââââââââââââââââââââââââ
def verify_standard_logic(std, live_data):
    """
    Unified comparison logic for all scraper types.
    Compares local standard data with live scraped data.
    Returns a list of issue strings.
    """
    issues = []

    # Edition / Version comparison
    live_ver = None
    if 'edition' in live_data:
        live_ver = live_data['edition']
    elif 'version' in live_data:
        live_ver = live_data['version']

    if live_ver:
        live_num = re.search(r'([\d]+\.?\d*)', str(live_ver))
        live_num = live_num.group(1) if live_num else str(live_ver)
        local_ver = std.get('version', '')
        local_num = re.search(r'([\d]+\.?\d*)', str(local_ver))
        local_num = local_num.group(1) if local_num else local_ver

        if live_num and (not local_num or live_num != local_num):
            label = 'Edition' if 'edition' in live_data else 'Version'
            issues.append(f"{label}: Local='{std.get('version') or '(empty)'}' vs Live='{live_ver}'")

    # Date comparison
    if 'publication_date' in live_data:
        if live_data['publication_date'] != std.get('effectiveDate'):
            issues.append(f"Date: Local='{std.get('effectiveDate')}' vs Live='{live_data['publication_date']}'")

    # Cost comparison
    if 'price' in live_data:
        live_price = re.sub(r'[^\d]', '', live_data['price'])
        local_price = re.sub(r'[^\d]', '', std.get('cost', ''))
        if live_price and (not local_price or live_price != local_price):
            issues.append(f"Cost: Local='{std.get('cost') or '(empty)'}' vs Live='{live_data['price']}'")

    # Stability date comparison
    if 'stability_date' in live_data:
        live_stab = live_data['stability_date']
        local_exp = std.get('expiryDate', '')
        if live_stab not in local_exp:
            issues.append(f"Stability: Local='{local_exp}' vs Live='{live_stab}'")

    # Withdrawn status
    if live_data.get('status') == 'Withdrawn':
        issues.append('Standard Withdrawn')

    return issues


# ââ Main Verification ââââââââââââââââââââââââââââââââââââââââ
def run_verification(base_path):
    """Main entry point for verification."""
    print("--- DQA Standard Verification Agent (Optimized) ---")

    standards = load_standards(base_path)
    print(f"Loaded {len(standards)} standards\n")

    json_results = []
    total = len(standards)

    with selenium_driver() as driver:
        if driver is None:
            print("[WARN] Selenium driver failed to initialize.")

        for idx, std in enumerate(standards, start=1):
            url = std.get('sourceUrl')
            name = std.get('name')
            std_id = std.get('id', f'std-{idx}')

            result_entry = {
                'id': std_id,
                'name': name,
                'url': url or '',
                'status': 'OK',
                'issues': []
            }

            if not url or '/search/' in url:
                result_entry['status'] = 'SKIPPED'
                json_results.append(result_entry)
                print(f"[{idx}/{total}] {name} - Skipped (no URL)")
                continue

            print(f"[{idx}/{total}] Checking {name}...", end=" ", flush=True)

            live_data = {}
            scraper_error = False

            # Route to appropriate scraper
            if 'webstore.iec.ch' in url:
                live_data = scrape_iec_page(url, driver)
            elif 'ieee.org' in url:
                live_data = scrape_ieee_page(url)
            elif 'store.accuristech.com' in url:
                live_data = scrape_nema_store(url, driver)
            elif 'bsigroup.com' in url:
                live_data = scrape_bsi_knowledge(url, driver)
            else:
                live_data = scrape_smart_generic(url, name)

            # Handle errors
            if 'error' in live_data:
                result_entry['status'] = 'ERROR'
                result_entry['issues'] = [live_data['error']]
                print(f"ERROR: {live_data['error']}")
                scraper_error = True
            elif live_data.get('accessible') is False:
                result_entry['status'] = 'WARNING'
                print("WARNING (not accessible)")
                scraper_error = True

            # Unified verification for all scrapers
            if not scraper_error:
                issues = verify_standard_logic(std, live_data)
                if issues:
                    result_entry['status'] = 'MISMATCH'
                    result_entry['issues'] = issues
                    print(f"MISMATCH: {'; '.join(issues)}")
                else:
                    print("OK")

            json_results.append(result_entry)

        # Rate limiting: brief delay between requests
        if idx < total:
            time.sleep(0.5)

    # Save report with summary
    json_report = {
        'timestamp': datetime.now().isoformat(),
        'total': total,
        'summary': {
            'ok': sum(1 for r in json_results if r['status'] == 'OK'),
            'mismatch': sum(1 for r in json_results if r['status'] == 'MISMATCH'),
            'error': sum(1 for r in json_results if r['status'] == 'ERROR'),
            'skipped': sum(1 for r in json_results if r['status'] == 'SKIPPED'),
            'warning': sum(1 for r in json_results if r['status'] == 'WARNING'),
        },
        'results': json_results
    }

    report_path = os.path.join(base_path, 'verification_results.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)

    s = json_report['summary']
    print(f"\n--- Verification Complete ---")
    print(f"OK: {s['ok']} | MISMATCH: {s['mismatch']} | ERROR: {s['error']} | SKIPPED: {s['skipped']}")

    return {'status': 'success', 'message': 'Verification complete'}


if __name__ == "__main__":
    run_verification(".")
