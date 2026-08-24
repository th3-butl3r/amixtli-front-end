import os
from concurrent.futures import ThreadPoolExecutor

import sentry_sdk
from flask import Flask
from flask import Response
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask_babel import Babel
from flask_babel import get_locale
from loguru import logger
from sentry_sdk.integrations.flask import FlaskIntegration

from config.settings import settings
from managers.storage_manager import storage_manager
from managers.supabase_manager import supabase_manager

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FlaskIntegration()],
        environment=settings.ENV_STATE.lower(),
        # Captura el 10 % de las transacciones para monitoreo de rendimiento
        traces_sample_rate=0.1,
        # Sin datos personales: IPs y emails no se envían a Sentry
        send_default_pii=False,
    )
    logger.info("BL > sentry_sdk.init() - Sentry initialized")

app = Flask(__name__)
app.secret_key = settings.SECRET_KEY or os.urandom(24)

babel = Babel()


def _get_locale() -> str:
    """Return the active UI locale from the session (defaults to Spanish)."""
    return session.get("lang", "es")


babel.init_app(app, locale_selector=_get_locale)


@app.context_processor
def inject_globals() -> dict:
    """Inject shared variables into all template contexts."""
    from datetime import datetime

    return {
        "env_state": settings.ENV_STATE,
        "current_year": datetime.now().year,
        "current_lang": str(get_locale()),
    }


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


@app.route("/lang/<code>")
def set_language(code: str) -> Response:
    """Set the UI language preference in the session and redirect back.

    Args:
        code: Language code — 'es' or 'en'.

    Returns:
        Redirect to the referring page or home.
    """
    logger.info(f"BL > set_language() - lang={code}")
    if code in ("es", "en"):
        session["lang"] = code
    return redirect(request.referrer or "/")


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
