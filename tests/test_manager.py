"""Tests for AmixtliManager — HTTP client wrapper."""

import json
from unittest.mock import MagicMock, patch


from managers.amixtli_manager import amixtli_manager


def _make_response(status_code: int, body: dict = None) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = json.dumps(body or {})
    return mock


class TestGetReports:
    def test_returns_results_on_200(self):
        body = {"results": [{"id": "1"}, {"id": "2"}]}
        with patch(
            "managers.amixtli_manager.requests.get",
            return_value=_make_response(200, body),
        ):
            result = amixtli_manager.get_reports()
        assert result == [{"id": "1"}, {"id": "2"}]

    def test_returns_results_on_201(self):
        body = {"results": [{"id": "3"}]}
        with patch(
            "managers.amixtli_manager.requests.get",
            return_value=_make_response(201, body),
        ):
            result = amixtli_manager.get_reports()
        assert result == [{"id": "3"}]

    def test_sends_params_when_is_valid_provided(self):
        body = {"results": []}
        with patch(
            "managers.amixtli_manager.requests.get",
            return_value=_make_response(200, body),
        ) as mock_get:
            amixtli_manager.get_reports(is_valid=True)
        mock_get.assert_called_once_with(amixtli_manager.url, params={"is_valid": True})

    def test_no_params_when_is_valid_is_none(self):
        body = {"results": []}
        with patch(
            "managers.amixtli_manager.requests.get",
            return_value=_make_response(200, body),
        ) as mock_get:
            amixtli_manager.get_reports(is_valid=None)
        mock_get.assert_called_once_with(amixtli_manager.url)

    def test_returns_empty_list_on_404(self):
        with patch(
            "managers.amixtli_manager.requests.get", return_value=_make_response(404)
        ):
            result = amixtli_manager.get_reports()
        assert result == []

    def test_returns_empty_list_on_500(self):
        with patch(
            "managers.amixtli_manager.requests.get", return_value=_make_response(500)
        ):
            result = amixtli_manager.get_reports(is_valid=False)
        assert result == []

    def test_returns_empty_list_when_results_key_missing(self):
        body = {"data": [{"id": "1"}]}  # no "results" key
        with patch(
            "managers.amixtli_manager.requests.get",
            return_value=_make_response(200, body),
        ):
            result = amixtli_manager.get_reports()
        assert result == []


class TestUpdateReport:
    def test_sends_patch_with_correct_payload(self):
        mock_resp = _make_response(200)
        with patch(
            "managers.amixtli_manager.requests.patch", return_value=mock_resp
        ) as mock_patch:
            result = amixtli_manager.update_report(
                "123", {"isValid": True}, "bearer-token"
            )

        mock_patch.assert_called_once_with(
            f"{amixtli_manager.url}/123",
            json={"isValid": True},
            headers={"Authorization": "Bearer bearer-token"},
        )
        assert result is mock_resp

    def test_sends_correct_authorization_header(self):
        with patch(
            "managers.amixtli_manager.requests.patch", return_value=_make_response(200)
        ) as mock_patch:
            amixtli_manager.update_report("abc", {"isValid": False}, "my-secret-token")
        _, kwargs = mock_patch.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer my-secret-token"

    def test_returns_response_object(self):
        mock_resp = _make_response(400)
        with patch("managers.amixtli_manager.requests.patch", return_value=mock_resp):
            result = amixtli_manager.update_report("x", {}, "tok")
        assert result is mock_resp

    def test_update_report_builds_correct_url(self):
        with patch(
            "managers.amixtli_manager.requests.patch", return_value=_make_response(200)
        ) as mock_patch:
            amixtli_manager.update_report("report-id-99", {"isValid": True}, "t")
        call_url = mock_patch.call_args[0][0]
        assert call_url.endswith("/report-id-99")
