import branca
import folium

from managers.amixtli_manager import amixtli_manager
from utils.struct_element_html import create_html_element


def build_map():
    docs = amixtli_manager.get_reports()
    # creation of map comes here + business logic
    # * where the map start: Mexico
    maping = folium.Map(
        location=(19.9998589, -100.9994856), titles="Mexico", zoom_start=7, max_zoom=19
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
                        color="green", icon_color="#000", icon="fa-trash", prefix="fa"
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
