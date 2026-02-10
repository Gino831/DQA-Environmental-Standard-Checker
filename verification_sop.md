# IEC Standard Data Verification Process

This document outlines the step-by-step process for verifying the accuracy of IEC standard data (Version, Date, Cost) using the official IEC Webstore.

## 1. Official Source
All data must be verified against the **IEC Webstore** (https://webstore.iec.ch/). This is the single source of truth.

## 2. Search Procedure
1.  **Go to** [webstore.iec.ch](https://webstore.iec.ch/).
2.  **Enter the Standard Number** in the search bar (e.g., `60068-2-1`).
3.  **Click Search**.

## 3. Selecting the Correct Version (CRITICAL)
The search results will often show multiple versions. You must select the **Base Publication**.

*   **Look for**: `International Standard` in the "Publication type" column.
*   **Avoid**:
    *   `Consolidated Version` (CSV): These usually have higher prices (e.g., CHF 400+) because they include past amendments.
    *   `Redline Version` (RLV): These show changes and are also more expensive.
    *   `Amendment` (AMD): These are just updates, not the full standard.

**Example:**
For `IEC 60068-2-1`:
*   ✅ **Select**: `IEC 60068-2-1:2007` (Edition 6.0) - *If this is the active base version.*
*   ❌ **Ignore**: `IEC 60068-2-1:2007+AMD1:2011 CSV` (Consolidated).

## 4. Verifying Data Points
Once on the correct product page, verify the following:

### A. Edition / Version
*   Check the **Edition** number (e.g., `6.0`).
*   Check the **Publication date** (e.g., `2007-03-28`).
*   **Format**: `Ed. 6.0 (2007)`.

### B. Effective Date
*   Use the **Publication date** from the "General information" section.

### C. Stability Date / Expiry
*   Look for the **Stability date** in the "Life cycle" or "General information" section.
*   **Format**: `2027 (Stability)`.

### D. Cost (Price)
*   Look for the price of the **Base Publication**.
*   **Note**: Ensure you are looking at the price for the standard itself, not a bundle or a different format.
*   **Currency**: CHF (Swiss Francs).

## 5. Common Pitfalls & Solutions
*   **"Price is too high"**: You are likely looking at a *Consolidated Version* (CSV). Go back and find the Base Version.
*   **"Date doesn't match"**: Check if you are looking at an *Amendment* (AMD) date instead of the Base Version date.
*   **"Standard not found"**: Ensure you typed the number correctly. Try searching without the "IEC" prefix (e.g., just `60068-2-1`).

## 6. Verification Checklist
- [ ] URL points to the **Base Version** (not CSV/RLV).
- [ ] **Edition** matches the official page.
- [ ] **Publication Date** matches.
- [ ] **Stability Date** matches.
- [ ] **Cost** matches the Base Version price.
