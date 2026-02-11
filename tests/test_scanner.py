"""Tests for barcode scanner keyboard wedge input capture."""

import time
from unittest.mock import MagicMock
import pytest

from src.scanner import Scanner, ScanResult


class TestKeystrokeProcessing:

    def test_valid_12_digit_scan(self):
        scanner = Scanner()
        for ch in "000100001525":
            result = scanner.on_keystroke(ch)
            assert result is None
        result = scanner.on_keystroke("\r")
        assert result is not None
        assert result.scanned == "000100001525"

    def test_scan_with_newline(self):
        scanner = Scanner()
        for ch in "000100001525":
            scanner.on_keystroke(ch)
        result = scanner.on_keystroke("\n")
        assert result is not None
        assert result.scanned == "000100001525"

    def test_short_input_rejected(self):
        scanner = Scanner()
        for ch in "00010":
            scanner.on_keystroke(ch)
        result = scanner.on_keystroke("\r")
        assert result is None

    def test_long_input_rejected(self):
        scanner = Scanner()
        for ch in "0001000015250":  # 13 digits
            scanner.on_keystroke(ch)
        result = scanner.on_keystroke("\r")
        assert result is None

    def test_non_digit_filtered(self):
        scanner = Scanner()
        # Mix in letters; they should be ignored
        for ch in "0A0B0C1D0E0F0G0H1I5J2K5":
            scanner.on_keystroke(ch)
        result = scanner.on_keystroke("\r")
        assert result is not None
        assert result.scanned == "000100001525"

    def test_buffer_clears_after_scan(self):
        scanner = Scanner()
        for ch in "000100001525":
            scanner.on_keystroke(ch)
        scanner.on_keystroke("\r")
        # Second scan attempt with empty buffer
        result = scanner.on_keystroke("\r")
        assert result is None


class TestVerification:

    def test_match(self):
        scanner = Scanner()
        scanner.set_expected("000100001525")
        for ch in "000100001525":
            scanner.on_keystroke(ch)
        result = scanner.on_keystroke("\r")
        assert result.matched is True

    def test_mismatch(self):
        scanner = Scanner()
        scanner.set_expected("000100001525")
        for ch in "000100002008":
            scanner.on_keystroke(ch)
        result = scanner.on_keystroke("\r")
        assert result.matched is False

    def test_no_expected(self):
        scanner = Scanner()
        for ch in "000100001525":
            scanner.on_keystroke(ch)
        result = scanner.on_keystroke("\r")
        assert result.matched is False
        assert result.expected is None

    def test_clear_expected(self):
        scanner = Scanner()
        scanner.set_expected("000100001525")
        scanner.clear_expected()
        assert scanner._expected_barcode is None


class TestRawInput:

    def test_valid_raw(self):
        scanner = Scanner()
        scanner.set_expected("000100001525")
        result = scanner.process_raw_input("000100001525")
        assert result is not None
        assert result.matched is True

    def test_invalid_raw_short(self):
        scanner = Scanner()
        result = scanner.process_raw_input("00010")
        assert result is None

    def test_raw_with_whitespace(self):
        scanner = Scanner()
        result = scanner.process_raw_input("  000100001525  ")
        assert result is not None
        assert result.scanned == "000100001525"


class TestCallback:

    def test_callback_called(self):
        scanner = Scanner()
        callback = MagicMock()
        scanner.set_callback(callback)
        for ch in "000100001525":
            scanner.on_keystroke(ch)
        scanner.on_keystroke("\r")
        callback.assert_called_once()
        result = callback.call_args[0][0]
        assert isinstance(result, ScanResult)

    def test_callback_on_raw(self):
        scanner = Scanner()
        callback = MagicMock()
        scanner.set_callback(callback)
        scanner.process_raw_input("000100001525")
        callback.assert_called_once()


class TestScanResult:

    def test_repr_match(self):
        r = ScanResult("000100001525", "000100001525")
        assert "MATCH" in repr(r)

    def test_repr_mismatch(self):
        r = ScanResult("000100001525", "000100002008")
        assert "MISMATCH" in repr(r)
