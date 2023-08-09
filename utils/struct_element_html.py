import folium


def create_html_element(element):
    importance_level = element.get("importanceReport", None)
    labels = element.get("labels", None)
    register_date = element.get("created", None)
    comment = element.get("comments", None)
    url_image = element.get("uriImage", None)

    return folium.Html(
        f"""
            <!DOCTYPE html>
            <html>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
            <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet"/>
            <h4 align="center" style="color:red"><strong>Número de reportes: <u>{importance_level}</u><strong></h4>
            <div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
                <div class="panel panel-default" style="text-align: left; border-color: #ffffff !important;">
                    <div class="panel-heading" role="tab" id="headingOne" style="background: #ffffff!important;">
                        <h4 class="panel-title" style="color:cornflowerblue">
                            <a role="button" data-toggle="collapse" data-parent="#accordion" href="#collapseOne" aria-expanded="false" aria-controls="collapseOne">
                                <strong> <i class="fa fa-newspaper-o"></i> Información asociada <span class="glyphicon glyphicon-menu-down" aria-hidden="true" style="float: right;"></span></strong>
                            </a>
                        </h4>
                    </div>
                    <div id="collapseOne" class="panel-collapse collapse in" role="tabpanel" aria-labelledby="headingOne">
                        <div class="panel-body" align="left">
                            <p><strong>Etiquetas:</strong> {labels}</p>\
                            <p><strong>Fecha de registro:</strong> {register_date}</p>\
                            <p><strong>Comentarios del usuario:</strong> {comment}</p>
                        </div>
                    </div>
                </div>
            </div>
            <center>
                <img src="{url_image}"style="width:270px;height:180px;"/>
            </center>
        </html>
            """,
        script=True,
    )
