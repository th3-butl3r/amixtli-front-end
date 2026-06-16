"""Tests for all Flask routes in app.py."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt

from config.settings import settings
from managers.storage_manager import storage_manager as _st_manager
from managers.supabase_manager import supabase_manager as _sb_manager

# Shared valid credentials used across admin route tests
_SECRET = "unit-test-secret-32-bytes-padded!!"
_EMAILS = '["admin@test.com"]'

_PENDING_REPORT = {
    "id": "r1",
    "image_path": "uuid/photo.jpg",
    "street": "Main St",
    "city": "Morelia",
    "state": "Michoacán",
    "comment": "lots of trash",
    "waste_type": "inorgánico",
    "environment_type": "urbano",
    "importance_report": 3,
    "latitude": 19.5,
    "longitude": -101.6,
}


def _local_admin_ctx():
    """Context manager stack that satisfies _admin_guard() for all three checks."""
    return (
        patch.object(settings, "ENV_STATE", "LOCAL"),
        patch.object(settings, "SECRET_KEY", _SECRET),
        patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
    )


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

    def test_unknown_route(self, client):
        assert client.get("/ruta-inexistente").status_code == 404

    def test_home_renders_reports_label(self, client):
        with patch.object(_sb_manager, "get_reports_count", return_value=0):
            res = client.get("/")
        assert b"Reportes realizados" in res.data

    def test_home_injects_reports_count(self, client):
        with patch.object(_sb_manager, "get_reports_count", return_value=42):
            res = client.get("/")
        assert b"42" in res.data


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


# ─── Validación de reportes — GET ────────────────────────────────────────────


class TestValidacionReportesGet:
    def test_get_renders_login_form(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
        ):
            res = client.get("/validacion_reportes")
        assert res.status_code == 200
        assert b"token_personal" in res.data

    def test_get_blocked_in_production(self, client):
        with patch.object(settings, "ENV_STATE", "PRODUCTION"):
            res = client.get("/validacion_reportes")
        assert res.status_code == 404

    def test_get_blocked_in_staging(self, client):
        with patch.object(settings, "ENV_STATE", "STAGING"):
            res = client.get("/validacion_reportes")
        assert res.status_code == 404

    def test_get_blocked_in_development(self, client):
        with patch.object(settings, "ENV_STATE", "DEVELOPMENT"):
            res = client.get("/validacion_reportes")
        assert res.status_code == 404


# ─── Validación de reportes — POST ───────────────────────────────────────────


class TestValidacionReportesPost:
    def _make_token(self, email: str = "admin@test.com", expired: bool = False) -> str:
        payload = {"email": email}
        if expired:
            payload["exp"] = datetime.now(timezone.utc) - timedelta(hours=1)
        return jwt.encode(payload, _SECRET, algorithm="HS256")

    def test_post_empty_token_stays_on_form(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
        ):
            res = client.post("/validacion_reportes", data={"token_personal": ""})
        assert res.status_code == 200
        assert b"token_personal" in res.data

    def test_post_valid_token_authorized_redirects(self, client):
        token = self._make_token()
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
        ):
            res = client.post("/validacion_reportes", data={"token_personal": token})
        assert res.status_code == 302
        assert "reportes" in res.headers.get("Location", "")

    def test_post_invalid_token_stays_on_form(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
        ):
            res = client.post(
                "/validacion_reportes", data={"token_personal": "not.a.jwt"}
            )
        assert res.status_code == 200
        assert b"token_personal" in res.data

    def test_post_expired_token_stays_on_form(self, client):
        token = self._make_token(expired=True)
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
        ):
            res = client.post("/validacion_reportes", data={"token_personal": token})
        assert res.status_code == 200
        assert b"token_personal" in res.data

    def test_post_unauthorized_email_stays_on_form(self, client):
        token = self._make_token(email="hacker@evil.com")
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
        ):
            res = client.post("/validacion_reportes", data={"token_personal": token})
        assert res.status_code == 200
        assert b"token_personal" in res.data

    def test_post_malformed_allowed_emails_blocks_route(self, client):
        """Malformed ALLOWED_EMAILS → route is invisible (404) before reaching form."""
        token = self._make_token()
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", "not-valid-json"),
        ):
            res = client.post("/validacion_reportes", data={"token_personal": token})
        assert res.status_code == 404

    def test_post_blocked_non_local(self, client):
        with patch.object(settings, "ENV_STATE", "PRODUCTION"):
            res = client.post("/validacion_reportes", data={"token_personal": "x"})
        assert res.status_code == 404


# ─── _admin_guard: credential checks ─────────────────────────────────────────


class TestAdminGuard:
    """All combinations that must return 404 regardless of the route hit."""

    def _get_form(self, client, *, env: str, secret: str, emails: str):
        with (
            patch.object(settings, "ENV_STATE", env),
            patch.object(settings, "SECRET_KEY", secret),
            patch.object(settings, "ALLOWED_EMAILS", emails),
        ):
            return client.get("/validacion_reportes")

    def test_blocked_when_secret_key_empty(self, client):
        assert (
            self._get_form(client, env="LOCAL", secret="", emails=_EMAILS).status_code
            == 404
        )

    def test_blocked_when_secret_key_whitespace_only(self, client):
        assert (
            self._get_form(client, env="LOCAL", secret="   ", emails=_EMAILS).status_code
            == 404
        )

    def test_blocked_when_allowed_emails_empty_string(self, client):
        assert (
            self._get_form(client, env="LOCAL", secret=_SECRET, emails="").status_code
            == 404
        )

    def test_blocked_when_allowed_emails_whitespace_only(self, client):
        assert (
            self._get_form(client, env="LOCAL", secret=_SECRET, emails="  ").status_code
            == 404
        )

    def test_blocked_when_allowed_emails_empty_list(self, client):
        assert (
            self._get_form(client, env="LOCAL", secret=_SECRET, emails="[]").status_code
            == 404
        )

    def test_blocked_when_allowed_emails_not_a_list(self, client):
        assert (
            self._get_form(
                client, env="LOCAL", secret=_SECRET, emails='"just-a-string"'
            ).status_code
            == 404
        )

    def test_blocked_when_allowed_emails_malformed_json(self, client):
        assert (
            self._get_form(
                client, env="LOCAL", secret=_SECRET, emails="not-json"
            ).status_code
            == 404
        )

    def test_accessible_when_all_credentials_valid(self, client):
        assert (
            self._get_form(
                client, env="LOCAL", secret=_SECRET, emails=_EMAILS
            ).status_code
            == 200
        )

    def test_guard_also_applies_to_reportes(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", ""),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
        ):
            res = client.get("/reportes")
        assert res.status_code == 404

    def test_guard_also_applies_to_procesar(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", "[]"),
        ):
            res = client.post(
                "/procesar",
                data={"accion": "aceptar", "report_id": "1"},
            )
        assert res.status_code == 404


# ─── /reportes ────────────────────────────────────────────────────────────────


class TestReportes:
    def test_get_renders_reports(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
            patch.object(
                _sb_manager, "get_pending_reports", return_value=[_PENDING_REPORT]
            ),
            patch.object(
                _st_manager,
                "get_image_url",
                return_value="https://cdn.example.com/photo.jpg",
            ),
        ):
            res = client.get("/reportes")
        assert res.status_code == 200

    def test_get_renders_empty_list(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
            patch.object(_sb_manager, "get_pending_reports", return_value=[]),
        ):
            res = client.get("/reportes")
        assert res.status_code == 200

    def test_get_blocked_non_local(self, client):
        with patch.object(settings, "ENV_STATE", "PRODUCTION"):
            res = client.get("/reportes")
        assert res.status_code == 404

    def test_get_passes_token_to_template(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
            patch.object(_sb_manager, "get_pending_reports", return_value=[]),
        ):
            res = client.get("/reportes?token_user=my-token")
        assert res.status_code == 200

    def test_report_without_image_path_gets_none_url(self, client):
        report_no_img = {**_PENDING_REPORT, "image_path": None}
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
            patch.object(
                _sb_manager, "get_pending_reports", return_value=[report_no_img]
            ),
            patch.object(_st_manager, "get_image_url") as mock_url,
        ):
            res = client.get("/reportes")
        assert res.status_code == 200
        mock_url.assert_not_called()


# ─── /procesar ────────────────────────────────────────────────────────────────


class TestProcesar:
    def test_aceptar_success(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
            patch.object(_sb_manager, "approve_report", return_value=True),
        ):
            res = client.post(
                "/procesar",
                data={"accion": "aceptar", "report_id": "id-1"},
            )
        assert res.status_code == 200
        assert "aprobado" in res.data.decode("utf-8")

    def test_aceptar_with_waste_and_env_types(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
            patch.object(
                _sb_manager, "approve_report", return_value=True
            ) as mock_approve,
        ):
            res = client.post(
                "/procesar",
                data={
                    "accion": "aceptar",
                    "report_id": "id-1",
                    "waste_type": "inorgánico",
                    "environment_type": "urbano",
                },
            )
        assert res.status_code == 200
        mock_approve.assert_called_once_with(
            "id-1", waste_type="inorgánico", environment_type="urbano"
        )

    def test_rechazar_success(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
            patch.object(_sb_manager, "delete_report", return_value=True),
        ):
            res = client.post(
                "/procesar",
                data={"accion": "rechazar", "report_id": "id-2"},
            )
        assert res.status_code == 200
        assert "rechazado" in res.data.decode("utf-8")

    def test_rechazar_does_not_delete_image(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
            patch.object(_sb_manager, "delete_report", return_value=True),
            patch.object(_st_manager, "delete_image") as mock_del,
        ):
            client.post(
                "/procesar",
                data={
                    "accion": "rechazar",
                    "report_id": "id-2",
                    "image_path": "uuid/p.jpg",
                },
            )
        mock_del.assert_not_called()

    def test_eliminar_with_image_deletes_storage(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
            patch.object(_sb_manager, "delete_report", return_value=True),
            patch.object(_st_manager, "delete_image") as mock_del,
        ):
            res = client.post(
                "/procesar",
                data={
                    "accion": "eliminar",
                    "report_id": "id-3",
                    "image_path": "uuid/photo.jpg",
                },
            )
        assert res.status_code == 200
        assert "eliminad" in res.data.decode("utf-8")
        mock_del.assert_called_once_with("uuid/photo.jpg")

    def test_eliminar_without_image_skips_storage(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
            patch.object(_sb_manager, "delete_report", return_value=True),
            patch.object(_st_manager, "delete_image") as mock_del,
        ):
            res = client.post(
                "/procesar",
                data={"accion": "eliminar", "report_id": "id-3"},
            )
        assert res.status_code == 200
        mock_del.assert_not_called()

    def test_unknown_action_returns_message(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
        ):
            res = client.post(
                "/procesar",
                data={"accion": "foo", "report_id": "id-1"},
            )
        assert res.status_code == 200
        assert "no reconocida" in res.data.decode("utf-8")

    def test_action_failure_shows_error_message(self, client):
        with (
            patch.object(settings, "ENV_STATE", "LOCAL"),
            patch.object(settings, "SECRET_KEY", _SECRET),
            patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
            patch.object(_sb_manager, "approve_report", return_value=False),
        ):
            res = client.post(
                "/procesar",
                data={"accion": "aceptar", "report_id": "id-1"},
            )
        assert res.status_code == 200
        assert "error" in res.data.decode("utf-8").lower()

    def test_procesar_blocked_non_local(self, client):
        with patch.object(settings, "ENV_STATE", "PRODUCTION"):
            res = client.post(
                "/procesar",
                data={"accion": "aceptar", "report_id": "1"},
            )
        assert res.status_code == 404
