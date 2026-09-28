"""
Tests for gs_openapi.v3.references helpers.
"""

from gs_openapi.v3.references import (
    COMMAND_TYPES,
    TASK_START_ERROR_CODES,
    WORK_STATES,
    describe_task_error,
    describe_work_state,
    is_terminal_work_state,
)


def test_work_states_known_codes():
    assert WORK_STATES[100] == ("IDLE", "Idle")
    assert WORK_STATES[230] == ("AUTO_TASKING", "Auto task in progress")
    assert WORK_STATES[440] == ("EMERGENCY_PARKING", "Emergency parking")


def test_describe_work_state():
    assert describe_work_state(170) == ("NAVIGATING", "Navigating")
    assert describe_work_state(99999) is None


def test_is_terminal_work_state():
    assert is_terminal_work_state(100) is True   # IDLE
    assert is_terminal_work_state(420) is True   # PRIMARY_STOP
    assert is_terminal_work_state(440) is True   # EMERGENCY_PARKING
    assert is_terminal_work_state(0) is True     # UNSPECIFIED
    assert is_terminal_work_state(230) is False  # AUTO_TASKING (active)
    assert is_terminal_work_state(170) is False  # NAVIGATING


def test_command_types():
    assert COMMAND_TYPES["START_FUSION_TASK"] == ("Start task", "Start Combined Task")
    assert COMMAND_TYPES["CROSS_NAVIGATE"] == ("Navigate home", "Navigate Home")
    assert len(COMMAND_TYPES) == 9


def test_describe_task_error():
    assert describe_task_error(2010100009) == "Failed to operate data."
    assert describe_task_error(2010105002) == "Task time conflict, please create a new schedule."
    assert describe_task_error(1234567890) is None


def test_task_error_codes_populated():
    # Sanity: the table has hundreds of entries transcribed from the doc.
    assert len(TASK_START_ERROR_CODES) > 100
