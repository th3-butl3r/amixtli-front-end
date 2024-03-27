import ast
import json

from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from config.settings import settings
from services.map import map_services
from services.reports import reports_services

app = Flask(__name__)


@app.route("/inicio")
@app.route("/carto_group")
@app.route("/")
def home():
    """Provide the main page

    Returns:
        html: home page
    """
    return render_template("index.html")


@app.route("/contacto")
def contact():
    """Provide the contact page

    Returns:
        html: contact page
    """
    return render_template("contact.html")


@app.route("/ayuda")
def help():
    """Provide the help page

    Returns:
        html: help page
    """
    return render_template("help.html")


@app.route("/politica_privacidad")
def privacy_policy():
    """Provide the page with privacy policy

    Returns:
        html: privacy policy page
    """
    return render_template("privacy_policy.html")


@app.route("/mapa_reportes")
def map():
    """Provide the map page where the user can watch the different problems
    Returns:
        html: map page
    """
    map_html = map_services.build_map()
    return render_template("map.html", map_html=map_html)


# Functions AUX TO VALIDATE REPORTS
@app.route("/validacion_reportes", methods=["GET", "POST"])
def mostrar_formulario():
    mensaje_error = None
    if request.method == "POST":
        email = request.form.get("email_personal")
        try:
            emails_validos = ast.literal_eval(settings.ALLOWED_EMAILS)
        except (ValueError, SyntaxError):
            emails_validos = []

        if email in emails_validos:
            # Redirige a la página deseada si el token es correcto
            return redirect(url_for("validate_reports"))
        else:
            mensaje_error = "El correo no está dentro de la lista de confianza. Contacta con el administrador si quieres ingresar a esta lista."

    # Renderiza el formulario si es un método GET o si el token es incorrecto
    return render_template("login_form.html", mensaje_error=mensaje_error)


@app.route("/reportes")
def validate_reports():
    """Provide the page to validate reports by using a personal token
    Returns:
        html: validate reports page
    """
    reports = reports_services.get_reports_to_validate()
    return render_template(
        "validate_reports.html",
        imagenes=reports,
    )


@app.route("/procesar", methods=["POST"])
def procesar():
    token = request.form.get("token")
    accion = request.form.get("accion")
    imagen_id = request.form.get("image_id")

    if accion == "aceptar":
        # Hacer algo con el token cuando se presiona el botón "ACEPTAR"
        new_value = {"isValid": True}
        response = reports_services.update_report(
            id_report=imagen_id, new_value=new_value, token=token
        )
    elif accion == "eliminar":
        # Hacer algo con el token cuando se presiona el botón "ELIMINAR"
        response = reports_services.delete_report(id_report=imagen_id, token=token)

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

    return render_template("mensaje.html", mensaje=mensaje)


@app.route("/obtener_reportes", methods=["GET"])
def get_reports():
    list_reports = reports_services.get_reports()
    return jsonify(list_reports)


if __name__ == "__main__":
    environment = settings.ENV_STATE
    if environment == "LOCAL" or environment == "DEVELOPMENT":
        app.run(host="0.0.0.0", port=5000, debug=True)  # nosec

    else:
        app.run()
