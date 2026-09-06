# 07 — PDF Generation

## 7.1 Three document types

| Document | Generator | Template | Source |
| --- | --- | --- | --- |
| Bill (invoice) | `controllers/bill_gen.py` | `src/pdf/templates/bill_template.html` | `controllers/files.py:46` |
| Credit note | `controllers/cnote_gen.py` | `src/pdf/templates/cnote_template.html` | `controllers/files.py:56` |
| Customer info | `controllers/files.py:17` (ReportLab canvas) | none | `controllers/files.py:17` |

## 7.2 Bill / credit-note PDF pipeline

Source: `bill_gen.py` / `cnote_gen.py`, `controllers/billit.py:format_dyn_data`.

1. Select language: `customer.language.upper() == "FR"` → FR variant, else NL.
2. Load static labels (`pdf/static_data.py`): `bill_static_fr()` /
   `bill_static_nl()` (or `cnote_*`), including the seller block
   ("ANTOONS Luc BV/SRL", address, VAT, IBAN, BIC, contact).
3. Inject the 6% VAT certificate text when `ventilationCode == "2"`
   (`six_percent_certificate[FR|NL]`).
4. Build dynamic data (`PDF` TypedDict) via `format_dyn_data`:
   - `Order`: number, about-invoice-number (cnotes), dates (dd/mm/YYYY),
     title, reference (= orderNumber), VAT, totals, OGM, legal info
     (`comments[lang][ventilationCode]`).
   - `Customer`: company, contact full name, salutation, street+number,
     zip, city, VAT, customer nr.
   - `OrderLines`: formatted via `order_line_string` (prices as `"12,34"`).
5. Render the Jinja2 template to HTML (`autoescape=True`), passing
   `unit_is_empty` and (bills only) `add_salutation` flags.
6. Convert HTML → PDF with WeasyPrint, applying `src/pdf/pdf.css` and a
   `FontConfiguration`.
7. Merge the generated PDF with `src/pdf/verkoopsvoorwaarden.pdf` (general
   conditions) using PyPDF2 `PdfMerger`.

Requirements:

- FR-PDF-1: The PDF language must follow the customer's `language` field.
- FR-PDF-2: All monetary amounts must use comma decimal separator
  (`price_to_string`).
- FR-PDF-3: The 6% certificate text must appear only when
  `ventilationCode == "2"`.
- FR-PDF-4: The general-conditions PDF must always be appended.
- FR-PDF-5: Credit-note PDFs must omit delivery date and OGM, and show the
  "about invoice number" and a credit-note-specific comment
  (`CnoteComment` label).
- FR-PDF-6: The same generated PDF bytes are both sent to Billit (base64 in
  `OrderPDF`) and returned by the `/api/files/...` endpoints.

## 7.3 Legal / static content

Source: `pdf/static_data.py`.

- `me`: seller identity (ANTOONS Luc BV/SRL, BE 0885.315.931, IBAN, BIC).
- `comments[lang][ventilationCode]`: VAT legal comment per language and code.
  For code `21` (reverse charge) the autoliquidation text is inserted; codes
  `1/2/4` have empty legal comments (the 6% certificate is injected
  separately for code `2`).
- `static_fr` / `static_nl`: all UI labels (Description, UnitPrice, Count,
  Unit, Excl, VAT, Incl, Total, GeneralConditions, Contact, OGM, IBAN, BIC,
  CnoteComment).

## 7.4 Customer info PDF

Source: `controllers/files.py:17`. A minimal ReportLab canvas listing: Numéro,
Nom/Prénom, Société, Adresse, Numéro de TVA, Langue, Nom d'Architecte,
Commentaire. It is a plain listing (not the branded template) used by the
customer "Print" button.

## 7.5 Open points

- **[GAP]** PDF generation reads files via relative paths
  (`./src/pdf/pdf.css`, `./src/pdf/verkoopsvoorwaarden.pdf`,
  `FileSystemLoader("src/pdf/templates")`); it depends on the process CWD
  being `syncora/`. The Docker image copies `src/` to `/app` and runs from
  `/app`, so paths would need to be `src/pdf/...` — verify the container
  actually generates PDFs.
- **[ASSUMPTION]** fonts in `src/pdf/fonts` are referenced by `pdf.css`; not
  audited here.
