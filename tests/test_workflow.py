"""Tests for the labeling workflow state machine."""

from unittest.mock import MagicMock
import pytest

from src.safety import Workflow, WorkflowState, WorkflowError


@pytest.fixture
def wf():
    return Workflow()


class TestInitialState:

    def test_starts_idle(self, wf):
        assert wf.state == WorkflowState.IDLE

    def test_context_empty(self, wf):
        assert wf.context.product_id is None
        assert wf.context.weight_lb is None
        assert wf.context.barcode is None


class TestHappyPath:
    """Full workflow: IDLE -> PRODUCT_SELECTED -> WEIGHT_CAPTURED -> LABEL_PRINTED -> AWAITING_SCAN -> VERIFIED -> IDLE."""

    def test_full_cycle(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        assert wf.state == WorkflowState.PRODUCT_SELECTED
        assert wf.context.product_id == 1
        assert wf.context.sku == "00100"

        wf.capture_weight(1.52)
        assert wf.state == WorkflowState.WEIGHT_CAPTURED
        assert wf.context.weight_lb == 1.52

        wf.print_label("000100001525")
        assert wf.state == WorkflowState.LABEL_PRINTED
        assert wf.context.barcode == "000100001525"

        wf.await_scan()
        assert wf.state == WorkflowState.AWAITING_SCAN

        wf.verify(42)
        assert wf.state == WorkflowState.VERIFIED
        assert wf.context.package_id == 42

        wf.complete()
        assert wf.state == WorkflowState.IDLE
        assert wf.context.product_id is None

    def test_multiple_packages(self, wf):
        """Process two packages in sequence."""
        for _ in range(2):
            wf.select_product(1, "Ribeye", "00100")
            wf.capture_weight(1.52)
            wf.print_label("000100001525")
            wf.await_scan()
            wf.verify(1)
            wf.complete()
        assert wf.state == WorkflowState.IDLE


class TestInvalidTransitions:

    def test_cannot_skip_product_selection(self, wf):
        with pytest.raises(WorkflowError):
            wf.capture_weight(1.52)

    def test_cannot_skip_weight(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        with pytest.raises(WorkflowError):
            wf.print_label("000100001525")

    def test_cannot_skip_print(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        wf.capture_weight(1.52)
        with pytest.raises(WorkflowError):
            wf.await_scan()

    def test_cannot_skip_scan(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        wf.capture_weight(1.52)
        wf.print_label("barcode")
        with pytest.raises(WorkflowError):
            wf.verify(1)

    def test_cannot_verify_from_idle(self, wf):
        with pytest.raises(WorkflowError):
            wf.verify(1)

    def test_cannot_complete_from_product_selected(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        with pytest.raises(WorkflowError):
            wf.complete()

    def test_zero_weight_rejected(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        with pytest.raises(WorkflowError, match="positive"):
            wf.capture_weight(0.0)

    def test_negative_weight_rejected(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        with pytest.raises(WorkflowError, match="positive"):
            wf.capture_weight(-1.0)


class TestCancel:

    def test_cancel_from_product_selected(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        wf.cancel()
        assert wf.state == WorkflowState.IDLE
        assert wf.context.product_id is None

    def test_cancel_from_weight_captured(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        wf.capture_weight(1.52)
        wf.cancel()
        assert wf.state == WorkflowState.IDLE

    def test_cancel_from_label_printed(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        wf.capture_weight(1.52)
        wf.print_label("barcode")
        wf.cancel()
        assert wf.state == WorkflowState.IDLE

    def test_cancel_from_awaiting_scan(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        wf.capture_weight(1.52)
        wf.print_label("barcode")
        wf.await_scan()
        wf.cancel()
        assert wf.state == WorkflowState.IDLE

    def test_cancel_from_idle_is_noop(self, wf):
        wf.cancel()
        assert wf.state == WorkflowState.IDLE


class TestReweigh:

    def test_reweigh_from_weight_captured(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        wf.capture_weight(1.52)
        wf.reweigh()
        assert wf.state == WorkflowState.PRODUCT_SELECTED
        assert wf.context.weight_lb is None
        assert wf.context.product_id == 1  # product still set

    def test_reweigh_then_capture(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        wf.capture_weight(1.52)
        wf.reweigh()
        wf.capture_weight(1.55)
        assert wf.context.weight_lb == 1.55

    def test_reweigh_from_wrong_state(self, wf):
        wf.select_product(1, "Ribeye", "00100")
        with pytest.raises(WorkflowError):
            wf.reweigh()


class TestCallback:

    def test_state_change_callback(self, wf):
        callback = MagicMock()
        wf.set_callback(callback)
        wf.select_product(1, "Ribeye", "00100")
        callback.assert_called_once_with(
            WorkflowState.IDLE, WorkflowState.PRODUCT_SELECTED
        )

    def test_cancel_callback(self, wf):
        callback = MagicMock()
        wf.set_callback(callback)
        wf.select_product(1, "Ribeye", "00100")
        callback.reset_mock()
        wf.cancel()
        callback.assert_called_once_with(
            WorkflowState.PRODUCT_SELECTED, WorkflowState.IDLE
        )


class TestContextPersistence:

    def test_animal_box_persist_across_cancel(self, wf):
        wf.context.animal_id = 1
        wf.context.box_id = 5
        wf.select_product(1, "Ribeye", "00100")
        wf.cancel()
        assert wf.context.animal_id == 1
        assert wf.context.box_id == 5

    def test_animal_box_persist_across_complete(self, wf):
        wf.context.animal_id = 1
        wf.context.box_id = 5
        wf.select_product(1, "Ribeye", "00100")
        wf.capture_weight(1.52)
        wf.print_label("barcode")
        wf.await_scan()
        wf.verify(42)
        wf.complete()
        assert wf.context.animal_id == 1
        assert wf.context.box_id == 5
