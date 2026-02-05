"""
Tests for safety and validation module.
"""

import unittest
import time
from src.safety import (
    WorkflowGuard, WorkflowState, ValidationResult,
    WeightValidator, BarcodeValidator, OperationLock,
    validate_sku, validate_weight, validate_customer_name
)


class TestWorkflowGuard(unittest.TestCase):
    """Test workflow state machine."""

    def setUp(self):
        self.guard = WorkflowGuard()

    def test_initial_state(self):
        """Test initial state is IDLE."""
        self.assertEqual(self.guard.state, WorkflowState.IDLE)

    def test_valid_transition_idle_to_product_selected(self):
        """Test valid transition from IDLE to PRODUCT_SELECTED."""
        result = self.guard.transition(WorkflowState.PRODUCT_SELECTED)
        self.assertTrue(result)
        self.assertEqual(self.guard.state, WorkflowState.PRODUCT_SELECTED)

    def test_invalid_transition_idle_to_weight_captured(self):
        """Test invalid transition (skipping PRODUCT_SELECTED)."""
        result = self.guard.transition(WorkflowState.WEIGHT_CAPTURED)
        self.assertFalse(result)
        self.assertEqual(self.guard.state, WorkflowState.IDLE)

    def test_full_workflow_sequence(self):
        """Test complete valid workflow sequence."""
        transitions = [
            WorkflowState.PRODUCT_SELECTED,
            WorkflowState.WEIGHT_CAPTURED,
            WorkflowState.LABEL_PRINTED,
            WorkflowState.AWAITING_SCAN,
            WorkflowState.VERIFIED,
        ]
        for state in transitions:
            result = self.guard.transition(state)
            self.assertTrue(result, f"Failed transition to {state}")
            self.assertEqual(self.guard.state, state)

    def test_reset(self):
        """Test reset returns to IDLE."""
        self.guard.transition(WorkflowState.PRODUCT_SELECTED)
        self.guard.reset()
        self.assertEqual(self.guard.state, WorkflowState.IDLE)

    def test_can_select_product_from_idle(self):
        """Test can_select_product is True from IDLE."""
        self.assertTrue(self.guard.can_select_product)

    def test_cannot_select_product_during_scan(self):
        """Test can_select_product is False during AWAITING_SCAN."""
        self.guard.transition(WorkflowState.PRODUCT_SELECTED)
        self.guard.transition(WorkflowState.WEIGHT_CAPTURED)
        self.guard.transition(WorkflowState.LABEL_PRINTED)
        self.guard.transition(WorkflowState.AWAITING_SCAN)
        self.assertFalse(self.guard.can_select_product)

    def test_can_print_only_after_weight_captured(self):
        """Test can_print is only True in WEIGHT_CAPTURED state."""
        self.assertFalse(self.guard.can_print)

        self.guard.transition(WorkflowState.PRODUCT_SELECTED)
        self.assertFalse(self.guard.can_print)

        self.guard.transition(WorkflowState.WEIGHT_CAPTURED)
        self.assertTrue(self.guard.can_print)

    def test_can_go_back_to_product_selected(self):
        """Test can go back to select different product."""
        self.guard.transition(WorkflowState.PRODUCT_SELECTED)
        self.guard.transition(WorkflowState.WEIGHT_CAPTURED)

        # Should be able to go back
        result = self.guard.transition(WorkflowState.PRODUCT_SELECTED)
        self.assertTrue(result)

    def test_state_change_callback(self):
        """Test state change callback is called."""
        states_received = []
        self.guard.on_state_change(lambda s: states_received.append(s))

        self.guard.transition(WorkflowState.PRODUCT_SELECTED)
        self.guard.transition(WorkflowState.WEIGHT_CAPTURED)

        self.assertEqual(states_received, [
            WorkflowState.PRODUCT_SELECTED,
            WorkflowState.WEIGHT_CAPTURED
        ])


class TestWeightValidator(unittest.TestCase):
    """Test weight validation logic."""

    def setUp(self):
        self.validator = WeightValidator()

    def test_single_reading_not_stable(self):
        """Test single reading is not stable."""
        self.validator.add_reading(2.5)
        self.assertFalse(self.validator.is_stable())
        self.assertIsNone(self.validator.get_stable_weight())

    def test_stable_after_multiple_readings(self):
        """Test stability after consistent readings."""
        for _ in range(3):
            self.validator.add_reading(2.50)

        self.assertTrue(self.validator.is_stable())
        self.assertEqual(self.validator.get_stable_weight(), 2.50)

    def test_not_stable_with_varying_readings(self):
        """Test instability with varying readings."""
        self.validator.add_reading(2.50)
        self.validator.add_reading(2.55)
        self.validator.add_reading(2.60)

        self.assertFalse(self.validator.is_stable())

    def test_stable_within_tolerance(self):
        """Test stability within tolerance."""
        self.validator.add_reading(2.50)
        self.validator.add_reading(2.51)
        self.validator.add_reading(2.50)

        self.assertTrue(self.validator.is_stable())

    def test_negative_weight_invalid(self):
        """Test negative weight is invalid."""
        result = self.validator.add_reading(-1.0)
        self.assertFalse(result.valid)
        self.assertIn("Negative", result.message)

    def test_weight_exceeds_max(self):
        """Test weight exceeding maximum."""
        result = self.validator.add_reading(150.0)
        self.assertFalse(result.valid)
        self.assertIn("exceeds", result.message)

    def test_reset_clears_readings(self):
        """Test reset clears all readings."""
        for _ in range(3):
            self.validator.add_reading(2.50)

        self.assertTrue(self.validator.is_stable())

        self.validator.reset()
        self.assertFalse(self.validator.is_stable())

    def test_minimum_weight_threshold(self):
        """Test minimum weight threshold."""
        for _ in range(3):
            self.validator.add_reading(0.01)

        # Stable but below minimum
        self.assertTrue(self.validator.is_stable())
        self.assertIsNone(self.validator.get_stable_weight())


class TestBarcodeValidator(unittest.TestCase):
    """Test barcode validation logic."""

    def setUp(self):
        self.validator = BarcodeValidator()

    def test_no_expectation_accepts_any(self):
        """Test scan accepted when no expectation set."""
        result = self.validator.validate_scan("123456789012")
        self.assertTrue(result.valid)

    def test_matching_barcode_valid(self):
        """Test matching barcode is valid."""
        self.validator.expect_barcode("123456789012", timeout=10)
        result = self.validator.validate_scan("123456789012")
        self.assertTrue(result.valid)

    def test_non_matching_barcode_invalid(self):
        """Test non-matching barcode is invalid."""
        self.validator.expect_barcode("123456789012", timeout=10)
        result = self.validator.validate_scan("000000000000")
        self.assertFalse(result.valid)
        self.assertTrue(result.can_retry)

    def test_timeout_expired(self):
        """Test scan after timeout expired."""
        self.validator.expect_barcode("123456789012", timeout=0.1)
        time.sleep(0.2)
        result = self.validator.validate_scan("123456789012")
        self.assertFalse(result.valid)
        self.assertIn("timeout", result.message.lower())

    def test_clear_expectation(self):
        """Test clearing expectation."""
        self.validator.expect_barcode("123456789012")
        self.assertTrue(self.validator.is_expecting)

        self.validator.clear_expectation()
        self.assertFalse(self.validator.is_expecting)

    def test_time_remaining(self):
        """Test time remaining calculation."""
        self.validator.expect_barcode("123456789012", timeout=5)
        remaining = self.validator.time_remaining
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 4)
        self.assertLessEqual(remaining, 5)

    def test_debounce_rapid_scans(self):
        """Test rapid scans are debounced."""
        self.validator.validate_scan("123456789012")
        # Immediate second scan should be rejected
        result = self.validator.validate_scan("123456789012")
        self.assertFalse(result.valid)
        self.assertIn("too fast", result.message.lower())


class TestOperationLock(unittest.TestCase):
    """Test operation lock for concurrency."""

    def setUp(self):
        self.lock = OperationLock()

    def test_acquire_when_free(self):
        """Test acquiring lock when free."""
        result = self.lock.acquire("print")
        self.assertTrue(result)
        self.assertEqual(self.lock.current_operation, "print")

    def test_cannot_acquire_when_locked(self):
        """Test cannot acquire when already locked."""
        self.lock.acquire("print")
        result = self.lock.acquire("scan")
        self.assertFalse(result)
        self.assertEqual(self.lock.current_operation, "print")

    def test_release_allows_new_acquire(self):
        """Test release allows new acquisition."""
        self.lock.acquire("print")
        self.lock.release()
        result = self.lock.acquire("scan")
        self.assertTrue(result)


class TestValidationFunctions(unittest.TestCase):
    """Test standalone validation functions."""

    def test_validate_sku_valid(self):
        """Test valid SKU."""
        result = validate_sku("00123")
        self.assertTrue(result.valid)

    def test_validate_sku_empty(self):
        """Test empty SKU is invalid."""
        result = validate_sku("")
        self.assertFalse(result.valid)

    def test_validate_sku_non_numeric(self):
        """Test non-numeric SKU is invalid."""
        result = validate_sku("ABC12")
        self.assertFalse(result.valid)

    def test_validate_sku_too_long(self):
        """Test SKU too long is invalid."""
        result = validate_sku("123456")
        self.assertFalse(result.valid)

    def test_validate_weight_valid(self):
        """Test valid weight."""
        result = validate_weight(2.5)
        self.assertTrue(result.valid)

    def test_validate_weight_zero(self):
        """Test zero weight is invalid."""
        result = validate_weight(0)
        self.assertFalse(result.valid)

    def test_validate_weight_negative(self):
        """Test negative weight is invalid."""
        result = validate_weight(-1.0)
        self.assertFalse(result.valid)

    def test_validate_weight_too_small(self):
        """Test weight below minimum is invalid."""
        result = validate_weight(0.01)
        self.assertFalse(result.valid)

    def test_validate_weight_too_large(self):
        """Test weight above maximum is invalid."""
        result = validate_weight(150.0)
        self.assertFalse(result.valid)

    def test_validate_customer_name_valid(self):
        """Test valid customer name."""
        result = validate_customer_name("John Smith")
        self.assertTrue(result.valid)

    def test_validate_customer_name_empty(self):
        """Test empty name is invalid."""
        result = validate_customer_name("")
        self.assertFalse(result.valid)

    def test_validate_customer_name_too_short(self):
        """Test name too short is invalid."""
        result = validate_customer_name("J")
        self.assertFalse(result.valid)


if __name__ == '__main__':
    unittest.main()
