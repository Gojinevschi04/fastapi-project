from unittest.mock import patch

from app.core.config import Settings


def test_default_values() -> None:
    with patch.dict("os.environ", {}, clear=True):
        test_settings = Settings()
        assert test_settings.LOG_LEVEL in ["INFO", 20]
        assert test_settings.STORAGE_PATH == "storage"


def test_db_url_computed_field() -> None:
    with patch.dict(
        "os.environ",
        {
            "DB_USER": "testuser",
            "DB_PASS": "testpass",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "testdb",
        },
        clear=True,
    ):
        test_settings = Settings()
        expected_url = "postgresql+asyncpg://testuser:testpass@localhost:5432/testdb"
        assert expected_url == test_settings.DB_URL


def test_storage_dir_computed_field() -> None:
    with patch.dict("os.environ", {}, clear=True):
        test_settings = Settings()
        assert test_settings.STORAGE_DIR.name == "storage"  # type: ignore
