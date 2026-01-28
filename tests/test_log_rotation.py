import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import tempfile
import unittest


class TestLogRotation(unittest.TestCase):
    def test_rotating_file_handler_creates_backups(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "test.log"
            logger = logging.getLogger("test_rotation")
            logger.setLevel(logging.INFO)
            logger.propagate = False

            if logger.handlers:
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)

            handler = RotatingFileHandler(
                log_path,
                maxBytes=512,
                backupCount=2,
                encoding="utf-8",
            )
            logger.addHandler(handler)

            for i in range(200):
                logger.info("log line %s", i)

            handler.close()
            logger.removeHandler(handler)

            self.assertTrue(log_path.exists(), "Основной лог-файл не создан")
            rotated_files = [p for p in log_path.parent.glob("test.log.*") if p.is_file()]
            self.assertTrue(
                any(p.suffix in {".1", ".2"} for p in rotated_files),
                "Ротированные файлы не созданы",
            )
            total_files = 1 + len(rotated_files)
            self.assertLessEqual(
                total_files,
                3,
                "Количество файлов превышает backupCount",
            )


if __name__ == "__main__":
    unittest.main()
