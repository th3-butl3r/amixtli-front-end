from dotenv import dotenv_values
from flask import Flask
from flask import render_template

variables = dotenv_values("config/.env")
app = Flask(__name__)


@app.route("/inicio")
@app.route("/carto_group")
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/contacto")
def contact():
    return render_template("contact.html")


@app.route("/ayuda")
def help():
    return render_template("help.html")


@app.route("/politica_privacidad")
def privacy_policy():
    return render_template("privacy_policy.html")


# TODO: Añadir las páginas de reportes y de mapas

if __name__ == "__main__":
    environment = variables["ENV_STATE"]
    if environment == "LOCAL" or environment == "DEVELOPMENT":
        app.run(debug=True)  # nosec
    else:
        app.run()
