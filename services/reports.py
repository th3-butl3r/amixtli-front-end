from managers.amixtli_manager import amixtli_manager


class ReportsServices:
    @classmethod
    def get_reports_to_validate(self):
        """Function to get and struct reports for validate_reports page"""
        docs = amixtli_manager.get_reports(is_valid=False)
        imagenes = []
        for doc in docs:
            # TODO: Añadir el ID del reporte a la tupla para poder hacer el update en el front
            url_image = doc.get("uriImage", None)
            labels = doc.get("labels", None)
            comments = doc.get("comments", None)
            city = doc.get("city", None)
            state = doc.get("state", None)
            if url_image is not None:
                imagenes.append((url_image, labels, comments, city, state))
            if len(imagenes) == 5:
                break

        return imagenes


reports_services = ReportsServices()
