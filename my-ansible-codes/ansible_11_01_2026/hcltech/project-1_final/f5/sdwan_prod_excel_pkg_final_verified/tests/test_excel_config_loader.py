from src.services.excel_config_loader import DEFAULT_EXCEL_PATH


def test_excel_template_exists():
    # Smoke check so packaging doesn't forget the customer workbook template.
    import os

    assert os.path.isfile(DEFAULT_EXCEL_PATH)
