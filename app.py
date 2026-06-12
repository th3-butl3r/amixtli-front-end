import ast
import json

import jwt
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from loguru import logger

from config.settings import settings
from services.map import map_services
from services.reports import reports_services

app = Flask(__name__)


@app.route("/inicio")
@app.route("/carto_group")
@app.route("/")
def home() -> str:
    """Render the main landing page.

    Returns:
        Rendered HTML of the home page.
    """
    logger.info("BL > home() - Rendering home page")
    return render_template("index.html")


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
    """Render the map page with all validated reports.

    Returns:
        Rendered HTML of the map page.
    """
    logger.info("BL > map() - Building and rendering map page")
    map_html = map_services.build_map()
    return render_template("map.html", map_html=map_html)


@app.route("/validacion_reportes", methods=["GET", "POST"])
def mostrar_formulario() -> str:
    """Render the JWT login form and validate the submitted token.

    On POST, decodes the JWT and checks the email against ALLOWED_EMAILS.
    On success redirects to the reports validation page.

    Returns:
        Redirect to validate_reports on success, or the login form with an
        error message on failure.
    """
    mensaje_error = None
    if request.method == "POST":
        logger.info("BL > mostrar_formulario() - Processing token login")
        token_personal = request.form.get("token_personal")
        try:
            emails_validos = ast.literal_eval(settings.ALLOWED_EMAILS)
        except (ValueError, SyntaxError):
            emails_validos = []
        try:
            payload = jwt.decode(
                token_personal, settings.SECRET_KEY, algorithms=["HS256"]
            )
            email = payload.get("email", None)
        except jwt.ExpiredSignatureError:
            mensaje_error = "Token expirado"
            logger.warning("BL > mostrar_formulario() - Expired token received")
        except jwt.InvalidTokenError:
            mensaje_error = "Token inválido"
            logger.warning("BL > mostrar_formulario() - Invalid token received")

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
    logger.info("BL > validate_reports() - Rendering reports validation page")
    token_user = request.args.get("token_user", "")
    reports = reports_services.get_reports_to_validate()
    return render_template(
        "validate_reports.html", imagenes=reports, token_user=token_user
    )


@app.route("/procesar", methods=["POST"])
def procesar() -> str:
    """Process an accept or reject action on a report.

    Returns:
        Rendered HTML confirmation message page.
    """
    token = request.form.get("token")
    accion = request.form.get("accion")
    imagen_id = request.form.get("image_id")
    logger.info(f"BL > procesar() - Processing action='{accion}' for report id={imagen_id}")

    if accion == "aceptar":
        new_value = {"isValid": True}
    elif accion == "rechazar":
        new_value = {"isValid": False}

    response = reports_services.update_report(
        id_report=imagen_id, new_value=new_value, token=token
    )
    if response.status_code in [200, 201]:
        mensaje = "¡El reporte se ha actualizado con éxito! Muchas gracias por validar que el reporte sea un reporte válido y permitirnos mejorar el sistema."
    else:
        txt = json.loads(response.text)
        errors = txt.get("errors", None)
        if errors is None:
            mensaje = "Ha ocurrido un error, por favor contacte al administrador"
        else:
            mensaje = str(
                errors.get(
                    "error",
                    "Parece que algo ha fallado durante la actualización del reporte. Por favor, inténtelo más tarde o contacte al administrador",
                )
            )
        logger.error(f"BL > procesar() - Failed to update report id={imagen_id}: {mensaje}")

    return render_template("mensaje.html", mensaje=mensaje)


if __name__ == "__main__":
    environment = settings.ENV_STATE
    if environment == "LOCAL" or environment == "DEVELOPMENT":
        app.run(host="0.0.0.0", port=5000, debug=True)  # nosec
    else:
        app.run()
