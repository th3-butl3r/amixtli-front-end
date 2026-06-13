import html as html_escape_lib
import branca
import folium
from loguru import logger

from managers.amixtli_manager import amixtli_manager


class MapServices:
    @classmethod
    def build_map(cls) -> str:
        """Build the interactive folium map from validated reports.

        Returns:
            Raw HTML string of the rendered map, ready to embed in a template.
        """
        logger.info("BL > MapServices.build_map() - Building map")
        docs = amixtli_manager.get_reports(is_valid=True)
        Mexico = (19.9998589, -100.9994856)
        ENES_Computo = (19.649269, -101.222084)
        maping = folium.Map(
            location=Mexico,
            titles="Mexico",
            zoom_start=7,
            max_zoom=19,
        )
        html = folium.Html(
            """
                <!DOCTYPE html>
                <html>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
                <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet"/>
               <div class="panel-group" id="accordion" role="tablist" aria-multiselectable="true">
                    <div class="panel panel-default" style="text-align: left; border-color: #ffffff !important;">
                        <div class="panel-heading" role="tab" id="headingOne" style="background: #ffffff!important;">
                            <h4 class="panel-title" style="color:cornflowerblue">
                                <a role="button" data-toggle="collapse" data-parent="#accordion" href="#collapseOne" aria-expanded="false" aria-controls="collapseOne">
                                    <strong> <i class="fa fa-newspaper-o"></i> Significado de los colores <span class="glyphicon glyphicon-menu-down" aria-hidden="true" style="float: right;"></span></strong>
                                </a>
                            </h4>
                        </div>
                        <div id="collapseOne" class="panel-collapse collapse in" role="tabpanel" aria-labelledby="headingOne">
                            <div class="panel-body" align="left">
                                <p><strong>Iconos Color Rojo:</strong> Indican reportes que no han sido resueltos</p>\
                                <p><strong>Iconos Color Verde:</strong> Indican reportes que ya han sido resueltos</p>\
                            </div>
                        </div>
                    </div>
                </div>
            </html>
                """,
            script=True,
        )
        iframe1 = branca.element.IFrame(html=html, width=280, height=200)
        folium.Marker(
            location=ENES_Computo,
            popup=folium.Popup(iframe1, max_width=400),
            icon=folium.Icon(
                color="white", icon_color="#0055A4", icon="fa-info", prefix="fa"
            ),
            opacity=0.85,
            tooltip="Presiona para ver la información de los colores",
        ).add_to(maping)

        folium.TileLayer("cartodbpositron").add_to(maping)

        group_report = folium.FeatureGroup(name="Reportes")
        logger.info(f"BL > MapServices.build_map() - Rendering {len(docs)} valid reports")
        if len(docs) >= 1:
            for doc in docs:
                element = doc
                html = cls.create_html_element(element)
                iframe1 = branca.element.IFrame(html=html, width=280, height=200)
                if element.get("isSolved", None) is False:
                    folium.Circle(
                        [element.get("latitude"), element.get("longitude")],
                        radius=15,
                        color="red",
                        fill_color="red",
                    ).add_to(maping)

                    the_element = folium.Marker(
                        location=(element.get("latitude"), element.get("longitude")),
                        popup=folium.Popup(iframe1, max_width=400),
                        icon=folium.Icon(
                            color="red", icon_color="#000", icon="fa-trash", prefix="fa"
                        ),
                        tooltip="Presiona para ver la información",
                    )
                else:
                    folium.Circle(
                        [element.get("latitude"), element.get("longitude")],
                        radius=15,
                        color="green",
                        fill_color="green",
                    ).add_to(maping)

                    the_element = folium.Marker(
                        location=(element.get("latitude"), element.get("longitude")),
                        popup=folium.Popup(iframe1, max_width=400),
                        icon=folium.Icon(
                            color="green",
                            icon_color="#000",
                            icon="fa-trash",
                            prefix="fa",
                        ),
                        tooltip="Presiona para ver la información",
                    )

                the_element.add_to(group_report)

        group_report.add_to(maping)
        folium.LayerControl().add_to(maping)

        m = maping._repr_html_()  # strip folium's outer wrapper before embedding
        m = m[:95] + m[180:]
        m = m[:37] + m[55:]
        return m

    @classmethod
    def create_html_element(cls, element: dict) -> folium.Html:
        """Build the folium HTML popup for a single report marker.

        Args:
            element: Report dict from the API containing location and metadata.

        Returns:
            A folium.Html object to use as a marker popup.
        """
        e = html_escape_lib.escape  # alias for brevity
        importance_level = e(str(element.get("importanceReport", "")))
        labels = e(str(element.get("labels", "")))
        register_date = e(str(element.get("created", "")))
        comment = e(str(element.get("comments", "")))
        url_image = e(str(element.get("uriImage", "")))

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
                    <img src="{url_image}" style="width:270px;height:180px;"/>
                </center>
            </html>
                """,
            script=False,
        )


map_services = MapServices()
