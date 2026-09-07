"""Gap regression tests (§21).

These pin known-deficient behaviours so regressions are detected. Many
TC-GAP-* cases are pinned inline in the api/unit test files (see cross-references
below); this file covers the remaining ones.

Inline-covered: TC-GAP-1 (test_bills), TC-GAP-2 (test_bills/test_customers),
TC-GAP-3 (test_peppol_flow), TC-GAP-4/5 (test_billit_flow/test_peppol_flow),
TC-GAP-7 (unit/test_dates_locking), TC-GAP-8 (test_customers),
TC-GAP-13 (test_files), TC-GAP-14 (test_polling), TC-GAP-16 (unit/test_billit_dto).
"""
