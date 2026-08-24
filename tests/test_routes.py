"""Tests for all Flask routes in app.py."""

from unittest.mock import patch

from managers.storage_manager import storage_manager as _st_manager
from managers.supabase_manager import supabase_manager as _sb_manager


# ─── /health ─────────────────────────────────────────────────────────────────


class TestHealthEndpoint:
    def test_returns_200_when_db_ok(self, client):
        with patch.object(_sb_manager, "health_db", return_value=True):
            res = client.get("/health")
        assert res.status_code == 200
        assert res.json["status"] == "Online"
        assert res.json["db"] == "Connected"

    def test_returns_400_when_db_returns_false(self, client):
        with patch.object(_sb_manager, "health_db", return_value=False):
            res = client.get("/health")
        assert res.status_code == 400
        assert res.json["status"] == "Error"

    def test_returns_503_on_exception(self, client):
        with patch.object(_sb_manager, "health_db", side_effect=Exception("timeout")):
            res = client.get("/health")
        assert res.status_code == 503
        assert "detail" in res.json

    def test_response_is_json(self, client):
        with patch.object(_sb_manager, "health_db", return_value=True):
            res = client.get("/health")
        assert "application/json" in res.content_type


# ─── Public routes ────────────────────────────────────────────────────────────


class TestPublicRoutes:
    def test_home_root(self, client):
        with patch.object(_sb_manager, "get_reports_count", return_value=0):
            assert client.get("/").status_code == 200

    def test_home_inicio(self, client):
        with patch.object(_sb_manager, "get_reports_count", return_value=0):
            assert client.get("/inicio").status_code == 200

    def test_home_carto_group(self, client):
        with patch.object(_sb_manager, "get_reports_count", return_value=0):
            assert client.get("/carto_group").status_code == 200

    def test_contacto(self, client):
        assert client.get("/contacto").status_code == 200

    def test_ayuda(self, client):
        assert client.get("/ayuda").status_code == 200

    def test_politica_privacidad(self, client):
        assert client.get("/politica_privacidad").status_code == 200

    def test_mapa_reportes(self, client):
        with (
            patch.object(_sb_manager, "get_map_reports", return_value=[]),
            patch.object(_sb_manager, "get_top_reports", return_value=[]),
            patch.object(_sb_manager, "get_available_states", return_value=[]),
        ):
            assert client.get("/mapa_reportes").status_code == 200

    def test_mapa_reportes_passes_reports_to_template(self, client):
        markers = [
            {"id": "abc", "latitude": 19.5, "longitude": -101.6, "importanceReport": 3}
        ]
        with (
            patch.object(_sb_manager, "get_map_reports", return_value=markers),
            patch.object(_sb_manager, "get_top_reports", return_value=[]),
            patch.object(_sb_manager, "get_available_states", return_value=[]),
        ):
            res = client.get("/mapa_reportes")
        assert res.status_code == 200
        assert b'"latitude"' in res.data

    def test_app_page(self, client):
        assert client.get("/app").status_code == 200

    def test_apoyo(self, client):
        assert client.get("/apoyo").status_code == 200

    def test_unknown_route_returns_404(self, client):
        assert client.get("/ruta-inexistente").status_code == 404

    # def test_home_renders_reports_label(self, client):
    #     with patch.object(_sb_manager, "get_reports_count", return_value=0):
    #         res = client.get("/")
    #     assert b"Reportes realizados" in res.data

    def test_home_injects_reports_count(self, client):
        with patch.object(_sb_manager, "get_reports_count", return_value=42):
            res = client.get("/")
        assert b"42" in res.data

    def test_admin_routes_are_gone(self, client):
        """Routes moved to ValidationReports project must not exist here."""
        assert client.get("/validacion_reportes").status_code == 404
        assert client.get("/reportes").status_code == 404
        assert client.post("/procesar").status_code == 404


# ─── /api/top_reportes ───────────────────────────────────────────────────────


class TestTopReportsApi:
    def test_returns_json_list(self, client):
        data = [{"id": "1", "importance_report": 10}]
        with patch.object(_sb_manager, "get_top_reports", return_value=data):
            res = client.get("/api/top_reportes")
        assert res.status_code == 200
        assert res.json == data

    def test_default_limit_is_10(self, client):
        with patch.object(_sb_manager, "get_top_reports", return_value=[]) as mock_top:
            client.get("/api/top_reportes")
        mock_top.assert_called_once_with(limit=10, state=None)

    def test_custom_limit_is_clamped_to_20(self, client):
        with patch.object(_sb_manager, "get_top_reports", return_value=[]) as mock_top:
            client.get("/api/top_reportes?limit=99")
        mock_top.assert_called_once_with(limit=20, state=None)

    def test_custom_limit_1_is_accepted(self, client):
        with patch.object(_sb_manager, "get_top_reports", return_value=[]) as mock_top:
            client.get("/api/top_reportes?limit=1")
        mock_top.assert_called_once_with(limit=1, state=None)

    def test_invalid_limit_falls_back_to_10(self, client):
        with patch.object(_sb_manager, "get_top_reports", return_value=[]) as mock_top:
            client.get("/api/top_reportes?limit=abc")
        mock_top.assert_called_once_with(limit=10, state=None)

    def test_state_filter_is_forwarded(self, client):
        with patch.object(_sb_manager, "get_top_reports", return_value=[]) as mock_top:
            client.get("/api/top_reportes?state=Jalisco")
        mock_top.assert_called_once_with(limit=10, state="Jalisco")

    def test_content_type_is_json(self, client):
        with patch.object(_sb_manager, "get_top_reports", return_value=[]):
            res = client.get("/api/top_reportes")
        assert "application/json" in res.content_type

    def test_empty_state_param_is_treated_as_none(self, client):
        with patch.object(_sb_manager, "get_top_reports", return_value=[]) as mock_top:
            client.get("/api/top_reportes?state=")
        mock_top.assert_called_once_with(limit=10, state=None)


# ─── /api/reporte/<id> ───────────────────────────────────────────────────────


class TestReporteDetailApi:
    _DETAIL = {
        "id": "uuid-123",
        "image_path": "uuid/photo.jpg",
        "street": "Av. Principal",
        "city": "Morelia",
        "comment": "Mucha basura acumulada",
        "waste_type": "inorgánico",
        "environment_type": "urbano",
        "importance_report": 5,
    }

    def test_found_returns_200_with_json(self, client):
        with (
            patch.object(_sb_manager, "get_report_detail", return_value=self._DETAIL),
            patch.object(
                _st_manager,
                "get_image_url",
                return_value="https://cdn.example.com/photo.jpg",
            ),
        ):
            res = client.get("/api/reporte/uuid-123")
        assert res.status_code == 200
        assert res.json["city"] == "Morelia"
        assert res.json["id"] == "uuid-123"

    def test_image_url_is_injected(self, client):
        with (
            patch.object(
                _sb_manager, "get_report_detail", return_value=dict(self._DETAIL)
            ),
            patch.object(
                _st_manager,
                "get_image_url",
                return_value="https://cdn.example.com/photo.jpg",
            ),
        ):
            res = client.get("/api/reporte/uuid-123")
        assert res.json["image_url"] == "https://cdn.example.com/photo.jpg"

    def test_no_image_path_sets_image_url_none(self, client):
        detail = {**self._DETAIL, "image_path": None}
        with patch.object(_sb_manager, "get_report_detail", return_value=detail):
            res = client.get("/api/reporte/uuid-123")
        assert res.json["image_url"] is None

    def test_not_found_returns_404(self, client):
        with patch.object(_sb_manager, "get_report_detail", return_value=None):
            res = client.get("/api/reporte/nonexistent")
        assert res.status_code == 404
        assert "error" in res.json

    def test_response_is_json_content_type(self, client):
        with (
            patch.object(_sb_manager, "get_report_detail", return_value=self._DETAIL),
            patch.object(_st_manager, "get_image_url", return_value=None),
        ):
            res = client.get("/api/reporte/uuid-123")
        assert "application/json" in res.content_type

    def test_get_image_url_not_called_when_no_image_path(self, client):
        detail = {**self._DETAIL, "image_path": None}
        with (
            patch.object(_sb_manager, "get_report_detail", return_value=detail),
            patch.object(_st_manager, "get_image_url") as mock_url,
        ):
            client.get("/api/reporte/uuid-123")
        mock_url.assert_not_called()


# ─── /lang/<code> ────────────────────────────────────────────────────────────


class TestSetLanguage:
    def test_valid_es_sets_session_and_redirects(self, client):
        res = client.get("/lang/es")
        assert res.status_code == 302
        with client.session_transaction() as sess:
            assert sess["lang"] == "es"

    def test_valid_en_sets_session_and_redirects(self, client):
        res = client.get("/lang/en")
        assert res.status_code == 302
        with client.session_transaction() as sess:
            assert sess["lang"] == "en"

    def test_invalid_code_does_not_set_session(self, client):
        client.get("/lang/fr")
        with client.session_transaction() as sess:
            assert "lang" not in sess

    def test_invalid_code_page_still_renders_in_spanish(self, client):
        """An unsupported lang code must not switch the UI away from Spanish."""
        client.get("/lang/fr")
        with patch.object(_sb_manager, "get_reports_count", return_value=0):
            res = client.get("/")
        # "Reportes realizados" is the Spanish label; if English were active it
        # would say "Reports submitted".
        assert b"Reportes realizados" in res.data

    def test_accept_language_header_does_not_change_locale(self, client):
        """Accept-Language must be ignored — locale is manual only."""
        with patch.object(_sb_manager, "get_reports_count", return_value=0):
            res = client.get("/", headers={"Accept-Language": "en-US,en;q=0.9"})
        assert b"Reportes realizados" in res.data

    def test_redirects_to_referrer_when_present(self, client):
        res = client.get("/lang/en", headers={"Referer": "http://localhost/ayuda"})
        assert res.headers["Location"] == "http://localhost/ayuda"

    def test_redirects_to_root_when_no_referrer(self, client):
        res = client.get("/lang/es")
        assert res.headers["Location"] == "/"
