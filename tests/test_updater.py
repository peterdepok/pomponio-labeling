"""Tests for GitHub auto-updater."""

import pytest

from src.updater import Updater


class TestVersionComparison:

    def test_newer_patch(self):
        assert Updater._is_newer("1.0.1", "1.0.0") is True

    def test_newer_minor(self):
        assert Updater._is_newer("1.1.0", "1.0.0") is True

    def test_newer_major(self):
        assert Updater._is_newer("2.0.0", "1.0.0") is True

    def test_same_version(self):
        assert Updater._is_newer("1.0.0", "1.0.0") is False

    def test_older_version(self):
        assert Updater._is_newer("1.0.0", "1.0.1") is False

    def test_different_lengths(self):
        assert Updater._is_newer("1.1", "1.0.0") is True
        assert Updater._is_newer("1.0.0", "1.1") is False

    def test_invalid_version(self):
        assert Updater._is_newer("abc", "1.0.0") is False
        assert Updater._is_newer("1.0.0", "abc") is False
