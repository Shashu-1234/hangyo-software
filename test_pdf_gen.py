import os
import tempfile
import unittest

from pdf_gen import _monthly_report_header_styles, _styles, generate_monthly_report_pdf


class TestMonthlyReportPdfHeaderLayout(unittest.TestCase):
    def test_monthly_header_styles_have_safe_spacing(self):
        _, title, sub, *_ = _styles()
        brand_style, report_title_style = _monthly_report_header_styles(title, sub)

        self.assertGreaterEqual(brand_style.leading, brand_style.fontSize)
        self.assertGreater(brand_style.spaceAfter, 0)
        self.assertGreaterEqual(report_title_style.leading, report_title_style.fontSize)
        self.assertGreater(report_title_style.spaceBefore, 0)

    def test_generate_monthly_report_pdf_creates_file(self):
        data = {
            "summary": {
                "total_orders": 3,
                "total_billed": 1200,
                "total_collected": 1000,
                "total_pending": 200,
                "delivered": 2,
            },
            "top_products": [],
            "top_shops": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "monthly-report.pdf")
            result = generate_monthly_report_pdf("April 2026", data, path)

            self.assertEqual(result, path)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)


if __name__ == "__main__":
    unittest.main()
