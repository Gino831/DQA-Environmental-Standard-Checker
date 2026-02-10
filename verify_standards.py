import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import os
import time

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Global Selenium driver
_selenium_driver = None

def get_selenium_driver():
    """
    Returns a singleton Selenium WebDriver instance.
    Creates one if it doesn't exist.
    """
    global _selenium_driver
    if _selenium_driver is None:
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            chrome_options.add_argument('--log-level=3')  # Suppress console logs
            
            # Suppress driver logs
            service = Service(ChromeDriverManager().install())
            # service.creation_flags = 0x08000000  # CREATE_NO_WINDOW (Windows only)
            
            _selenium_driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"Failed to initialize Selenium driver: {e}")
            return None
            
    return _selenium_driver

def close_selenium_driver():
    """Closes the Selenium WebDriver if it exists."""
    global _selenium_driver
    if _selenium_driver is not None:
        try:
            _selenium_driver.quit()
        except:
            pass
        _selenium_driver = None

def load_standards(file_path):
    """Loads standards from data.js"""
    standards = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Remove comments
        content = re.sub(r'(?m)^\s*//.*', '', content)
        
        chunks = content.split('{')
        for chunk in chunks:
            if '"id"' not in chunk and 'id:' not in chunk:
                continue
                
            std = {}
            def get_field(field_name, text):
                pattern = fr'(?:"{field_name}"|\b{field_name})\s*:\s*[\'"]([^\'"]*)[\'"]'
                match = re.search(pattern, text)
                return match.group(1) if match else ''
                
            std['id'] = get_field('id', chunk)
            std['name'] = get_field('name', chunk)
            std['cost'] = get_field('cost', chunk)
            std['effectiveDate'] = get_field('effectiveDate', chunk)
            std['expiryDate'] = get_field('expiryDate', chunk)
            std['sourceUrl'] = get_field('sourceUrl', chunk)
            std['version'] = get_field('version', chunk)
            
            if std['id'] and std['name']:
                standards.append(std)
                
        return standards
    except Exception as e:
        print(f"Error parsing data.js: {e}")
        return []

def scrape_iec_page(url):
    """Scrapes IEC webstore using Selenium"""
    try:
        driver = get_selenium_driver()
        if not driver:
            return {'error': 'Selenium driver not available'}
            
        driver.get(url)
        time.sleep(3) # Wait for JS
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        data = {}
        
        lines = page_text.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if 'publication date' in line_lower:
                match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
                if match: data['publication_date'] = match.group(1)
            if 'stability date' in line_lower:
                match = re.search(r'(\d{4})', line)
                if match: data['stability_date'] = match.group(1)
            if line_lower.startswith('edition') and 'amended' not in line_lower:
                match = re.search(r'(\d+\.?\d*)', line)
                if match: data['edition'] = match.group(1)
                
        # Price scraping improvements
        price_found = None
        
        # 1. Try CSS selectors
        try:
            price_el = driver.find_element(By.CSS_SELECTOR, ".price-container .price, .product-price, span[itemprop='price']")
            if price_el:
                price_found = price_el.text.strip()
        except: pass
        
        # 2. Try XPath for CHF
        if not price_found:
            try:
                # Look for element containing CHF followed by digits
                price_el = driver.find_element(By.XPATH, "//*[contains(text(), 'CHF') and string-length(text()) < 20]")
                if price_el:
                    price_found = price_el.text.strip()
            except: pass
            
        # 3. Regex fallback on full text
        if not price_found:
            price_match = re.search(r'CHF\s*([\d,\']+\.?\-?)', page_text)
            if price_match:
                price_found = f"CHF {price_match.group(1)}"

        if price_found:
            # Clean up price string
            # Remove extra spaces
            price_found = re.sub(r'\s+', ' ', price_found)
            data['price'] = price_found
            
        return data
    except Exception as e:
        return {'error': str(e)}

def scrape_ieee_page(url):
    """Scrapes IEEE page (static)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return {'error': f"HTTP {response.status_code}"}
            
        soup = BeautifulSoup(response.content, 'html.parser')
        data = {'source': 'IEEE', 'accessible': True}
        
        title = soup.select_one('title')
        if title:
            title_text = title.get_text()
            match = re.search(r'IEEE\s+\d+[A-Za-z]*-(\d{4})', title_text)
            if match:
                data['version'] = match.group(1)
        return data
    except Exception as e:
        return {'error': str(e)}

def scrape_nema_store(url):
    """Scrapes NEMA store using Selenium (bypass 403)"""
    try:
        driver = get_selenium_driver()
        if not driver: return {'error': 'Selenium driver not available'}
        
        driver.get(url)
        time.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        data = {'source': 'NEMA Store', 'accessible': True}
        
        title = soup.select_one('h1, .product-title, title')
        if title:
            # 優先抓取 20xx 年份，避免抓到標準編號 (如 0339)
            match = re.search(r'(20\d{2})', title.get_text())
            if match: data['version'] = match.group(1)
            
        price_el = soup.select_one('.price, .product-price, [class*="price"]')
        if price_el:
            price_match = re.search(r'[\$€£]\s*[\d,]+\.?\d*', price_el.get_text(strip=True))
            if price_match: data['price'] = price_match.group(0)
            
        return data
    except Exception as e:
        return {'error': str(e)}

def scrape_bsi_knowledge(url):
    """Scrapes BSI Knowledge using Selenium"""
    try:
        driver = get_selenium_driver()
        if not driver: return {'error': 'Selenium driver not available'}
        
        driver.get(url)
        time.sleep(5)
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        data = {'source': 'BSI Knowledge', 'accessible': True}
        
        # Version from title
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        h1 = soup.select_one('h1')
        if h1:
            match = re.search(r':(\d{4})', h1.get_text(strip=True))
            if match: data['version'] = match.group(1)
            
        # Date
        date_match = re.search(r'Published[:\s]*(\d{1,2}\s+\w+\s+\d{4})', page_text)
        if date_match:
            try:
                dt = datetime.strptime(date_match.group(1), '%d %b %Y')
                data['publication_date'] = dt.strftime('%Y-%m-%d')
            except: pass
            
        # Price
        price_match = re.search(r'Non-Member\s*(?:Total)?\s*[£$€]\s*([\d,\.]+)', page_text)
        if price_match:
            data['price'] = f"£{price_match.group(1)}"
            
        if 'Withdrawn' in page_text:
            data['status'] = 'Withdrawn'
            
        return data
    except Exception as e:
        return {'error': str(e)}

def scrape_generic_page(url, standard_name):
    """Generic scraper"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        data = {
            'http_status': response.status_code,
            'accessible': response.status_code == 200,
            'final_url': response.url
        }
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()
            data['name_found'] = standard_name and standard_name.upper() in page_text.upper()
        return data
    except Exception as e:
        return {'error': str(e), 'accessible': False}

def scrape_smart_generic(url, standard_name):
    """
    智能通用爬蟲 - 自動識別版本/價格資訊
    適用於用戶自行新增的法規
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return {'error': f"HTTP {response.status_code}", 'accessible': False}
            
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()
        data = {'accessible': True, 'source': 'Smart Generic'}
        
        # 版本模式識別 (優先順序由高到低)
        version_patterns = [
            (r'Issue\s+(\d+)', 'Issue'),           # Telcordia: Issue 4
            (r'Edition\s+(\d+\.?\d*)', 'Ed.'),     # IEC: Edition 7.0
            (r'Version\s+(\d+\.?\d*)', 'Ver.'),    # Generic: Version 2.0
            (r'Rev\.?\s*(\d+)', 'Rev.'),           # Revision: Rev. 10
            (r':\s*(20\d{2})\b', ''),              # Year suffix: :2021
        ]
        
        for pattern, prefix in version_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                ver = match.group(1)
                data['version'] = f"{prefix} {ver}".strip() if prefix else ver
                data['edition'] = ver
                break
        
        # 嘗試抓取價格
        price_patterns = [
            r'[\$€£¥]\s*([\d,]+\.?\d*)',           # $99.00, €50, £100
            r'([\d,]+\.?\d*)\s*(?:USD|EUR|GBP)',   # 99.00 USD
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, page_text)
            if match:
                data['price'] = match.group(0)
                break
                
        return data
    except Exception as e:
        return {'error': str(e), 'accessible': False}

def verify_standard_logic(std, live_data):
    issues = []
    
    # Edition - 當網站有版本但本地沒有，或版本不相同時產生 issue
    if 'edition' in live_data:
        live_ed = re.search(r'([\d]+\.?\d*)', live_data['edition'])
        live_ed = live_ed.group(1) if live_ed else live_data['edition']
        
        local_ed = re.search(r'([\d]+\.?\d*)', std.get('version', ''))
        local_ed = local_ed.group(1) if local_ed else std.get('version', '')
        
        # 版本不符 (包括本地為空的情況)
        if live_ed and (not local_ed or live_ed != local_ed):
            issues.append(f"Edition: Local='{std.get('version') or '(empty)'}' vs Live='{live_data['edition']}'")

    # Date
    if 'publication_date' in live_data:
        if live_data['publication_date'] != std.get('effectiveDate'):
             issues.append(f"Date: Local='{std.get('effectiveDate')}' vs Live='{live_data['publication_date']}'")

    # Cost - 當網站有價格但本地沒有，或價格不相同時產生 issue
    if 'price' in live_data:
        live_price = re.sub(r'[^\d]', '', live_data['price'])
        local_price = re.sub(r'[^\d]', '', std.get('cost', ''))
        # 價格不符 (包括本地為空的情況)
        if live_price and (not local_price or live_price != local_price):
             issues.append(f"Cost: Local='{std.get('cost') or '(empty)'}' vs Live='{live_data['price']}'")

    # Stability
    if 'stability_date' in live_data:
        live_stab = live_data['stability_date']
        local_exp = std.get('expiryDate', '')
        if live_stab not in local_exp:
             issues.append(f"Stability: Local='{local_exp}' vs Live='{live_stab}'")
             
    return issues

def run_verification(base_path):
    """Main entry point for verification"""
    print("--- DQA Standard Verification Agent (Selenium) ---")
    data_file = os.path.join(base_path, 'data.js')
    standards = load_standards(data_file)
    print(f"Loaded {len(standards)} standards")
    
    json_results = []
    total = len(standards)
    
    for idx, std in enumerate(standards, start=1):
        url = std.get('sourceUrl')
        name = std.get('name')
        std_id = std.get('id', f'std-{idx}')
        
        result_entry = {
            'id': std_id, 'name': name, 'url': url or '',
            'status': 'OK', 'issues': []
        }
        
        if not url or '/search/' in url:
            result_entry['status'] = 'SKIPPED'
            json_results.append(result_entry)
            print(f"[{idx}/{total}] {name} - Skipped")
            continue
            
        print(f"[{idx}/{total}] Checking {name}...", end=" ", flush=True)
        
        live_data = {}
        if 'webstore.iec.ch' in url:
            live_data = scrape_iec_page(url)
            if 'error' not in live_data:
                issues = verify_standard_logic(std, live_data)
                if issues:
                    result_entry['status'] = 'MISMATCH'
                    result_entry['issues'] = issues
                    print("MISMATCH")
                else:
                    print("OK")
            else:
                result_entry['status'] = 'ERROR'
                result_entry['issues'] = [live_data['error']]
                print(f"ERROR: {live_data['error']}")
                
        elif 'ieee.org' in url:
            live_data = scrape_ieee_page(url)
            if 'error' not in live_data and live_data.get('accessible'):
                print(f"OK (Version: {live_data.get('version', 'N/A')})")
            else:
                result_entry['status'] = 'WARNING'
                print("WARNING")
                
        elif 'store.accuristech.com' in url: # NEMA/DNV
            live_data = scrape_nema_store(url)
            if 'error' not in live_data and live_data.get('accessible'):
                # Simple version check
                ver = live_data.get('version')
                if ver and ver not in std.get('version', ''):
                    result_entry['status'] = 'MISMATCH'
                    result_entry['issues'] = [f"Edition: Local='{std.get('version', '')}' vs Live='{ver}'"]
                    print(f"MISMATCH (Live {ver})")
                else:
                    print("OK")
            else:
                result_entry['status'] = 'ERROR'
                result_entry['issues'] = [live_data.get('error', 'Unknown error')]
                print("ERROR")
                
        elif 'bsigroup.com' in url:
            live_data = scrape_bsi_knowledge(url)
            if 'error' not in live_data and live_data.get('accessible'):
                 # Simple check
                 if live_data.get('status') == 'Withdrawn':
                     result_entry['status'] = 'MISMATCH'
                     result_entry['issues'] = ['Standard Withdrawn']
                     print("WITHDRAWN")
                 else:
                     print("OK")
            else:
                result_entry['status'] = 'ERROR'
                print("ERROR")
        else:
            # 使用智能通用爬蟲
            live_data = scrape_smart_generic(url, name)
            if live_data.get('accessible'):
                # 版本比對
                ver = live_data.get('version')
                if ver:
                    local_ver = std.get('version', '')
                    # 提取版本號進行比對
                    live_num = re.search(r'(\d+)', str(ver))
                    local_num = re.search(r'(\d+)', str(local_ver))
                    live_num = live_num.group(1) if live_num else ''
                    local_num = local_num.group(1) if local_num else ''
                    
                    if live_num and local_num and live_num != local_num:
                        result_entry['status'] = 'MISMATCH'
                        result_entry['issues'] = [f"Version: Local='{local_ver}' vs Live='{ver}'"]
                        print(f"MISMATCH (Local: {local_ver}, Live: {ver})")
                    elif live_num and not local_num:
                        result_entry['status'] = 'UPDATE'
                        result_entry['issues'] = [f"Found version: {ver}"]
                        print(f"OK (Found: {ver})")
                    else:
                        print(f"OK (Version: {ver})")
                else:
                    print("OK (Accessible)")
            else:
                result_entry['status'] = 'WARNING'
                print("WARNING")
                
        json_results.append(result_entry)
        
    # Save report
    json_report = {
        'timestamp': datetime.now().isoformat(),
        'results': json_results
    }
    report_path = os.path.join(base_path, 'verification_results.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)
        
    close_selenium_driver()
    return {'status': 'success', 'message': 'Verification complete'}

if __name__ == "__main__":
    run_verification(".")
