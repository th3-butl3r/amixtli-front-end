import json
from concurrent.futures import ThreadPoolExecutor

import jwt
from flask import Flask
from flask import Response
from flask import abort
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from loguru import logger

from config.settings import settings
from managers.storage_manager import storage_manager
from managers.supabase_manager import supabase_manager

app = Flask(__name__)


@app.context_processor
def inject_globals() -> dict:
    """Inject shared variables into all template contexts."""
    from datetime import datetime

    return {"env_state": settings.ENV_STATE, "current_year": datetime.now().year}


@app.route("/health")
def health():
    try:
        result = supabase_manager.health_db()
        if result is True:
            return jsonify({"status": "Online", "db": "Connected"}), 200
        else:
            return jsonify({"status": "Error", "db": "Connection Fail"}), 400
    except Exception as e:
        return (
            jsonify({"status": "Error", "db": "Connection Fail", "detail": str(e)}),
            503,
        )


@app.route("/inicio")
@app.route("/carto_group")
@app.route("/")
def home() -> str:
    """Render the main landing page with the total report count from Supabase.

    Returns:
        Rendered HTML of the home page.
    """
    logger.info("BL > home() - Rendering home page")

    reports_count = supabase_manager.get_reports_count()
    return render_template("index.html", reports_count=reports_count)


@app.route("/contacto")
def contact() -> str:
    """Render the contact page.

    Returns:
        Rendered HTML of the contact page.
    """
    logger.info("BL > contact() - Rendering contact page")
    return render_template("contact.html")


@app.route("/ayuda")
def help() -> str:
    """Render the help page.

    Returns:
        Rendered HTML of the help page.
    """
    logger.info("BL > help() - Rendering help page")
    return render_template("help.html")


@app.route("/politica_privacidad")
def privacy_policy() -> str:
    """Render the privacy policy page.

    Returns:
        Rendered HTML of the privacy policy page.
    """
    logger.info("BL > privacy_policy() - Rendering privacy policy page")
    return render_template("privacy_policy.html")


@app.route("/mapa_reportes")
def map() -> str:
    """Render the map page with approved reports loaded from Supabase.

    Returns:
        Rendered HTML of the map page with serialised report markers.
    """
    logger.info("BL > map() - Rendering map page")
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_reports = pool.submit(supabase_manager.get_map_reports)
        f_top = pool.submit(supabase_manager.get_top_reports, 10)
        f_states = pool.submit(supabase_manager.get_available_states)
        reports = f_reports.result()
        top_reports = f_top.result()
        states = f_states.result()
    logger.info(
        f"BL > map() - Passing {len(reports)} markers, {len(top_reports)} top reports, {len(states)} states"
    )
    return render_template(
        "map.html", reports=reports, top_reports=top_reports, states=states
    )


@app.route("/api/reporte/<report_id>")
def report_detail(report_id: str) -> Response:
    """Return full detail for a single approved report as JSON.

    Called by the map front-end when the user clicks a marker.

    Args:
        report_id: UUID of the report to fetch.

    Returns:
        JSON body with report fields, or 404 if not found.
    """
    logger.info(f"BL > report_detail() - Request for id={report_id}")
    detail = supabase_manager.get_report_detail(report_id)
    if detail is None:
        logger.warning(f"BL > report_detail() - Not found id={report_id}")
        return make_response(jsonify({"error": "not found"}), 404)

    image_path = detail.get("image_path")
    detail["image_url"] = (
        storage_manager.get_image_url(image_path) if image_path else None
    )

    return jsonify(detail)


@app.route("/api/top_reportes")
def top_reports() -> Response:
    """Return the top N approved reports ordered by importance score as JSON.

    Accepts optional query params:
        limit (int, default 10): Maximum number of results.
        state (str, optional): Filter by Mexican state name.

    Returns:
        JSON array of report dicts.
    """
    try:
        limit = int(request.args.get("limit", 10))
        limit = max(1, min(limit, 20))
    except (TypeError, ValueError):
        limit = 10
    state = request.args.get("state") or None
    logger.info(f"BL > top_reports() - limit={limit}, state={state}")
    data = supabase_manager.get_top_reports(limit=limit, state=state)
    return jsonify(data)


@app.route("/apoyo")
def support() -> str:
    """Render the support/donation page.

    Returns:
        Rendered HTML of the support page.
    """
    logger.info("BL > support() - Rendering support page")
    return render_template("support.html", bmac_url=settings.BUY_ME_A_COFFEE_URL)


@app.route("/app")
def our_app() -> str:
    """Render the app presentation page.

    Returns:
        Rendered HTML of the app page.
    """
    logger.info("BL > our_app() - Rendering app page")
    return render_template("app.html")


def _admin_guard() -> None:
    """Abort 404 unless all admin security conditions are met.

    Conditions checked in order:
    - ENV_STATE must be LOCAL.
    - SECRET_KEY must be present and non-empty.
    - ALLOWED_EMAILS must be present, non-empty, parseable, and contain at
      least one address.

    Always returns 404 on failure so the routes remain invisible outside LOCAL.
    """
    if settings.ENV_STATE != "LOCAL":
        logger.warning("BL > _admin_guard() - Blocked: environment is not LOCAL")
        abort(404)
    if not (settings.SECRET_KEY or "").strip():
        logger.warning("BL > _admin_guard() - Blocked: SECRET_KEY is not configured")
        abort(404)
    raw_emails = (settings.ALLOWED_EMAILS or "").strip()
    if not raw_emails:
        logger.warning("BL > _admin_guard() - Blocked: ALLOWED_EMAILS is not configured")
        abort(404)
    try:
        emails = json.loads(raw_emails)
    except (ValueError, SyntaxError):
        logger.warning(
            "BL > _admin_guard() - Blocked: ALLOWED_EMAILS is not valid JSON list"
        )
        abort(404)
    if not isinstance(emails, list) or not emails:
        logger.warning("BL > _admin_guard() - Blocked: ALLOWED_EMAILS list is empty")
        abort(404)


@app.route("/validacion_reportes", methods=["GET", "POST"])
def mostrar_formulario() -> str:
    """Render the JWT login form and validate the submitted token.

    On POST, decodes the JWT and checks the email against ALLOWED_EMAILS.
    On success redirects to the reports validation page.

    Returns:
        Redirect to validate_reports on success, or the login form with an
        error message on failure.
    """
    _admin_guard()
    mensaje_error = None
    if request.method == "POST":
        logger.info("BL > mostrar_formulario() - Processing token login")
        token_personal = (request.form.get("token_personal") or "").strip()
        if not token_personal:
            mensaje_error = "Token vacío"
            logger.warning("BL > mostrar_formulario() - Empty token received")
            return render_template("login_form.html", mensaje_error=mensaje_error)
        try:
            emails_validos = json.loads(settings.ALLOWED_EMAILS)
        except (ValueError, SyntaxError):
            emails_validos = []
        email = None
        try:
            payload = jwt.decode(
                token_personal, settings.SECRET_KEY, algorithms=["HS256"]
            )
            email = payload.get("email", None)
        except jwt.ExpiredSignatureError:
            mensaje_error = "Token expirado"
            logger.warning("BL > mostrar_formulario() - Expired token received")
        except jwt.InvalidTokenError as e:
            mensaje_error = "Token inválido"
            logger.warning(f"BL > mostrar_formulario() - Invalid token: {e}")

        if email in emails_validos:
            logger.info(f"BL > mostrar_formulario() - Authorized access for {email}")
            return redirect(url_for("validate_reports", token_user=token_personal))
        else:
            mensaje_error = "El token no es válido. Contacta con el administrador si aún no tienes tu token personal."
            logger.warning("BL > mostrar_formulario() - Unauthorized email in token")

    return render_template("login_form.html", mensaje_error=mensaje_error)


@app.route("/reportes")
def validate_reports() -> str:
    """Render the report moderation page for authorized admins.

    Returns:
        Rendered HTML of the validate reports page.
    """
    _admin_guard()
    logger.info("BL > validate_reports() - Rendering reports validation page")
    raw_reports = supabase_manager.get_pending_reports()
    for r in raw_reports:
        ip = r.get("image_path")
        r["image_url"] = storage_manager.get_image_url(ip) if ip else None
    logger.info(f"BL > validate_reports() - Passing {len(raw_reports)} pending reports")
    return render_template("validate_reports.html", reportes=raw_reports)


@app.route("/procesar", methods=["POST"])
def procesar() -> str:
    """Process a moderation action (aceptar / rechazar / eliminar) on a report.

    - aceptar:  sets status to 'aprobado'; report becomes visible on the public map.
    - rechazar: deletes the DB record; image is kept in storage for model training.
    - eliminar: deletes both the DB record and the image from storage.

    Returns:
        Rendered HTML confirmation message page.
    """
    _admin_guard()
    accion = request.form.get("accion")
    report_id = request.form.get("report_id")
    image_path = (request.form.get("image_path") or "").strip()
    logger.info(f"BL > procesar() - action='{accion}' for id={report_id}")

    ok = False
    if accion == "aceptar":
        waste_type = request.form.get("waste_type") or None
        env_type = request.form.get("environment_type") or None
        logger.debug(f"BL > procesar() - waste_type='{waste_type}' env_type='{env_type}'")
        ok = supabase_manager.approve_report(
            report_id,
            waste_type=waste_type,
            environment_type=env_type,
        )
        mensaje = "Reporte aprobado. Ya es visible en el mapa público."
    elif accion == "rechazar":
        ok = supabase_manager.delete_report(report_id)
        mensaje = "Reporte rechazado. La imagen se conserva para entrenamiento."
    elif accion == "eliminar":
        if image_path:
            storage_manager.delete_image(image_path)
        ok = supabase_manager.delete_report(report_id)
        mensaje = "Reporte y su imagen eliminados permanentemente."
    else:
        mensaje = "Acción no reconocida."
        logger.warning(f"BL > procesar() - Unknown action='{accion}'")

    if not ok and accion in ("aceptar", "rechazar", "eliminar"):
        mensaje = "Ha ocurrido un error. Por favor inténtalo de nuevo."
        logger.error(f"BL > procesar() - Failed action='{accion}' for id={report_id}")

    return render_template("mensaje.html", mensaje=mensaje)


@app.errorhandler(404)
def page_not_found(e: Exception) -> tuple:
    """Render the custom 404 page.

    Returns:
        Rendered HTML of the 404 page with a 404 status code.
    """
    logger.warning(f"BL > page_not_found() - 404 for path={request.path}")
    return render_template("404.html"), 404


if __name__ == "__main__":
    environment = settings.ENV_STATE
    if environment == "LOCAL" or environment == "DEVELOPMENT":
        app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)  # nosec
    else:
        app.run()
