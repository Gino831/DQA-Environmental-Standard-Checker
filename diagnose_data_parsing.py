"""
診斷 load_standards 函式為何無法正確解析 data.js
"""
import re

# 讀取 data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()

print("=== data.js 解析診斷 ===")
print(f"檔案大小: {len(content)} 字元")

# 移除註解
content = re.sub(r'(?m)^\s*//.*', '', content)

# 分割
chunks = content.split('{')
print(f"找到 {len(chunks)} 個區塊")

# 嘗試解析第一個標準
for i, chunk in enumerate(chunks):
    if 'id' not in chunk:
        continue
    
    print(f"\n=== 測試區塊 {i} ===")
    print(f"區塊前 300 字元:")
    print(chunk[:300])
    
    # 這是 verify_standards.py 使用的模式
    pattern1 = r"id:\s*['\"](.+?)['\"]"
    match1 = re.search(pattern1, chunk)
    print(f"\n模式 'id:' 搭配單/雙引號: {match1}")
    
    # 因為 data.js 使用雙引號作為 key
    pattern2 = r'"id"\s*:\s*"(.+?)"'
    match2 = re.search(pattern2, chunk)
    print(f"模式 '\"id\"' 搭配雙引號: {'找到: ' + match2.group(1) if match2 else '未找到'}")
    
    break

print("\n=== 結論 ===")
print("data.js 使用的是 JSON 格式（雙引號包圍 key），但 verify_standards.py 的正則表達式預期的是 JavaScript 物件字面量格式（key 不需要引號）")
