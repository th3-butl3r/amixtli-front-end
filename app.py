from flask import Flask
from flask import render_template

from config.settings import settings
from utils.make_map import build_map

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
    map_html = build_map()
    return render_template("map.html", map_html=map_html)


# TODO: Añadir las páginas de reportes

if __name__ == "__main__":
    environment = settings.ENV_STATE
    if environment == "LOCAL" or environment == "DEVELOPMENT":
        app.run(debug=True)  # nosec
    else:
        app.run()
