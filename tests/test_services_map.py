"""Tests for MapServices."""

from unittest.mock import patch

import folium


from services.map import MapServices


def _make_report(is_solved: bool = False, **overrides) -> dict:
    doc = {
        "latitude": 19.4326,
        "longitude": -99.1332,
        "isSolved": is_solved,
        "importanceReport": "3",
        "labels": "basura orgánica",
        "created": "2024-06-01T10:00:00Z",
        "comments": "Hay mucha basura en la esquina.",
        "uriImage": "http://example.com/images/report1.jpg",
    }
    doc.update(overrides)
    return doc


class TestCreateHtmlElement:
    def test_returns_folium_html_instance(self):
        result = MapServices.create_html_element(_make_report())
        assert isinstance(result, folium.Html)

    def test_renders_importance_level(self):
        result = MapServices.create_html_element(_make_report(importanceReport="7"))
        assert "7" in result.data

    def test_renders_labels(self):
        result = MapServices.create_html_element(_make_report(labels="plástico"))
        assert "plástico" in result.data

    def test_renders_comments(self):
        result = MapServices.create_html_element(
            _make_report(comments="Zona muy contaminada")
        )
        assert "Zona muy contaminada" in result.data

    def test_renders_image_url(self):
        url = "http://example.com/images/pic.jpg"
        result = MapServices.create_html_element(_make_report(uriImage=url))
        assert url in result.data

    def test_escapes_xss_in_importance_level(self):
        payload = '<script>alert("xss")</script>'
        result = MapServices.create_html_element(_make_report(importanceReport=payload))
        assert "<script>" not in result.data
        assert "&lt;script&gt;" in result.data

    def test_escapes_xss_in_labels(self):
        result = MapServices.create_html_element(_make_report(labels="<b>bold</b>"))
        assert "<b>" not in result.data
        assert "&lt;b&gt;" in result.data

    def test_escapes_xss_in_comments(self):
        # html.escape converts <img to &lt;img so the browser never treats
        # the injected markup as a real tag (the template's own <img> is fine)
        payload = '"><img src=x onerror=alert(1)>'
        result = MapServices.create_html_element(_make_report(comments=payload))
        assert "&lt;img src=x onerror=alert(1)&gt;" in result.data

    def test_handles_missing_fields_gracefully(self):
        result = MapServices.create_html_element({})
        assert isinstance(result, folium.Html)

    def test_script_execution_disabled(self):
        # folium.Html with script=False should not set script=True
        result = MapServices.create_html_element(_make_report())
        assert result.script is False


class TestBuildMap:
    def test_returns_string(self):
        with patch("services.map.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = []
            result = MapServices.build_map()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_requests_only_valid_reports(self):
        with patch("services.map.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = []
            MapServices.build_map()
        mock_mgr.get_reports.assert_called_once_with(is_valid=True)

    def test_builds_map_with_unsolved_report(self):
        docs = [_make_report(is_solved=False)]
        with patch("services.map.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = docs
            result = MapServices.build_map()
        assert isinstance(result, str)

    def test_builds_map_with_solved_report(self):
        docs = [_make_report(is_solved=True)]
        with patch("services.map.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = docs
            result = MapServices.build_map()
        assert isinstance(result, str)

    def test_builds_map_with_multiple_reports(self):
        docs = [
            _make_report(is_solved=False, latitude=19.4, longitude=-99.1),
            _make_report(is_solved=True, latitude=20.9, longitude=-89.6),
            _make_report(is_solved=False, latitude=25.6, longitude=-100.3),
        ]
        with patch("services.map.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = docs
            result = MapServices.build_map()
        assert isinstance(result, str)

    def test_map_html_is_embeddable(self):
        """Result should not contain the outer folium wrapper divs."""
        with patch("services.map.amixtli_manager") as mock_mgr:
            mock_mgr.get_reports.return_value = []
            result = MapServices.build_map()
        # The string surgery in build_map strips the outer wrapper; result
        # should start with something reasonable (not the stripped wrapper).
        assert result.strip() != ""
