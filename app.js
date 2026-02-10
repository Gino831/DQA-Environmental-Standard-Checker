
// State
let standards = [];
let categoryOrder = JSON.parse(localStorage.getItem('dqa_category_order')) ||
    ['MOXA Standard', 'Marine Standard', 'Railway Standard', 'Power Station', 'Other'];
let subcategoryOrder = JSON.parse(localStorage.getItem('dqa_subcategory_order')) ||
    ['溫度類', '濕度類', '鹽霧類', '高空類', '機構類', '包裝類', '防護類', '船舶標準', '鐵路標準', '電廠標準', '其他'];


// 子分類定義 - 用於按測試類型分組顯示
const SUBCATEGORY_MAP = {
    'temperature-low': { name: '溫度類', icon: '🌡️', order: 1 },
    'temperature-high': { name: '溫度類', icon: '🌡️', order: 1 },
    'temperature-cyclic': { name: '溫度類', icon: '🌡️', order: 1 },
    'humidity': { name: '濕度類', icon: '💧', order: 2 },
    'salt-mist': { name: '鹽霧類', icon: '🧂', order: 3 },
    'pressure': { name: '高空類', icon: '🏔️', order: 4 },
    'vibration': { name: '機構類', icon: '🔧', order: 5 },
    'shock': { name: '機構類', icon: '🔧', order: 5 },
    'packaging': { name: '包裝類', icon: '📦', order: 6 },
    'ip-protection': { name: '防護類', icon: '🛡️', order: 7 },
    'marine': { name: '船舶標準', icon: '🚢', order: 8 },
    'railway': { name: '鐵路標準', icon: '🚃', order: 9 },
    'emc': { name: '電廠標準', icon: '⚡', order: 10 }
};

// 取得子分類資訊
function getSubcategory(stressType) {
    return SUBCATEGORY_MAP[stressType] || { name: '其他', icon: '📋', order: 99 };
}


// 同步資料到 data.js 的通用函數
async function syncToDataJs(standardsData, actionMessage) {
    try {
        const syncResponse = await fetch('/api/sync-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(standardsData)
        });
        const syncResult = await syncResponse.json();
        if (syncResult.status === 'success') {
            console.log(`[SYNC] data.js 已同步: ${actionMessage}`);
        } else {
            console.warn('[SYNC] 同步失敗:', syncResult.message);
            alert(`${actionMessage}，但同步到 data.js 失敗: ${syncResult.message}`);
        }
    } catch (syncError) {
        console.warn('[SYNC] 無法同步到 data.js:', syncError);
        // 靜默失敗，資料已保存在 localStorage
    }
}

// Apply Updates Function - used by Update All button
function applyUpdates(updates) {
    updates.forEach(update => {
        const idx = standards.findIndex(s => s.id === update.id);
        if (idx !== -1) {
            // Update existing standard
            if (update.newVersion) standards[idx].version = update.newVersion;
            if (update.newEffective) standards[idx].effectiveDate = update.newEffective;
            if (update.newCost) standards[idx].cost = update.newCost;
            if (update.newExpiry) standards[idx].expiryDate = update.newExpiry;
            if (update.newSummary) standards[idx].revisionSummary = update.newSummary;
            if (update.newSourceUrl) standards[idx].sourceUrl = update.newSourceUrl;
            console.log(`Updated: ${update.name}`);
        }
    });

    // Save to localStorage
    localStorage.setItem('dqa_standards', JSON.stringify(standards));

    // Close modal and refresh
    const updatesModal = document.getElementById('updates-modal');
    if (updatesModal) {
        updatesModal.classList.remove('active');
        setTimeout(() => updatesModal.classList.add('hidden'), 200);
    }

    // Refresh the table
    if (typeof renderStandards === 'function') {
        renderStandards();
    }

    alert(`成功更新 ${updates.length} 項標準！`);
}

// CSV Parser Helper
function parseCSV(csvText) {
    const lines = csvText.split(/\r?\n/);
    if (lines.length < 2) return [];

    const headers = lines[0].split(',').map(h => h.trim());
    const result = [];

    for (let i = 1; i < lines.length; i++) {
        if (!lines[i].trim()) continue;

        const obj = {};
        let currentLine = lines[i];

        // Handle quoted fields containing commas
        const row = [];
        let inQuote = false;
        let field = '';

        for (let j = 0; j < currentLine.length; j++) {
            const char = currentLine[j];
            if (char === '"') {
                inQuote = !inQuote;
            } else if (char === ',' && !inQuote) {
                row.push(field);
                field = '';
            } else {
                field += char;
            }
        }
        row.push(field); // Last field

        // Map to headers
        headers.forEach((header, index) => {
            if (index < row.length) {
                // Remove surrounding quotes if present
                let value = row[index].trim();
                if (value.startsWith('"') && value.endsWith('"')) {
                    value = value.substring(1, value.length - 1);
                }
                // Unescape double quotes
                value = value.replace(/""/g, '"');
                obj[header] = value;
            }
        });

        if (obj.id) result.push(obj);
    }

    // Deduplicate based on Name (case-insensitive)
    const uniqueResult = [];
    const seenNames = new Set();

    result.forEach(std => {
        const normalizedName = std.name ? std.name.trim().toUpperCase() : '';
        if (normalizedName && !seenNames.has(normalizedName)) {
            seenNames.add(normalizedName);
            uniqueResult.push(std);
        }
    });

    return uniqueResult;
}

async function loadStandards() {
    // 1. Try to load from Google Sheets
    if (typeof config !== 'undefined' && config.googleSheetCsvUrl) {
        try {
            console.log('Fetching from Google Sheets...');
            const response = await fetch(config.googleSheetCsvUrl);
            if (response.ok) {
                const csvText = await response.text();
                const fetchedStandards = parseCSV(csvText);
                if (fetchedStandards.length > 0) {
                    console.log('Loaded from Google Sheets:', fetchedStandards.length);
                    standards = fetchedStandards;
                    localStorage.setItem('dqa_standards', JSON.stringify(standards));
                    if (typeof renderStandards === 'function') renderStandards();
                    return;
                }
            }
        } catch (e) {
            console.error('Failed to fetch from Google Sheets:', e);
        }
    }

    // 2. Fallback to LocalStorage
    const stored = localStorage.getItem('dqa_standards');
    if (stored) {
        console.log('Loaded from LocalStorage');
        standards = JSON.parse(stored);
    }
    // 3. Fallback to initialStandards (from data.js)
    else if (typeof initialStandards !== 'undefined') {
        console.log('Loaded from initialStandards');
        standards = [...initialStandards];
    }

    if (typeof renderStandards === 'function') renderStandards();
}

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const standardsList = document.getElementById('standards-list'); // This is now the <tbody>
    const searchInput = document.getElementById('search-input');
    const addBtn = document.getElementById('add-btn');
    const addModal = document.getElementById('add-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const cancelBtn = document.getElementById('cancel-btn');
    const addForm = document.getElementById('add-form');
    const stdCategorySelect = document.getElementById('std-category-select');
    const stdCategoryCustom = document.getElementById('std-category-custom');
    const resetDataBtn = document.getElementById('reset-data-btn');

    // Dashboard Elements
    const expiringCountEl = document.getElementById('expiring-count');
    const totalCostEl = document.getElementById('total-cost');
    const checkUpdatesBtn = document.getElementById('check-updates-btn');
    const updatesModal = document.getElementById('updates-modal');
    const closeUpdatesModalBtn = document.getElementById('close-updates-modal');
    const closeUpdatesBtn = document.getElementById('close-updates-btn');
    const updatesList = document.getElementById('updates-list');

    // Details Modal Elements
    const detailsModal = document.getElementById('details-modal');
    const closeDetailsModalBtn = document.getElementById('close-details-modal');
    const closeDetailsBtn = document.getElementById('close-details-btn');
    const detailsContent = document.getElementById('details-content');

    // Reset Data Button Handler
    if (resetDataBtn) {
        resetDataBtn.addEventListener('click', () => {
            if (confirm('確定要重置所有資料嗎？這將清除您所有的修改並從 data.js 重新載入完整的法規清單。')) {
                localStorage.removeItem('dqa_standards');
                if (typeof initialStandards !== 'undefined') {
                    standards = [...initialStandards];
                    console.log(`Reset complete: Loaded ${standards.length} standards from data.js`);
                    renderStandards();
                    alert(`已成功重置！共載入 ${standards.length} 項法規標準。`);
                } else {
                    alert('錯誤：無法找到 initialStandards。請確認 data.js 已正確載入。');
                }
            }
        });
    }

    // Helper Functions
    function formatDate(dateString) {
        if (!dateString) return '-';
        // Check if it's a stability date string like "2027 (Stability)"
        if (dateString.includes('Stability')) {
            // Extract only the year
            const yearMatch = dateString.match(/\d{4}/);
            return yearMatch ? yearMatch[0] : dateString;
        }
        // Otherwise try to format as a date
        const date = new Date(dateString);
        if (isNaN(date.getTime())) {
            // Try to extract year if present
            const yearMatch = dateString.match(/\d{4}/);
            return yearMatch ? yearMatch[0] : dateString;
        }
        // Return full date format (YYYY/M/D) for effective dates
        return date.toLocaleDateString('zh-TW');
    }

    function isExpired(expiryDateString) {
        if (!expiryDateString) return false;

        // Handle Stability Dates
        if (expiryDateString.includes('Stability')) {
            // Extract year, e.g. "2027 (Stability)" -> 2027
            const yearMatch = expiryDateString.match(/\d{4}/);
            if (yearMatch) {
                const expiryYear = parseInt(yearMatch[0]);
                const currentYear = new Date().getFullYear();
                // If current year is greater than stability year, consider it "expired" (or needing review)
                // Or if we want to be strict: > stability year
                return currentYear > expiryYear;
            }
            return false;
        }

        const today = new Date();
        const expiry = new Date(expiryDateString);
        if (isNaN(expiry.getTime())) return false;

        return today > expiry;
    }

    // Check if expiring THIS YEAR (or already expired)
    function isExpiringThisYear(expiryDateString) {
        if (!expiryDateString) return false;
        const currentYear = new Date().getFullYear();

        if (expiryDateString.includes('Stability')) {
            const yearMatch = expiryDateString.match(/\d{4}/);
            if (yearMatch) {
                const expiryYear = parseInt(yearMatch[0]);
                return expiryYear <= currentYear;
            }
        } else {
            const expiry = new Date(expiryDateString);
            if (!isNaN(expiry.getTime())) {
                return expiry.getFullYear() <= currentYear;
            }
        }
        return false;
    }

    function getSearchUrl(standardName) {
        const name = standardName.trim().toUpperCase();

        // Use Google search for all standards to ensure reliable results
        if (name.startsWith('IEC')) {
            return `https://www.google.com/search?q=${encodeURIComponent(standardName + ' IEC webstore')}`;
        } else if (name.startsWith('ISO')) {
            return `https://www.google.com/search?q=${encodeURIComponent(standardName + ' ISO standard')}`;
        } else if (name.startsWith('IEEE')) {
            return `https://www.google.com/search?q=${encodeURIComponent(standardName + ' IEEE standard')}`;
        } else if (name.startsWith('EN')) {
            return `https://www.google.com/search?q=${encodeURIComponent(standardName + ' EN standard latest version')}`;
        } else if (name.startsWith('NEMA')) {
            return `https://www.google.com/search?q=${encodeURIComponent(standardName + ' standard')}`;
        } else if (name.includes('MOXA')) {
            return `https://www.google.com/search?q=${encodeURIComponent(standardName + ' standard')}`;
        } else {
            return `https://www.google.com/search?q=${encodeURIComponent(standardName + ' standard latest version')}`;
        }
    }

    function parseCost(costString) {
        if (!costString) return 0;
        // Remove currency symbol and parse number
        const num = parseFloat(costString.replace(/[^0-9.]/g, ''));
        return isNaN(num) ? 0 : num;
    }

    function updateDashboard() {
        let count = 0;
        let totalCostTWD = 0;

        // Exchange rates (2026-01-08)
        const RATES = {
            CHF: 39.60,
            USD: 31.47,
            GBP: 39.80  // Added GBP for EN 50155 (BSI Knowledge)
        };

        standards.forEach(std => {
            if (isExpiringThisYear(std.expiryDate)) {
                count++;

                const costStr = std.cost || '';
                let costInTWD = 0;

                // Parse cost based on currency
                const val = parseFloat(costStr.replace(/[^\d.]/g, '')) || 0;

                if (costStr.includes('£') || costStr.includes('GBP')) {
                    costInTWD = val * RATES.GBP;
                } else if (costStr.includes('USD') || costStr.includes('$')) {
                    costInTWD = val * RATES.USD;
                } else if (costStr.toLowerCase().includes('free')) {
                    costInTWD = 0;
                } else {
                    // Default to CHF (most common in IEC) if no specific currency or explicitly CHF
                    costInTWD = val * RATES.CHF;
                }

                totalCostTWD += costInTWD;
            }
        });

        if (expiringCountEl) expiringCountEl.textContent = count;
        if (totalCostEl) {
            // Format as NT$ X,XXX
            const formattedCost = Math.round(totalCostTWD).toLocaleString();
            totalCostEl.textContent = `NT$ ${formattedCost} (Est.)`;
        }
    }

    function showStandardDetails(std) {
        const expired = isExpired(std.expiryDate);
        const statusClass = expired ? 'status-expired' : 'status-valid';
        const statusText = expired ? 'Expired' : 'Valid';
        const revisionSummary = std.revisionSummary || 'No revision summary available.';
        const searchUrl = getSearchUrl(std.name);

        detailsContent.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
                <div>
                    <span class="detail-label">Standard ID</span>
                    <div class="detail-value">${std.name}</div>
                </div>
                <div>
                    <span class="detail-label">Version</span>
                    <div class="detail-value">${std.version || '-'}</div>
                </div>
                <div>
                    <span class="detail-label">Effective Date</span>
                    <div class="detail-value">${formatDate(std.effectiveDate)}</div>
                </div>
                <div>
                    <span class="detail-label">Expiry / Stability</span>
                    <div class="detail-value">${formatDate(std.expiryDate)}</div>
                </div>
                <div>
                    <span class="detail-label">Cost</span>
                    <div class="detail-value">${std.cost || '-'}</div>
                </div>
                <div>
                    <span class="detail-label">Category</span>
                    <div class="detail-value">${std.category || '-'}</div>
                </div>
            </div>

            <div style="margin-bottom: 1.5rem;">
                <span class="detail-label">Description</span>
                <div class="detail-value">${std.description || '-'}</div>
            </div>

            <div style="margin-bottom: 1.5rem;">
                <span class="detail-label">Revision Summary</span>
                <div class="detail-value" style="background: rgba(0,0,0,0.03); padding: 0.75rem; border-radius: 6px;">
                    ${revisionSummary}
                </div>
            </div>

            <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--glass-border); text-align: center;">
                 <p style="margin-bottom: 1rem; color: var(--text-secondary); font-size: 0.9rem;">
                    Please verify details on the official website
                </p>
                <a href="${searchUrl}" target="_blank" class="btn-primary" style="display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none; background: var(--accent-color); color: white; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 500;">
                    <i data-lucide="globe"></i> Verify on Official Website
                </a>
            </div>
        `;

        detailsModal.classList.remove('hidden');
        setTimeout(() => detailsModal.classList.add('active'), 10);
        lucide.createIcons();
    }

    const selectedStandards = new Set();
    const selectAllCheckbox = document.getElementById('select-all');

    // Expose renderStandards to global scope or use it inside loadStandards
    window.renderStandards = function (filterText = '') {
        standardsList.innerHTML = '';

        // Normalize text for better search matching
        const normalizeText = (text) => {
            if (!text) return '';
            return text.toLowerCase().replace(/[\s\-_]/g, '');
        };

        const normalizedFilter = normalizeText(filterText);

        const filtered = standards.filter(std => {
            const normalizedName = normalizeText(std.name);
            const normalizedDesc = normalizeText(std.description);
            const normalizedCategory = normalizeText(std.category);
            const normalizedSubcat = normalizeText(getSubcategory(std.stressType).name);

            return normalizedName.includes(normalizedFilter) ||
                normalizedDesc.includes(normalizedFilter) ||
                normalizedCategory.includes(normalizedFilter) ||
                normalizedSubcat.includes(normalizedFilter);
        });

        // 雙層分組：先按 Category，再按子分類
        const grouped = {};
        filtered.forEach(std => {
            const category = std.category || 'Other';
            const subcat = getSubcategory(std.stressType);
            const subcatKey = subcat.name;

            if (!grouped[category]) grouped[category] = {};
            if (!grouped[category][subcatKey]) {
                grouped[category][subcatKey] = {
                    items: [],
                    icon: subcat.icon,
                    order: subcat.order
                };
            }
            grouped[category][subcatKey].items.push(std);
        });

        // 使用動態 categoryOrder，並確保包含所有現有的 category
        const existingCategories = Object.keys(grouped);
        const allCategories = [...categoryOrder];
        existingCategories.forEach(cat => {
            if (!allCategories.includes(cat)) allCategories.push(cat);
        });
        const groupOrder = allCategories.filter(cat => grouped[cat]);

        // Render Rows
        groupOrder.forEach((categoryKey, catIdx) => {
            if (grouped[categoryKey]) {
                const isFirstCat = catIdx === 0;
                const isLastCat = catIdx === groupOrder.length - 1;

                // Category Header with move buttons
                const categoryHeaderRow = document.createElement('tr');
                categoryHeaderRow.className = 'category-header';
                categoryHeaderRow.innerHTML = `
                    <td colspan="10">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <span>${categoryKey}</span>
                            <div style="display: flex; gap: 0.25rem;">
                                <button class="btn-icon cat-move-up-btn" data-category="${categoryKey}" title="類別上移" style="opacity: ${isFirstCat ? '0.3' : '1'}; cursor: ${isFirstCat ? 'not-allowed' : 'pointer'};" ${isFirstCat ? 'disabled' : ''}>
                                    <i data-lucide="chevron-up" style="width: 16px; height: 16px;"></i>
                                </button>
                                <button class="btn-icon cat-move-down-btn" data-category="${categoryKey}" title="類別下移" style="opacity: ${isLastCat ? '0.3' : '1'}; cursor: ${isLastCat ? 'not-allowed' : 'pointer'};" ${isLastCat ? 'disabled' : ''}>
                                    <i data-lucide="chevron-down" style="width: 16px; height: 16px;"></i>
                                </button>
                            </div>
                        </div>
                    </td>`;
                standardsList.appendChild(categoryHeaderRow);

                // 按動態 subcategoryOrder 排序子分類
                const subcatKeys = Object.keys(grouped[categoryKey]).sort((a, b) => {
                    const orderA = subcategoryOrder.indexOf(a);
                    const orderB = subcategoryOrder.indexOf(b);
                    // 如果不在 subcategoryOrder 中，放到最後
                    return (orderA === -1 ? 999 : orderA) - (orderB === -1 ? 999 : orderB);
                });

                subcatKeys.forEach((subcatKey, subcatIdx) => {
                    const subcatData = grouped[categoryKey][subcatKey];
                    const subcatItems = subcatData.items;
                    const isFirstSubcat = subcatIdx === 0;
                    const isLastSubcat = subcatIdx === subcatKeys.length - 1;

                    // Subcategory Header with move buttons
                    const subcatHeaderRow = document.createElement('tr');
                    subcatHeaderRow.className = 'subcategory-header';
                    subcatHeaderRow.innerHTML = `
                        <td colspan="10">
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-left: 1.5rem;">
                                <span>${subcatData.icon} ${subcatKey}</span>
                                <div style="display: flex; gap: 0.25rem;">
                                    <button class="btn-icon subcat-move-up-btn" data-subcat="${subcatKey}" data-category="${categoryKey}" title="子分類上移" style="opacity: ${isFirstSubcat ? '0.3' : '1'}; cursor: ${isFirstSubcat ? 'not-allowed' : 'pointer'};" ${isFirstSubcat ? 'disabled' : ''}>
                                        <i data-lucide="chevron-up" style="width: 14px; height: 14px;"></i>
                                    </button>
                                    <button class="btn-icon subcat-move-down-btn" data-subcat="${subcatKey}" data-category="${categoryKey}" title="子分類下移" style="opacity: ${isLastSubcat ? '0.3' : '1'}; cursor: ${isLastSubcat ? 'not-allowed' : 'pointer'};" ${isLastSubcat ? 'disabled' : ''}>
                                        <i data-lucide="chevron-down" style="width: 14px; height: 14px;"></i>
                                    </button>
                                </div>
                            </div>
                        </td>`;
                    standardsList.appendChild(subcatHeaderRow);

                    // Standard Rows
                    subcatItems.forEach((std, idx) => {
                        const expired = isExpired(std.expiryDate);
                        const expiringThisYear = isExpiringThisYear(std.expiryDate);
                        const statusClass = expired ? 'status-expired' : 'status-valid';
                        const statusText = expired ? 'Expired' : 'Valid';
                        const isSelected = selectedStandards.has(std.id);

                        // 判斷是否為同子分類內的第一個/最後一個
                        const isFirst = idx === 0;
                        const isLast = idx === subcatItems.length - 1;

                        // Add special class for rows expiring this year
                        const rowClass = expiringThisYear ? 'expiring-row' : '';

                        const row = document.createElement('tr');
                        row.className = rowClass;

                        // 今年到期標籤
                        const expiringBadge = expiringThisYear && !expired ? '<span class="expiring-badge">今年到期</span>' : '';

                        row.innerHTML = `
                            <td style="font-weight: 500; color: var(--text-primary);">
                                ${std.name}${expiringBadge}
                                <a href="${getSearchUrl(std.name)}" target="_blank" class="direct-search-link" title="Verify on Official Website">
                                    <i data-lucide="external-link" style="width: 12px; height: 12px; margin-left: 4px; color: var(--primary);"></i>
                                </a>
                            </td>
                            <td>${std.description}</td>
                            <td class="revision-cell"><div class="revision-content">${std.revisionSummary || '-'}</div></td>
                            <td>${std.version || '-'}</td>
                            <td>${formatDate(std.effectiveDate)}</td>
                            <td>${formatDate(std.expiryDate)}</td>
                            <td>${std.cost || '-'}</td>
                            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                            <td>
                                <div style="display: flex; gap: 0.25rem; flex-wrap: nowrap;">
                                    <button class="btn-icon move-up-btn" data-id="${std.id}" title="上移" style="color: var(--text-secondary); opacity: ${isFirst ? '0.3' : '1'}; cursor: ${isFirst ? 'not-allowed' : 'pointer'};" ${isFirst ? 'disabled' : ''}>
                                        <i data-lucide="chevron-up" style="width: 14px; height: 14px;"></i>
                                    </button>
                                    <button class="btn-icon move-down-btn" data-id="${std.id}" title="下移" style="color: var(--text-secondary); opacity: ${isLast ? '0.3' : '1'}; cursor: ${isLast ? 'not-allowed' : 'pointer'};" ${isLast ? 'disabled' : ''}>
                                        <i data-lucide="chevron-down" style="width: 14px; height: 14px;"></i>
                                    </button>
                                    <button class="btn-query check-details-btn" data-id="${std.id}" title="Check Details">
                                        <i data-lucide="check-circle" style="width: 14px; height: 14px;"></i>
                                    </button>
                                    <button class="btn-icon edit-btn" data-id="${std.id}" title="Edit" style="color: var(--text-secondary);">
                                        <i data-lucide="edit-2" style="width: 14px; height: 14px;"></i>
                                    </button>
                                    <button class="btn-icon delete-btn" data-id="${std.id}" title="Delete" style="color: var(--error);">
                                        <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                                    </button>
                                </div>
                            </td>
                        `;
                        standardsList.appendChild(row);
                    });
                });
            }
        });

        // Add Event Listeners to new buttons
        document.querySelectorAll('.check-details-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const stdId = e.currentTarget.getAttribute('data-id');
                const std = standards.find(s => s.id === stdId);
                if (std) showStandardDetails(std);
            });
        });

        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const stdId = e.currentTarget.getAttribute('data-id');
                editStandard(stdId);
            });
        });

        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const stdId = e.currentTarget.getAttribute('data-id');
                deleteStandard(stdId);
            });
        });

        // 移動按鈕事件監聽器
        document.querySelectorAll('.move-up-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const stdId = e.currentTarget.getAttribute('data-id');
                moveStandard(stdId, 'up');
            });
        });

        document.querySelectorAll('.move-down-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const stdId = e.currentTarget.getAttribute('data-id');
                moveStandard(stdId, 'down');
            });
        });

        // Category 移動按鈕事件監聽器
        document.querySelectorAll('.cat-move-up-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const category = e.currentTarget.getAttribute('data-category');
                moveCategory(category, 'up');
            });
        });

        document.querySelectorAll('.cat-move-down-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const category = e.currentTarget.getAttribute('data-category');
                moveCategory(category, 'down');
            });
        });

        // 子分類移動按鈕事件監聽器
        document.querySelectorAll('.subcat-move-up-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const subcat = e.currentTarget.getAttribute('data-subcat');
                moveSubcategory(subcat, 'up');
            });
        });

        document.querySelectorAll('.subcat-move-down-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const subcat = e.currentTarget.getAttribute('data-subcat');
                moveSubcategory(subcat, 'down');
            });
        });

        // Add Event Listeners to Checkboxes
        document.querySelectorAll('.std-checkbox').forEach(cb => {
            cb.addEventListener('change', (e) => {
                const id = e.target.getAttribute('data-id');
                if (e.target.checked) {
                    selectedStandards.add(id);
                } else {
                    selectedStandards.delete(id);
                }

                // Update Select All state
                const allCheckboxes = document.querySelectorAll('.std-checkbox');
                const allChecked = Array.from(allCheckboxes).every(c => c.checked);
                if (selectAllCheckbox) selectAllCheckbox.checked = allChecked;
            });
        });

        // Re-initialize icons
        lucide.createIcons();
        updateDashboard();
    };

    // Edit Standard Function
    window.editStandard = function (id) {
        const std = standards.find(s => s.id === id);
        if (!std) return;

        // Populate form
        document.getElementById('std-id').value = std.id;
        document.getElementById('std-name').value = std.name;
        document.getElementById('std-desc').value = std.description || '';
        document.getElementById('std-version').value = std.version || '';
        document.getElementById('std-cost').value = std.cost || '';
        document.getElementById('std-effective').value = std.effectiveDate || '';
        document.getElementById('std-expiry').value = std.expiryDate || '';
        document.getElementById('std-source-url').value = std.sourceUrl || '';

        // Handle Category
        const categorySelect = document.getElementById('std-category-select');
        const customInput = document.getElementById('std-category-custom');

        // Check if category exists in options
        const options = Array.from(categorySelect.options).map(o => o.value);
        if (options.includes(std.category)) {
            categorySelect.value = std.category;
            customInput.style.display = 'none';
        } else {
            categorySelect.value = 'Other';
            customInput.style.display = 'block';
            customInput.value = std.category;
        }

        // Update Modal Title
        document.getElementById('modal-title').textContent = 'Edit Standard';

        // Show Modal
        addModal.classList.remove('hidden');
        setTimeout(() => addModal.classList.add('active'), 10);
    };

    // Delete Standard Function - 使用自訂 AlertDialog
    let pendingDeleteId = null;
    const deleteConfirmModal = document.getElementById('delete-confirm-modal');
    const deleteConfirmBtn = document.getElementById('delete-confirm-btn');
    const deleteCancelBtn = document.getElementById('delete-cancel-btn');

    // 開啟刪除確認對話框
    window.deleteStandard = function (id) {
        pendingDeleteId = id;
        deleteConfirmModal.classList.remove('hidden');
        setTimeout(() => deleteConfirmModal.classList.add('active'), 10);
    };

    // 確認刪除
    if (deleteConfirmBtn) {
        deleteConfirmBtn.addEventListener('click', () => {
            if (pendingDeleteId) {
                standards = standards.filter(s => s.id !== pendingDeleteId);
                localStorage.setItem('dqa_standards', JSON.stringify(standards));
                renderStandards(searchInput.value);

                // 即時同步到 data.js
                syncToDataJs(standards, '法規已刪除');
            }
            closeDeleteModal();
        });
    }

    // 取消刪除
    if (deleteCancelBtn) {
        deleteCancelBtn.addEventListener('click', closeDeleteModal);
    }

    // 關閉刪除確認對話框
    function closeDeleteModal() {
        deleteConfirmModal.classList.remove('active');
        setTimeout(() => deleteConfirmModal.classList.add('hidden'), 200);
        pendingDeleteId = null;
    }

    // 點擊背景關閉
    if (deleteConfirmModal) {
        deleteConfirmModal.addEventListener('click', (e) => {
            if (e.target === deleteConfirmModal) closeDeleteModal();
        });
    }

    // Move Standard Function - 同子分類內上下移動
    window.moveStandard = function (id, direction) {
        const std = standards.find(s => s.id === id);
        if (!std) return;

        // 取得同子分類、同 Category 的標準列表
        const category = std.category || 'Other';
        const stressType = std.stressType;
        const subcatName = getSubcategory(stressType).name;

        // 找出同分類同子分類的所有標準（按 standards 陣列順序）
        const sameSubcatStds = standards.filter(s =>
            (s.category || 'Other') === category &&
            getSubcategory(s.stressType).name === subcatName
        );

        // 在同子分類中找到當前標準的位置
        const subcatIdx = sameSubcatStds.findIndex(s => s.id === id);
        if (subcatIdx === -1) return;

        // 判斷是否可以移動
        if (direction === 'up' && subcatIdx === 0) return;
        if (direction === 'down' && subcatIdx === sameSubcatStds.length - 1) return;

        // 找到要交換的標準
        const swapIdx = direction === 'up' ? subcatIdx - 1 : subcatIdx + 1;
        const swapStd = sameSubcatStds[swapIdx];

        // 在主 standards 陣列中交換位置
        const mainIdx = standards.findIndex(s => s.id === id);
        const swapMainIdx = standards.findIndex(s => s.id === swapStd.id);

        // 執行交換
        [standards[mainIdx], standards[swapMainIdx]] = [standards[swapMainIdx], standards[mainIdx]];

        // 保存並重新渲染
        localStorage.setItem('dqa_standards', JSON.stringify(standards));
        renderStandards(searchInput.value);

        // 同步到 data.js
        syncToDataJs(standards, '法規順序已調整');
    };

    // Move Category Function - 調整類別順序
    window.moveCategory = function (category, direction) {
        const idx = categoryOrder.indexOf(category);
        if (idx === -1) return;

        // 判斷是否可以移動
        if (direction === 'up' && idx === 0) return;
        if (direction === 'down' && idx === categoryOrder.length - 1) return;

        // 找到要交換的位置
        const swapIdx = direction === 'up' ? idx - 1 : idx + 1;

        // 執行交換
        [categoryOrder[idx], categoryOrder[swapIdx]] = [categoryOrder[swapIdx], categoryOrder[idx]];

        // 保存到 localStorage 並重新渲染
        localStorage.setItem('dqa_category_order', JSON.stringify(categoryOrder));
        renderStandards(searchInput.value);
    };

    // Move Subcategory Function - 調整子分類順序
    window.moveSubcategory = function (subcat, direction) {
        const idx = subcategoryOrder.indexOf(subcat);

        // 如果子分類不在順序中，先加入
        if (idx === -1) {
            subcategoryOrder.push(subcat);
            localStorage.setItem('dqa_subcategory_order', JSON.stringify(subcategoryOrder));
            renderStandards(searchInput.value);
            return;
        }

        // 判斷是否可以移動
        if (direction === 'up' && idx === 0) return;
        if (direction === 'down' && idx === subcategoryOrder.length - 1) return;

        // 找到要交換的位置
        const swapIdx = direction === 'up' ? idx - 1 : idx + 1;

        // 執行交換
        [subcategoryOrder[idx], subcategoryOrder[swapIdx]] = [subcategoryOrder[swapIdx], subcategoryOrder[idx]];

        // 保存到 localStorage 並重新渲染
        localStorage.setItem('dqa_subcategory_order', JSON.stringify(subcategoryOrder));
        renderStandards(searchInput.value);
    };

    // Event Listeners
    searchInput.addEventListener('input', (e) => {
        renderStandards(e.target.value);
    });

    addBtn.addEventListener('click', () => {
        // Reset form for "Add" mode
        addForm.reset();
        document.getElementById('std-id').value = '';
        document.getElementById('modal-title').textContent = 'Add New Standard';
        if (stdCategoryCustom) stdCategoryCustom.style.display = 'none';

        addModal.classList.remove('hidden');
        setTimeout(() => addModal.classList.add('active'), 10);
    });

    function closeModal() {
        addModal.classList.remove('active');
        setTimeout(() => addModal.classList.add('hidden'), 200);
        addForm.reset();
        if (stdCategoryCustom) stdCategoryCustom.style.display = 'none'; // Reset custom input visibility
    }

    closeModalBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    addModal.addEventListener('click', (e) => {
        if (e.target === addModal) closeModal();
    });

    // Toggle Custom Category Input
    stdCategorySelect.addEventListener('change', (e) => {
        if (e.target.value === 'Other') {
            stdCategoryCustom.style.display = 'block';
            stdCategoryCustom.required = true;
        } else {
            stdCategoryCustom.style.display = 'none';
            stdCategoryCustom.required = false;
        }
    });

    addForm.addEventListener('submit', (e) => {
        e.preventDefault();

        let category = stdCategorySelect.value;
        if (category === 'Other') {
            category = stdCategoryCustom.value.trim() || 'Other';
        }

        const nameInput = document.getElementById('std-name').value.trim();
        const idInput = document.getElementById('std-id').value;

        if (idInput) {
            // EDIT MODE
            const stdIndex = standards.findIndex(s => s.id === idInput);
            if (stdIndex !== -1) {
                // Update existing
                standards[stdIndex].name = nameInput;
                standards[stdIndex].description = document.getElementById('std-desc').value;
                standards[stdIndex].version = document.getElementById('std-version').value;
                standards[stdIndex].cost = document.getElementById('std-cost').value;
                standards[stdIndex].effectiveDate = document.getElementById('std-effective').value;
                standards[stdIndex].expiryDate = document.getElementById('std-expiry').value;
                standards[stdIndex].category = category;
                standards[stdIndex].sourceUrl = document.getElementById('std-source-url').value;

                localStorage.setItem('dqa_standards', JSON.stringify(standards));
                renderStandards(searchInput.value);
                closeModal();

                // 即時同步到 data.js，確保一鍵更新能正確讀取
                syncToDataJs(standards, '法規已更新');
            }
        } else {
            // ADD MODE
            // Check for duplicates
            const isDuplicate = standards.some(std => std.name.trim().toUpperCase() === nameInput.toUpperCase());
            if (isDuplicate) {
                alert('Error: A standard with this name already exists.');
                return;
            }

            const newStandard = {
                id: 'std-' + Date.now(),
                name: nameInput,
                description: document.getElementById('std-desc').value,
                version: document.getElementById('std-version').value,
                cost: document.getElementById('std-cost').value,
                effectiveDate: document.getElementById('std-effective').value,
                expiryDate: document.getElementById('std-expiry').value,
                category: category,
                revisionSummary: '',
                sourceUrl: document.getElementById('std-source-url').value
            };

            standards.unshift(newStandard); // Add to top
            localStorage.setItem('dqa_standards', JSON.stringify(standards));
            renderStandards(searchInput.value);
            closeModal();

            // 即時同步到 data.js，確保一鍵更新能正確讀取
            syncToDataJs(standards, '法規已新增');
        }
    });

    // Details Modal Listeners
    function closeDetailsModal() {
        detailsModal.classList.remove('active');
        setTimeout(() => detailsModal.classList.add('hidden'), 200);
    }

    if (closeDetailsModalBtn) {
        closeDetailsModalBtn.addEventListener('click', closeDetailsModal);
    }
    if (closeDetailsBtn) {
        closeDetailsBtn.addEventListener('click', closeDetailsModal);
    }
    if (detailsModal) {
        detailsModal.addEventListener('click', (e) => {
            if (e.target === detailsModal) closeDetailsModal();
        });
    }

    // Auto-Update Feature - Detect new standards and version updates (Legacy - hidden button)
    if (checkUpdatesBtn) {
        checkUpdatesBtn.addEventListener('click', async () => {
            // 1. Show Scanning UI
            const originalText = checkUpdatesBtn.innerHTML;
            checkUpdatesBtn.disabled = true;
            checkUpdatesBtn.innerHTML = `<i data-lucide="loader-2" class="spin"></i> Scanning...`;
            lucide.createIcons();

            // Simulate network delay
            await new Promise(resolve => setTimeout(resolve, 1500));

            // 2. Compare initialStandards (from data.js) with current standards (from localStorage)
            const updatesFound = [];

            // Find new standards (in initialStandards but not in current standards)
            if (typeof initialStandards !== 'undefined') {
                initialStandards.forEach(initStd => {
                    const existingStd = standards.find(s => s.id === initStd.id);

                    if (!existingStd) {
                        // This is a new standard
                        updatesFound.push({
                            id: initStd.id,
                            name: initStd.name,
                            type: 'NEW',
                            newVersion: initStd.version,
                            newEffective: initStd.effectiveDate,
                            newExpiry: initStd.expiryDate,
                            newSummary: initStd.revisionSummary,
                            newCost: initStd.cost,
                            newDescription: initStd.description,
                            newCategory: initStd.category,
                            newSourceUrl: initStd.sourceUrl
                        });
                    } else {
                        // Check if any important data has been updated
                        const versionChanged = initStd.version && existingStd.version && initStd.version !== existingStd.version;
                        const dateChanged = initStd.effectiveDate && existingStd.effectiveDate && initStd.effectiveDate !== existingStd.effectiveDate;
                        const costChanged = initStd.cost && existingStd.cost && initStd.cost !== existingStd.cost;
                        const expiryChanged = initStd.expiryDate && existingStd.expiryDate && initStd.expiryDate !== existingStd.expiryDate;
                        const urlChanged = initStd.sourceUrl && existingStd.sourceUrl && initStd.sourceUrl !== existingStd.sourceUrl;

                        if (versionChanged || dateChanged || costChanged || expiryChanged || urlChanged) {
                            const changeType = versionChanged ? 'VERSION' : 'DATA';
                            updatesFound.push({
                                id: initStd.id,
                                name: initStd.name,
                                type: 'UPDATE',
                                changeType: changeType,
                                oldVersion: existingStd.version,
                                newVersion: initStd.version,
                                oldEffective: existingStd.effectiveDate,
                                newEffective: initStd.effectiveDate,
                                oldCost: existingStd.cost,
                                newCost: initStd.cost,
                                newExpiry: initStd.expiryDate,
                                newSummary: initStd.revisionSummary,
                                newDescription: initStd.description,
                                newCategory: initStd.category,
                                newSourceUrl: initStd.sourceUrl,
                                oldSourceUrl: existingStd.sourceUrl
                            });
                        }
                    }
                });
            }

            checkUpdatesBtn.innerHTML = originalText;
            checkUpdatesBtn.disabled = false;
            lucide.createIcons();

            // 3. Show Results in Modal
            updatesList.innerHTML = '';

            if (updatesFound.length === 0) {
                updatesList.innerHTML = '<div style="text-align:center; padding: 2rem;"><i data-lucide="check-circle" style="width:48px; height:48px; color:var(--success); margin-bottom:1rem;"></i><p style="font-size:1.1rem; color:var(--text-primary);">目前資料已是最新版本</p><p style="color:var(--text-secondary);">All standards are up to date.</p></div>';
                document.getElementById('update-confirm-btn').style.display = 'none';
                lucide.createIcons();
            } else {
                updatesFound.forEach(update => {
                    const item = document.createElement('div');
                    item.className = 'update-item';
                    if (update.type === 'NEW') {
                        // Find source URL (or use the one passed in update object)
                        const verifyUrl = update.newSourceUrl || '#';

                        item.innerHTML = `
                    <div style="flex:1;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.2rem;">
                                <h4 style="color:var(--accent-color); margin:0;">${update.name}</h4>
                                <a href="${verifyUrl}" target="_blank" style="font-size:0.8rem; color:var(--primary); text-decoration:none; display:flex; align-items:center; gap:4px;">
                                    <i data-lucide="external-link" style="width:12px; height:12px;"></i> Verify
                                </a>
                            </div>
                            <div style="display:flex; gap:1rem; font-size:0.85rem; color:var(--text-secondary);">
                                <span>Version: <b style="color:var(--text-primary);">${update.newVersion}</b></span>
                                <span>Cost: ${update.newCost || '-'}</span>
                            </div>
                        </div>
                        <div class="badge-new">NEW</div>
                    `;
                    } else {
                        const changeDetails = [];
                        if (update.oldVersion !== update.newVersion) changeDetails.push('版本');
                        if (update.oldEffective !== update.newEffective) changeDetails.push('日期');
                        if (update.oldCost !== update.newCost) changeDetails.push('成本');
                        const changeText = changeDetails.length > 0 ? ` (${changeDetails.join(', ')})` : '';

                        // Find source URL
                        const sourceStd = (typeof initialStandards !== 'undefined') ? initialStandards.find(s => s.id === update.id) : null;
                        const verifyUrl = sourceStd ? (sourceStd.sourceUrl || getSearchUrl(sourceStd.name)) : '#';

                        item.innerHTML = `
                        <div style="flex:1;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.2rem;">
                            <h4 style="color:var(--accent-color); margin:0;">${update.name}</h4>
                            <a href="${verifyUrl}" target="_blank" style="font-size:0.8rem; color:var(--primary); text-decoration:none; display:flex; align-items:center; gap:4px;">
                                <i data-lucide="external-link" style="width:12px; height:12px;"></i> Verify
                            </a>
                        </div>
                        <div style="display:flex; gap:1rem; font-size:0.85rem; color:var(--text-secondary); flex-wrap: wrap;">
                            ${update.oldVersion !== update.newVersion ? `<span>版本: ${update.oldVersion} → <b style="color:var(--text-primary);">${update.newVersion}</b></span>` : ''}
                            ${update.oldEffective !== update.newEffective ? `<span>日期: ${formatDate(update.oldEffective)} → <b style="color:var(--text-primary);">${formatDate(update.newEffective)}</b></span>` : ''}
                            ${update.oldCost !== update.newCost ? `<span>成本: ${update.oldCost} → <b style="color:var(--text-primary);">${update.newCost}</b></span>` : ''}
                            ${update.oldSourceUrl !== update.newSourceUrl ? `<span>連結: <b style="color:var(--text-primary);">Updated</b></span>` : ''}
                        </div>
                    </div>
                        <div class="badge-new">UPDATE${changeText}</div>
                `;

                    }
                    updatesList.appendChild(item);
                });

                // Show "Update All" button
                const confirmBtn = document.getElementById('update-confirm-btn');
                confirmBtn.style.display = 'block';
                confirmBtn.onclick = () => applyUpdates(updatesFound);
            }

            updatesModal.classList.remove('hidden');
            setTimeout(() => updatesModal.classList.add('active'), 10);
        });
    } // End of if (checkUpdatesBtn)

    async function applyUpdates(updates) {
        let newCount = 0;
        let updateCount = 0;

        updates.forEach(update => {
            if (update.type === 'NEW') {
                // Add new standard
                const newStandard = {
                    id: update.id,
                    name: update.name,
                    description: update.newDescription,
                    version: update.newVersion,
                    effectiveDate: update.newEffective,
                    expiryDate: update.newExpiry,
                    cost: update.newCost,
                    category: update.newCategory,
                    revisionSummary: update.newSummary
                };
                standards.push(newStandard);
                newCount++;
            } else {
                // Update existing standard
                const stdIndex = standards.findIndex(s => s.id === update.id);
                if (stdIndex !== -1) {
                    // Generate revision summary based on what changed
                    const changes = [];
                    if (update.oldVersion !== update.newVersion) {
                        changes.push(`版本: ${update.oldVersion} → ${update.newVersion}`);
                    }
                    if (update.oldEffective !== update.newEffective) {
                        changes.push(`發布日期更新`);
                    }
                    if (update.oldExpiry !== update.newExpiry) {
                        // Extract year for cleaner display
                        const oldYear = update.oldExpiry ? update.oldExpiry.match(/\d{4}/)?.[0] : '';
                        const newYear = update.newExpiry ? update.newExpiry.match(/\d{4}/)?.[0] : '';
                        if (oldYear && newYear && oldYear !== newYear) {
                            changes.push(`穩定性: ${oldYear} → ${newYear}`);
                        } else if (newYear) {
                            changes.push(`穩定性: ${newYear}`);
                        }
                    }
                    if (update.oldCost !== update.newCost) {
                        changes.push(`價格: ${update.oldCost || '-'} → ${update.newCost}`);
                    }

                    // Build revision summary
                    let revisionSummary;
                    if (changes.length > 0) {
                        const dateStr = new Date().toLocaleDateString('zh-TW');
                        revisionSummary = `[${dateStr}更新]${changes.join('; ')}`;
                    } else {
                        revisionSummary = update.newSummary || standards[stdIndex].revisionSummary || '';
                    }

                    standards[stdIndex].version = update.newVersion;
                    standards[stdIndex].effectiveDate = update.newEffective;
                    standards[stdIndex].expiryDate = update.newExpiry;
                    standards[stdIndex].revisionSummary = revisionSummary;
                    standards[stdIndex].cost = update.newCost;
                    standards[stdIndex].description = update.newDescription;
                    standards[stdIndex].category = update.newCategory;
                    standards[stdIndex].sourceUrl = update.newSourceUrl;
                    updateCount++;
                }
            }
        });

        localStorage.setItem('dqa_standards', JSON.stringify(standards));

        // Sync to data.js via API (so Python scraper uses updated data)
        try {
            const syncResponse = await fetch('/api/sync-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(standards)
            });
            const syncResult = await syncResponse.json();
            if (syncResult.status === 'success') {
                console.log('[SYNC] data.js updated successfully');
            } else {
                console.warn('[SYNC] Failed to sync data.js:', syncResult.message);
            }
        } catch (syncError) {
            console.warn('[SYNC] Could not sync to data.js:', syncError);
        }

        renderStandards(searchInput.value);
        closeUpdatesModal();

        // Show success feedback
        let message = '';
        if (newCount > 0 && updateCount > 0) {
            message = `成功新增 ${newCount} 個法規，更新 ${updateCount} 個法規。\n(已同步至 data.js)`;
        } else if (newCount > 0) {
            message = `成功新增 ${newCount} 個法規。\n(已同步至 data.js)`;
        } else if (updateCount > 0) {
            message = `成功更新 ${updateCount} 個法規。\n(已同步至 data.js)`;
        }
        alert(message);
    }

    function closeUpdatesModal() {
        updatesModal.classList.remove('active');
        setTimeout(() => updatesModal.classList.add('hidden'), 200);
    }

    closeUpdatesModalBtn.addEventListener('click', closeUpdatesModal);
    closeUpdatesBtn.addEventListener('click', closeUpdatesModal);

    // Manual Update (Load Python Report)
    const manualUpdateBtn = document.getElementById('manual-update-btn');
    if (manualUpdateBtn) {
        manualUpdateBtn.addEventListener('click', async () => {
            const originalText = manualUpdateBtn.innerHTML;
            manualUpdateBtn.disabled = true;
            manualUpdateBtn.innerHTML = `<i data-lucide="loader-2" class="spin"></i> Loading...`;
            lucide.createIcons();

            try {
                // 0. First sync current standards to data.js (so Python scraper includes newly added standards)
                try {
                    const syncResponse = await fetch('/api/sync-data', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(standards)
                    });
                    const syncResult = await syncResponse.json();
                    if (syncResult.status === 'success') {
                        console.log('[SYNC] data.js synced before verification');
                    } else {
                        console.warn('[SYNC] Failed to sync data.js:', syncResult.message);
                    }
                } catch (syncError) {
                    console.warn('[SYNC] Could not sync to data.js before verification:', syncError);
                }

                // 1. Trigger Python Script via Server
                const runResponse = await fetch('/api/run-verify', { method: 'POST' });
                if (runResponse.ok) {
                    const runResult = await runResponse.json();
                    if (runResult.status !== 'success') {
                        console.warn('Script warning:', runResult.message);
                        // Continue anyway to try loading report
                    }
                } else {
                    console.warn('Server API not available, trying to load static report...');
                }

                // 2. Load the generated JSON report
                const response = await fetch('verification_results.json?t=' + Date.now()); // Add timestamp to prevent caching
                if (!response.ok) throw new Error('Report not found');

                const reportData = await response.json();
                const updatesFound = [];

                reportData.results.forEach(res => {
                    if (res.status === 'MISMATCH') {
                        // Find existing standard to get old values
                        const existingStd = standards.find(s => s.id === res.id);
                        if (existingStd) {
                            // Parse issues to determine what changed
                            // Formats: "Date: Local='...' vs Live='...'"
                            //          "Stability: Local='...' vs Live='...'"
                            //          "Edition: Local='...' vs Live='...'"
                            //          "Cost: Local='...' vs Live='...'"
                            let newVersion = existingStd.version;
                            let newEffective = existingStd.effectiveDate;
                            let newCost = existingStd.cost;
                            let newExpiry = existingStd.expiryDate;

                            res.issues.forEach(issue => {
                                if (issue.includes('Date:')) {
                                    const match = issue.match(/Live='(.*?)'/);
                                    if (match) newEffective = match[1];
                                }
                                if (issue.includes('Cost:')) {
                                    const match = issue.match(/Live='(.*?)'/);
                                    if (match) newCost = match[1];
                                }
                                if (issue.includes('Stability:')) {
                                    const match = issue.match(/Live='(.*?)'/);
                                    if (match) {
                                        // Convert to Stability format: "2026" -> "2026 (Stability)"
                                        const year = match[1];
                                        newExpiry = year.includes('Stability') ? year : `${year}(Stability)`;
                                    }
                                }
                                if (issue.includes('Edition:')) {
                                    const match = issue.match(/Live='(.*?)'/);
                                    if (match) newVersion = match[1];
                                }
                            });

                            // Check if there are actual changes compared to localStorage
                            const hasChanges =
                                newVersion !== existingStd.version ||
                                newEffective !== existingStd.effectiveDate ||
                                newCost !== existingStd.cost ||
                                newExpiry !== existingStd.expiryDate;

                            if (hasChanges) {
                                updatesFound.push({
                                    id: res.id,
                                    name: res.name,
                                    type: 'UPDATE',
                                    changeType: 'DATA',
                                    oldVersion: existingStd.version,
                                    newVersion: newVersion,
                                    oldEffective: existingStd.effectiveDate,
                                    newEffective: newEffective,
                                    oldCost: existingStd.cost,
                                    newCost: newCost,
                                    oldExpiry: existingStd.expiryDate,
                                    newExpiry: newExpiry,
                                    newSummary: existingStd.revisionSummary,
                                    newDescription: existingStd.description,
                                    newCategory: existingStd.category,
                                    newSourceUrl: res.url,
                                    oldSourceUrl: existingStd.sourceUrl,
                                    issues: res.issues // 保存原始 issues 用於顯示
                                });
                            }
                        }
                    }
                });

                // Show Results using existing logic
                updatesList.innerHTML = '';
                if (updatesFound.length === 0) {
                    updatesList.innerHTML = '<div style="text-align:center; padding: 2rem;"><i data-lucide="check-circle" style="width:48px; height:48px; color:var(--success); margin-bottom:1rem;"></i><p style="font-size:1.1rem; color:var(--text-primary);">Report says all valid</p><p style="color:var(--text-secondary);">No mismatches found in the last report.</p></div>';
                    document.getElementById('update-confirm-btn').style.display = 'none';
                } else {
                    updatesFound.forEach(update => {
                        const item = document.createElement('div');
                        item.className = 'update-item';

                        // 直接使用 issues 來顯示差異
                        const issuesList = update.issues && update.issues.length > 0
                            ? update.issues.map(issue => {
                                // 解析 issue 格式: "Stability: Local='2026 (Stability)' vs Live='2029'"
                                const parts = issue.match(/^(\w+): Local='(.*)' vs Live='(.*)'$/);
                                if (parts) {
                                    const [, field, localVal, liveVal] = parts;
                                    const fieldName = {
                                        'Stability': '穩定性',
                                        'Date': '日期',
                                        'Edition': '版本',
                                        'Cost': '成本'
                                    }[field] || field;
                                    return `<span>${fieldName}: ${localVal} → <b style="color:var(--accent-color);">${liveVal}</b></span>`;
                                }
                                return `<span>${issue}</span>`;
                            }).join('')
                            : '<span style="color:var(--text-muted);">無詳細資訊</span>';

                        item.innerHTML = `
                    <div style="flex:1;">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.2rem;">
                                    <h4 style="color:var(--text-primary); margin:0;">${update.name}</h4>
                                    <a href="${update.newSourceUrl}" target="_blank" style="font-size:0.8rem; color:var(--accent-color); text-decoration:none; display:flex; align-items:center; gap:4px;">
                                        <i data-lucide="external-link" style="width:12px; height:12px;"></i> Verify
                                    </a>
                                </div>
                                <div style="display:flex; gap:1rem; font-size:0.85rem; color:var(--text-secondary); flex-wrap: wrap;">
                                    ${issuesList}
                                </div>
                                <div class="badge-new">UPDATE</div>
                            </div>
                        `;
                        updatesList.appendChild(item);
                    });

                    const confirmBtn = document.getElementById('update-confirm-btn');
                    confirmBtn.style.display = 'block';
                    confirmBtn.onclick = () => applyUpdates(updatesFound);
                }

                updatesModal.classList.remove('hidden');
                setTimeout(() => updatesModal.classList.add('active'), 10);
                lucide.createIcons();

            } catch (e) {
                console.error(e);
                alert('Failed to load report. Please run "python verify_standards.py" first.');
            } finally {
                manualUpdateBtn.innerHTML = originalText;
                manualUpdateBtn.disabled = false;
                lucide.createIcons();
            }
        });
    }

    // Initial Load
    loadStandards();
});
