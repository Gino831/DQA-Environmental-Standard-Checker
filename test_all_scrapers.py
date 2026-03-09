"""
爬蟲功能整合測試腳本
測試所有爬蟲模組是否正常運作
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from verify_standards import (
    scrape_iec_page,
    scrape_ieee_page,
    scrape_nema_store,
    scrape_bsi_knowledge,
    scrape_smart_generic,
    selenium_driver
)
import json


def print_result(name, data):
    """格式化輸出測試結果"""
    print(f"\n{'='*60}")
    print(f"📋 {name}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if 'error' in data:
        print(f"❌ 狀態: 錯誤")
    else:
        print(f"✅ 狀態: 成功")


def main():
    print("🚀 開始爬蟲功能測試")
    print("="*60)

    results = {}

    # Use the context manager for Selenium driver
    with selenium_driver() as driver:
        if driver is None:
            print("[WARN] Selenium driver failed to initialize.")

        # 1. 測試 IEC 爬蟲
        print("\n\n🔍 測試 1/5: IEC 爬蟲 (webstore.iec.ch)")
        iec_url = "https://webstore.iec.ch/en/publication/5395"  # IEC 61373
        print(f"URL: {iec_url}")
        try:
            data = scrape_iec_page(iec_url, driver)
            print_result("IEC 61373", data)
            results['IEC'] = '成功' if 'error' not in data else f"失敗: {data['error']}"
        except Exception as e:
            print(f"❌ IEC 爬蟲失敗: {e}")
            results['IEC'] = f"例外: {e}"

        # 2. 測試 IEEE 爬蟲
        print("\n\n🔍 測試 2/5: IEEE 爬蟲 (ieee.org)")
        ieee_url = "https://standards.ieee.org/ieee/1613/10817/"  # IEEE 1613
        print(f"URL: {ieee_url}")
        try:
            data = scrape_ieee_page(ieee_url)
            print_result("IEEE 1613", data)
            results['IEEE'] = '成功' if 'error' not in data else f"失敗: {data['error']}"
        except Exception as e:
            print(f"❌ IEEE 爬蟲失敗: {e}")
            results['IEEE'] = f"例外: {e}"

        # 3. 測試 NEMA 爬蟲
        print("\n\n🔍 測試 3/5: NEMA Store 爬蟲 (store.accuristech.com)")
        nema_url = "https://store.accuristech.com/standards/nema-ics-1-1?product_id=2001986"
        print(f"URL: {nema_url}")
        try:
            data = scrape_nema_store(nema_url, driver)
            print_result("NEMA ICS 1-1", data)
            results['NEMA'] = '成功' if 'error' not in data else f"失敗: {data['error']}"
        except Exception as e:
            print(f"❌ NEMA 爬蟲失敗: {e}")
            results['NEMA'] = f"例外: {e}"

        # 4. 測試 BSI Knowledge 爬蟲
        print("\n\n🔍 測試 4/5: BSI Knowledge 爬蟲 (bsigroup.com)")
        bsi_url = "https://knowledge.bsigroup.com/products/railway-applications-rolling-stock-equipment-electronic-equipment-used-on-rolling-stock/standard"
        print(f"URL: {bsi_url}")
        try:
            data = scrape_bsi_knowledge(bsi_url, driver)
            print_result("EN 50155", data)
            results['BSI'] = '成功' if 'error' not in data else f"失敗: {data['error']}"
        except Exception as e:
            print(f"❌ BSI 爬蟲失敗: {e}")
            results['BSI'] = f"例外: {e}"

        # 5. 測試通用爬蟲
        print("\n\n🔍 測試 5/5: 通用爬蟲 (Generic)")
        generic_url = "https://www.dnv.com/rules-standards/"
        print(f"URL: {generic_url}")
        try:
            data = scrape_smart_generic(generic_url, "DNV")
            print_result("DNV 通用頁面", data)
            results['Generic'] = '成功' if 'error' not in data else f"失敗: {data['error']}"
        except Exception as e:
            print(f"❌ 通用爬蟲失敗: {e}")
            results['Generic'] = f"例外: {e}"

    # 輸出總結
    print("\n\n")
    print("="*60)
    print("📊 測試結果總結")
    print("="*60)
    for scraper, status in results.items():
        icon = "✅" if "成功" in status else "❌"
        print(f"  {icon} {scraper}: {status}")

    print("\n✅ 爬蟲測試完成！")


if __name__ == "__main__":
    main()
