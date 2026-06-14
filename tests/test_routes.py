"""Tests for all Flask routes in app.py."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt


from config.settings import settings

# Shared valid credentials used across admin route tests
_SECRET = "unit-test-secret-32-bytes-padded!!"
_EMAILS = '["admin@test.com"]'


def _local_admin_ctx():
    """Context manager stack that satisfies _admin_guard() for all three checks."""
    return (
        patch.object(settings, "ENV_STATE", "LOCAL"),
        patch.object(settings, "SECRET_KEY", _SECRET),
        patch.object(settings, "ALLOWED_EMAILS", _EMAILS),
    )


# ─── Public routes ───────────────────────────────────────────────────────────


class TestPublicRoutes:
    def test_home_root(self, client):
        assert client.get("/").status_code == 200

    def test_home_inicio(self, client):
        assert client.get("/inicio").status_code == 200

    def test_home_carto_group(self, client):
        assert client.get("/carto_group").status_code == 200

    def test_contacto(self, client):
        assert client.get("/contacto").status_code == 200

    def test_ayuda(self, client):
        assert client.get("/ayuda").status_code == 200

    def test_politica_privacidad(self, client):
        assert client.get("/politica_privacidad").status_code == 200

    def test_mapa_reportes(self, client):
        assert client.get("/mapa_reportes").status_code == 200

    def test_app_page(self, client):
        assert client.get("/app").status_code == 200

    def test_apoyo(self, client):
        assert client.get("/apoyo").status_code == 200

    def test_unknown_route(self, client):
        assert client.get("/ruta-inexistente").status_code == 404

    def test_home_renders_current_year(self, client):
        res = client.get("/")
        assert str(datetime.now().year).encode() in res.data


# ─── Validación de reportes — GET ────────────────────────────────────────────


class TestValidacionReportesGet:
    def test_get_renders_login_form(self, client):
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS):
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

    def test_post_valid_token_authorized_redirects(self, client):
        token = self._make_token()
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS):
            res = client.post("/validacion_reportes", data={"token_personal": token})
        assert res.status_code == 302
        assert "reportes" in res.headers.get("Location", "")

    def test_post_invalid_token_stays_on_form(self, client):
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS):
            res = client.post(
                "/validacion_reportes", data={"token_personal": "not.a.jwt"}
            )
        assert res.status_code == 200
        assert b"token_personal" in res.data

    def test_post_expired_token_stays_on_form(self, client):
        token = self._make_token(expired=True)
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS):
            res = client.post("/validacion_reportes", data={"token_personal": token})
        assert res.status_code == 200
        assert b"token_personal" in res.data

    def test_post_unauthorized_email_stays_on_form(self, client):
        token = self._make_token(email="hacker@evil.com")
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS):
            res = client.post("/validacion_reportes", data={"token_personal": token})
        assert res.status_code == 200
        assert b"token_personal" in res.data

    def test_post_malformed_allowed_emails_blocks_route(self, client):
        """Malformed ALLOWED_EMAILS → route is invisible (404) before reaching form."""
        token = self._make_token()
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", "not-valid-json"):
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
        with patch.object(settings, "ENV_STATE", env), patch.object(
            settings, "SECRET_KEY", secret
        ), patch.object(settings, "ALLOWED_EMAILS", emails):
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
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", ""
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS), patch(
            "services.reports.reports_services.get_reports_to_validate", return_value=[]
        ):
            res = client.get("/reportes")
        assert res.status_code == 404

    def test_guard_also_applies_to_procesar(self, client):
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", "[]"):
            res = client.post(
                "/procesar",
                data={"token": "t", "accion": "aceptar", "image_id": "1"},
            )
        assert res.status_code == 404


# ─── /reportes ────────────────────────────────────────────────────────────────


class TestReportes:
    _REPORTS = [
        (
            "http://img.example.com/1.jpg",
            "basura",
            "mucha basura",
            "Morelia",
            "Michoacán",
            "id-1",
        )
    ]

    def test_get_renders_reports(self, client):
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS), patch(
            "services.reports.reports_services.get_reports_to_validate",
            return_value=self._REPORTS,
        ):
            res = client.get("/reportes")
        assert res.status_code == 200

    def test_get_renders_empty_list(self, client):
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS), patch(
            "services.reports.reports_services.get_reports_to_validate", return_value=[]
        ):
            res = client.get("/reportes")
        assert res.status_code == 200

    def test_get_blocked_non_local(self, client):
        with patch.object(settings, "ENV_STATE", "PRODUCTION"):
            res = client.get("/reportes")
        assert res.status_code == 404

    def test_get_passes_token_to_template(self, client):
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS), patch(
            "services.reports.reports_services.get_reports_to_validate", return_value=[]
        ):
            res = client.get("/reportes?token_user=my-token")
        assert res.status_code == 200


# ─── /procesar ────────────────────────────────────────────────────────────────


def _mock_response(status_code: int, body: dict = None) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = json.dumps(body or {})
    return mock


class TestProcesar:
    def test_aceptar_success(self, client):
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS), patch(
            "services.reports.reports_services.update_report",
            return_value=_mock_response(200),
        ):
            res = client.post(
                "/procesar",
                data={"token": "tok", "accion": "aceptar", "image_id": "123"},
            )
        assert res.status_code == 200
        assert "éxito".encode("utf-8") in res.data

    def test_rechazar_success(self, client):
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS), patch(
            "services.reports.reports_services.update_report",
            return_value=_mock_response(201),
        ):
            res = client.post(
                "/procesar",
                data={"token": "tok", "accion": "rechazar", "image_id": "456"},
            )
        assert res.status_code == 200
        assert "éxito".encode("utf-8") in res.data

    def test_api_error_with_error_field(self, client):
        body = {"errors": {"error": "Reporte no encontrado"}}
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS), patch(
            "services.reports.reports_services.update_report",
            return_value=_mock_response(400, body),
        ):
            res = client.post(
                "/procesar",
                data={"token": "tok", "accion": "aceptar", "image_id": "999"},
            )
        assert res.status_code == 200
        assert "Reporte no encontrado".encode("utf-8") in res.data

    def test_api_error_without_error_field_uses_default(self, client):
        body = {"errors": {}}
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS), patch(
            "services.reports.reports_services.update_report",
            return_value=_mock_response(400, body),
        ):
            res = client.post(
                "/procesar",
                data={"token": "tok", "accion": "aceptar", "image_id": "999"},
            )
        assert res.status_code == 200
        assert "administrador".encode("utf-8") in res.data

    def test_api_error_no_errors_key(self, client):
        body = {"message": "Internal server error"}
        with patch.object(settings, "ENV_STATE", "LOCAL"), patch.object(
            settings, "SECRET_KEY", _SECRET
        ), patch.object(settings, "ALLOWED_EMAILS", _EMAILS), patch(
            "services.reports.reports_services.update_report",
            return_value=_mock_response(500, body),
        ):
            res = client.post(
                "/procesar",
                data={"token": "tok", "accion": "aceptar", "image_id": "999"},
            )
        assert res.status_code == 200
        assert "administrador".encode("utf-8") in res.data

    def test_procesar_blocked_non_local(self, client):
        with patch.object(settings, "ENV_STATE", "PRODUCTION"):
            res = client.post(
                "/procesar",
                data={"token": "tok", "accion": "aceptar", "image_id": "1"},
            )
        assert res.status_code == 404
