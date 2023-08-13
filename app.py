import json

from flask import Flask
from flask import render_template
from flask import request

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


@app.route("/validacion_reportes")
def validate_reports():
    """Provide the page to validate reports by using a personal token
    Returns:
        html: validate reports page
    """
    reports = reports_services.get_reports_to_validate()
    return render_template("validate_reports.html", imagenes=reports)


@app.route("/procesar", methods=["POST"])
def procesar():
    token = request.form.get("token")
    accion = request.form.get("accion")
    imagen_id = request.form.get("image_id")

    if accion == "aceptar":
        # Hacer algo con el token cuando se presiona el botón "ACEPTAR"
        new_value = {"isValid": True}
    elif accion == "rechazar":
        # Hacer algo con el token cuando se presiona el botón "RECHAZAR"
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

    return render_template("mensaje.html", mensaje=mensaje)


if __name__ == "__main__":
    environment = settings.ENV_STATE
    if environment == "LOCAL" or environment == "DEVELOPMENT":
        app.run(debug=True)  # nosec
    else:
        app.run()
