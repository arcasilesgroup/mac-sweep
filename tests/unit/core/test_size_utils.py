"""Tests for mac_sweep.core.size_utils."""

import os
import tempfile

from mac_sweep.core.size_utils import dir_size, file_age_days, format_size


class TestFormatSize:
    def test_zero(self):
        assert format_size(0) == "0 B"

    def test_bytes(self):
        assert format_size(500) == "500 B"

    def test_kilobytes(self):
        result = format_size(1024)
        assert "KB" in result

    def test_megabytes(self):
        result = format_size(5 * 1024 * 1024)
        assert "MB" in result
        assert result.startswith("5")

    def test_gigabytes(self):
        result = format_size(4.2 * 1024**3)
        assert "GB" in result

    def test_terabytes(self):
        result = format_size(2 * 1024**4)
        assert "TB" in result

    def test_negative(self):
        assert format_size(-1) == "0 B"

    def test_large_megabytes(self):
        result = format_size(500 * 1024**2)
        assert "MB" in result

    def test_small_kilobytes(self):
        result = format_size(1536)
        assert "KB" in result


class TestDirSize:
    def test_missing_path(self):
        assert dir_size("/nonexistent/path/12345") == 0

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as td:
            assert dir_size(td) == 0

    def test_dir_with_files(self):
        with tempfile.TemporaryDirectory() as td:
            fpath = os.path.join(td, "test.txt")
            with open(fpath, "w") as f:
                f.write("x" * 100)
            size = dir_size(td)
            assert size >= 100

    def test_single_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"hello world")
            f.flush()
            path = f.name
        try:
            size = dir_size(path)
            assert size >= 11
        finally:
            os.unlink(path)

    def test_nested_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            sub = os.path.join(td, "sub")
            os.makedirs(sub)
            with open(os.path.join(sub, "data.bin"), "wb") as f:
                f.write(b"\x00" * 200)
            size = dir_size(td)
            assert size >= 200


class TestFileAgeDays:
    def test_missing_file(self):
        assert file_age_days("/nonexistent/12345") == -1

    def test_recent_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            age = file_age_days(path)
            assert 0 <= age < 1
        finally:
            os.unlink(path)

    def test_returns_float(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            age = file_age_days(path)
            assert isinstance(age, float)
        finally:
            os.unlink(path)
