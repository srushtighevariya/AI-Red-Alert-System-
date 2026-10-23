# Benchmark test documents

Longer, realistically formatted documents for testing the AI Document Red Alert
detector across formats (DOCX, text PDF, scanned/image PDF), languages (English,
Gujarati) and risk types. Each document is **3–4 pages** (the Green control is 2),
with substantial content and, where risky, a clear spread of detectable keywords.

**These are SYNTHETIC benchmark documents.** Every document carries a visible
"SYNTHETIC BENCHMARK — NOT A GENUINE DOCUMENT" banner on every page (and a
diagonal "SYNTHETIC SAMPLE" watermark on the PDFs). All people, companies,
banks, account numbers, Aadhaar/PAN numbers and events are fictional. The
Aadhaar numbers are format-valid (correct Verhoeff check digit) but belong to
no real person. These files are for detector testing only.

## The set, and how the detector scored it

| # | File | Format · pages | Scenario | Detector result |
|---|------|----------------|----------|-----------------|
| 01 | Infosec_Policy_SPW | DOCX · 4 | IT policy with a **buried off-book-payments clause** + annexures of staff Aadhaar/PAN/salary accounts and admin passwords | **Red 100** — keywords (confidential, password, classified, bank account), policy violation, sensitive data |
| 02 | Procurement_Vendor_Payments_AEC | DOCX · 3 | Procurement policy with a **buried "bypass approval / off the record / no paper trail" scheme** + bank/GSTIN | **Red 100** — fraud, bypass approval, do not share with compliance |
| 03 | Settlement_Demand_Letter (scanned) | image PDF · 4 | Extortion / "settlement" demand letter — tests **OCR** | **Red 100** — pay or else, leak your data, final warning, threat |
| 04 | Intimidation_Letter_NoKeywords | DOCX · 3 | Veiled intimidation with **no explicit threat keywords** — tests the **AI meaning-model** | **Yellow 56** — AI reads threat 0.92 (no keyword hits) |
| 05 | Recovery_Notice_Gujarati | DOCX · 3 | **Gujarati** debt-recovery-cum-threat notice with Aadhaar/PAN | **Red 100** — Gujarati keywords + threats |
| 06 | Divorce_MoU_RiskyClauses | PDF · 3 | Divorce settlement with **one-sided / risky clauses** (blank signed cheques, total waiver, ₹25 lakh penalty) + personal data | **Red 100** — confidential, do not disclose, bank account, sensitive data |
| 07 | Internal_Investigation_Report_NLT | DOCX · 3 | Confidential **fraud-investigation report** (fake invoices, misused password) | **Red 100** — fraud, fake, confidential, password + AI threat/policy |
| 08 | Internal_Memo_OffBook_Payment | DOCX · 3 | Internal memo approving an **off-the-books vendor payment** | **Red 100** — confidential, classified, do not disclose, do not keep evidence |
| 09 | Office_Circular_Holidays | DOCX · 2 | Plain festival-holiday / office-timings circular | **Green 0** — true-negative control |

So the set gives **8 clear detections** (7 Red with visible keywords, 1 Yellow
caught only by the AI model) and **1 Green** control proving the detector does
not flag an ordinary document.

## Not included

A bank phishing / credential-harvesting notice and an advance-fee ("you won a
loan, pay a fee") scam letter were deliberately **not** created: a convincing
version of either would work as a real attack. The risky documents here depict
threats or internal wrongdoing rather than ready-to-use fraud templates, and all
carry the synthetic watermark.
