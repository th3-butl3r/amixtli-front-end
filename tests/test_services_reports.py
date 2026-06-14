"""Tests for ReportsServices."""

from unittest.mock import patch


from services.reports import reports_services


def _make_doc(id: str, url: str = "http://img.example.com/x.jpg", **kwargs) -> dict:
    return {
        "id": id,
        "uriImage": url,
        "labels": kwargs.get("labels", "basura"),
        "comments": kwargs.get("comments", "comentario"),
        "city": kwargs.get("city", "Morelia"),
        "state": kwargs.get("state", "Michoacán"),
    }


class TestGetReportsToValidate:
    def test_returns_list_of_tuples(self):
        docs = [_make_doc("1"), _make_doc("2")]
        with patch("services.reports.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = docs
            result = reports_services.get_reports_to_validate()

        assert len(result) == 2
        # Each item is a tuple (url, labels, comments, city, state, id)
        assert result[0] == (
            "http://img.example.com/x.jpg",
            "basura",
            "comentario",
            "Morelia",
            "Michoacán",
            "1",
        )

    def test_skips_docs_without_id(self):
        docs = [{"uriImage": "http://img.example.com/noid.jpg"}, _make_doc("10")]
        with patch("services.reports.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = docs
            result = reports_services.get_reports_to_validate()

        assert len(result) == 1
        assert result[0][5] == "10"

    def test_skips_docs_without_uri_image(self):
        docs = [
            {"id": "no-img", "labels": "x"},  # no uriImage
            _make_doc("20"),
        ]
        with patch("services.reports.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = docs
            result = reports_services.get_reports_to_validate()

        assert len(result) == 1
        assert result[0][5] == "20"

    def test_caps_results_at_five(self):
        docs = [_make_doc(str(i)) for i in range(10)]
        with patch("services.reports.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = docs
            result = reports_services.get_reports_to_validate()

        assert len(result) == 5

    def test_returns_empty_list_when_no_docs(self):
        with patch("services.reports.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = []
            result = reports_services.get_reports_to_validate()

        assert result == []

    def test_optional_fields_default_to_none(self):
        docs = [{"id": "5", "uriImage": "http://img.example.com/5.jpg"}]
        with patch("services.reports.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = docs
            result = reports_services.get_reports_to_validate()

        assert len(result) == 1
        url, labels, comments, city, state, id_ = result[0]
        assert labels is None
        assert comments is None
        assert city is None
        assert state is None

    def test_requests_unvalidated_reports(self):
        with patch("services.reports.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = []
            reports_services.get_reports_to_validate()

        mock_mgr.get_reports.assert_called_once_with(is_valid=False)


class TestUpdateReport:
    def test_delegates_to_manager(self):
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("services.reports.amixtli_manager") as mock_mgr:
            mock_mgr.update_report.return_value = mock_response
            result = reports_services.update_report("id-1", {"isValid": True}, "tok")

        mock_mgr.update_report.assert_called_once_with(
            id_report="id-1", value_to_update={"isValid": True}, token="tok"
        )
        assert result is mock_response

    def test_returns_manager_response_unchanged(self):
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 400

        with patch("services.reports.amixtli_manager") as mock_mgr:
            mock_mgr.update_report.return_value = mock_response
            result = reports_services.update_report("x", {}, "t")

        assert result.status_code == 400
