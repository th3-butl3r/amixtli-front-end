import branca
import folium

from managers.amixtli_manager import amixtli_manager
from utils.struct_element_html import create_html_element


class MapServices:
    @classmethod
    def build_map(self):
        """Function to build the map for map page"""
        docs = amixtli_manager.get_reports()
        # creation of map comes here + business logic
        # * where the map start: Mexico
        maping = folium.Map(
            location=(19.9998589, -100.9994856),
            titles="Mexico",
            zoom_start=7,
            max_zoom=19,
        )
        folium.TileLayer("cartodbpositron").add_to(maping)

        # Create group to marks
        group_report = folium.FeatureGroup(name="Reportes")
        if len(docs) >= 1:
            for doc in docs:
                element = doc
                html = create_html_element(element)
                iframe1 = branca.element.IFrame(html=html, width=280, height=200)
                if element.get("isSolved", None) is False:
                    # Add radius for each register
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
                    # Add radius for each register
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

                # Add element to the group
                the_element.add_to(group_report)

        # NOTE: Descomentar en caso de ser necesario las delimitaciones geográficas para Mich.
        # style_function = lambda x: {  # NOQA
        #     "fillColor": ["green"],
        #     "color": "black",
        #     "weight": 0.85,
        #     "fillOpacity": 0.1,
        # }

        # # Add layer to delimit michoacan
        # map_graph = config("PATH_GEOMAP_MICH")
        # folium.GeoJson(map_graph, name="Michoacán", style_function=style_function).add_to(
        #     maping
        # )

        # add group to map
        group_report.add_to(maping)

        # # add layer control
        folium.LayerControl().add_to(maping)

        m = maping._repr_html_()  # * updated, with this I can see the map
        m = m[:95] + m[180:]
        m = m[:37] + m[55:]
        return m

    @classmethod
    def create_html_element(self, element):
        """Function to create pre-define html elements for the map"""
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


map_services = MapServices()
