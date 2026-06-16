"""Tests for managers/supabase_manager.py."""

import time
from unittest.mock import MagicMock, patch

import pytest

from managers.supabase_manager import (
    _cache,
    _cache_get,
    _cache_set,
    _invalidate,
    _with_retry,
    supabase_manager,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Wipe the module-level TTL cache before and after every test."""
    _cache.clear()
    yield
    _cache.clear()


def _fluent_mock(data=None):
    """Return (mock_client, response) where every chained call returns mock_client.

    Args:
        data: Value assigned to response.data (defaults to empty list).

    Returns:
        Tuple of (mock_supabase_client, response_mock).
    """
    response = MagicMock()
    response.data = data if data is not None else []
    mock = MagicMock()
    for method in (
        "table",
        "select",
        "eq",
        "order",
        "limit",
        "single",
        "rpc",
        "update",
        "delete",
    ):
        getattr(mock, method).return_value = mock
    mock.execute.return_value = response
    return mock, response


# ─── Cache helpers ────────────────────────────────────────────────────────────


class TestCacheHelpers:
    def test_cache_miss_when_empty(self):
        hit, val = _cache_get("map_reports")
        assert hit is False
        assert val is None

    def test_cache_set_then_hit(self):
        _cache_set("map_reports", [{"id": "1"}])
        hit, val = _cache_get("map_reports")
        assert hit is True
        assert val == [{"id": "1"}]

    def test_cache_expired_returns_miss(self):
        _cache["map_reports"] = ([{"id": "1"}], time.time() - 9999)
        hit, val = _cache_get("map_reports")
        assert hit is False
        assert val is None

    def test_invalidate_removes_key(self):
        _cache_set("map_reports", ["x"])
        _invalidate("map_reports")
        hit, _ = _cache_get("map_reports")
        assert hit is False

    def test_invalidate_missing_key_is_noop(self):
        _invalidate("nonexistent_key")  # Must not raise

    def test_invalidate_multiple_keys(self):
        _cache_set("map_reports", ["x"])
        _cache_set("count", 5)
        _invalidate("map_reports", "count")
        assert _cache_get("map_reports")[0] is False
        assert _cache_get("count")[0] is False

    def test_top_reports_cache_key_uses_prefix_ttl(self):
        """'top_reports:{limit}:{state}' must resolve TTL via the 'top_reports' prefix."""
        _cache_set("top_reports:10:", ["x"])
        hit, val = _cache_get("top_reports:10:")
        assert hit is True
        assert val == ["x"]


# ─── _with_retry ──────────────────────────────────────────────────────────────


class TestWithRetry:
    def test_success_first_attempt(self):
        fn = MagicMock(return_value="ok")
        result = _with_retry(fn, retries=2)
        assert result == "ok"
        assert fn.call_count == 1

    def test_retryable_error_then_success(self):
        fn = MagicMock(side_effect=[ConnectionError("server disconnected"), "ok"])
        with patch("managers.supabase_manager.time.sleep"):
            result = _with_retry(fn, retries=1)
        assert result == "ok"
        assert fn.call_count == 2

    def test_non_retryable_error_raises_immediately(self):
        fn = MagicMock(side_effect=ValueError("bad input"))
        with pytest.raises(ValueError, match="bad input"):
            _with_retry(fn, retries=2)
        assert fn.call_count == 1

    def test_all_retries_exhausted_raises(self):
        fn = MagicMock(side_effect=ConnectionError("connection refused"))
        with patch("managers.supabase_manager.time.sleep"), pytest.raises(
            ConnectionError
        ):
            _with_retry(fn, retries=2)
        assert fn.call_count == 3

    def test_eof_error_is_retryable(self):
        fn = MagicMock(side_effect=[EOFError("eof reached"), "done"])
        with patch("managers.supabase_manager.time.sleep"):
            result = _with_retry(fn, retries=1)
        assert result == "done"

    def test_timeout_error_is_retryable(self):
        fn = MagicMock(side_effect=[TimeoutError("timeout"), "done"])
        with patch("managers.supabase_manager.time.sleep"):
            result = _with_retry(fn, retries=1)
        assert result == "done"


# ─── get_map_reports ──────────────────────────────────────────────────────────


class TestGetMapReports:
    def test_returns_data_from_db(self):
        mock_sb, _ = _fluent_mock(data=[{"id": "1", "latitude": 19.4}])
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_map_reports()
        assert result == [{"id": "1", "latitude": 19.4}]

    def test_populates_cache_on_success(self):
        mock_sb, _ = _fluent_mock(data=[{"id": "2"}])
        with patch("managers.supabase_manager.supabase", mock_sb):
            supabase_manager.get_map_reports()
        hit, cached = _cache_get("map_reports")
        assert hit is True
        assert cached == [{"id": "2"}]

    def test_cache_hit_skips_db(self):
        _cache_set("map_reports", [{"id": "cached"}])
        mock_sb, _ = _fluent_mock(data=[])
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_map_reports()
        assert result == [{"id": "cached"}]
        mock_sb.table.assert_not_called()

    def test_returns_empty_list_on_error(self):
        mock_sb = MagicMock()
        mock_sb.table.side_effect = Exception("DB down")
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_map_reports()
        assert result == []


# ─── get_reports_count ────────────────────────────────────────────────────────


class TestGetReportsCount:
    def test_returns_count_from_rpc(self):
        mock_sb, response = _fluent_mock()
        response.data = 42
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_reports_count()
        assert result == 42

    def test_cache_hit_skips_rpc(self):
        _cache_set("count", 99)
        mock_sb, _ = _fluent_mock()
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_reports_count()
        assert result == 99
        mock_sb.rpc.assert_not_called()

    def test_returns_zero_on_error(self):
        mock_sb = MagicMock()
        mock_sb.rpc.side_effect = Exception("RPC failure")
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_reports_count()
        assert result == 0


# ─── get_available_states ─────────────────────────────────────────────────────


class TestGetAvailableStates:
    def test_returns_sorted_distinct_states(self):
        rows = [{"state": "Michoacán"}, {"state": "Jalisco"}, {"state": "Michoacán"}]
        mock_sb, _ = _fluent_mock(data=rows)
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_available_states()
        assert result == ["Jalisco", "Michoacán"]

    def test_filters_out_none_states(self):
        rows = [{"state": "Jalisco"}, {"state": None}, {"state": ""}]
        mock_sb, _ = _fluent_mock(data=rows)
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_available_states()
        assert result == ["Jalisco"]

    def test_cache_hit_skips_db(self):
        _cache_set("states", ["Cached"])
        mock_sb, _ = _fluent_mock(data=[])
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_available_states()
        assert result == ["Cached"]
        mock_sb.table.assert_not_called()

    def test_returns_empty_list_on_error(self):
        mock_sb = MagicMock()
        mock_sb.table.side_effect = Exception("fail")
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_available_states()
        assert result == []


# ─── get_top_reports ──────────────────────────────────────────────────────────


class TestGetTopReports:
    def test_returns_reports_without_state_filter(self):
        data = [{"id": "1", "importance_report": 10}]
        mock_sb, _ = _fluent_mock(data=data)
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_top_reports(limit=5)
        assert result == data

    def test_with_state_filter(self):
        data = [{"id": "2", "state": "Jalisco"}]
        mock_sb, _ = _fluent_mock(data=data)
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_top_reports(limit=5, state="Jalisco")
        assert result == data

    def test_cache_hit_skips_db(self):
        _cache_set("top_reports:10:", [{"id": "cached"}])
        mock_sb, _ = _fluent_mock(data=[])
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_top_reports(limit=10)
        assert result == [{"id": "cached"}]
        mock_sb.table.assert_not_called()

    def test_state_and_no_state_have_separate_cache_keys(self):
        mock_sb, _ = _fluent_mock(data=[{"id": "1"}])
        with patch("managers.supabase_manager.supabase", mock_sb):
            supabase_manager.get_top_reports(limit=10, state="Jalisco")
        hit_no_state, _ = _cache_get("top_reports:10:")
        hit_with_state, _ = _cache_get("top_reports:10:Jalisco")
        assert hit_no_state is False
        assert hit_with_state is True

    def test_returns_empty_list_on_error(self):
        mock_sb = MagicMock()
        mock_sb.table.side_effect = Exception("fail")
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_top_reports(limit=5)
        assert result == []


# ─── get_report_detail ────────────────────────────────────────────────────────


class TestGetReportDetail:
    _DETAIL = {"id": "abc", "street": "Av. Principal", "city": "Morelia"}

    def test_found_returns_data(self):
        mock_sb, response = _fluent_mock(data=self._DETAIL)
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_report_detail("abc")
        assert result == self._DETAIL

    def test_not_found_returns_none(self):
        mock_sb, response = _fluent_mock()
        response.data = None
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_report_detail("xyz")
        assert result is None

    def test_exception_returns_none(self):
        mock_sb = MagicMock()
        mock_sb.table.side_effect = Exception("fail")
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_report_detail("xyz")
        assert result is None


# ─── get_pending_reports ──────────────────────────────────────────────────────


class TestGetPendingReports:
    def test_returns_pending_reports(self):
        data = [{"id": "p1", "status": "pendiente"}]
        mock_sb, _ = _fluent_mock(data=data)
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_pending_reports()
        assert result == data

    def test_limit_is_applied(self):
        mock_sb, _ = _fluent_mock(data=[])
        with patch("managers.supabase_manager.supabase", mock_sb):
            supabase_manager.get_pending_reports(limit=5)
        mock_sb.limit.assert_called_with(5)

    def test_returns_empty_list_on_error(self):
        mock_sb = MagicMock()
        mock_sb.table.side_effect = Exception("fail")
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.get_pending_reports()
        assert result == []


# ─── approve_report ───────────────────────────────────────────────────────────


class TestApproveReport:
    def test_success_returns_true_and_invalidates_cache(self):
        _cache_set("map_reports", ["x"])
        _cache_set("states", ["y"])
        _cache_set("count", 1)
        mock_sb, _ = _fluent_mock(data=[{"id": "1"}])
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.approve_report(
                "1", waste_type="inorgánico", environment_type="urbano"
            )
        assert result is True
        assert _cache_get("map_reports")[0] is False
        assert _cache_get("states")[0] is False
        assert _cache_get("count")[0] is False

    def test_success_without_optional_fields(self):
        mock_sb, _ = _fluent_mock(data=[{"id": "2"}])
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.approve_report("2")
        assert result is True

    def test_empty_response_data_returns_false(self):
        mock_sb, _ = _fluent_mock(data=[])
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.approve_report("3")
        assert result is False

    def test_exception_returns_false(self):
        mock_sb = MagicMock()
        mock_sb.table.side_effect = Exception("DB error")
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.approve_report("4")
        assert result is False


# ─── delete_report ────────────────────────────────────────────────────────────


class TestDeleteReport:
    def test_success_returns_true(self):
        mock_sb, _ = _fluent_mock(data=[])
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.delete_report("1")
        assert result is True

    def test_exception_returns_false(self):
        mock_sb = MagicMock()
        mock_sb.table.side_effect = Exception("fail")
        with patch("managers.supabase_manager.supabase", mock_sb):
            result = supabase_manager.delete_report("2")
        assert result is False
