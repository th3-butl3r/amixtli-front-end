from managers.amixtli_manager import amixtli_manager


class ReportsServices:
    @classmethod
    def get_reports_to_validate(self):
        """Function to get and struct reports for validate_reports page"""
        docs = amixtli_manager.get_reports(is_valid=False)
        imagenes = []
        for doc in docs:
            id = doc.get("id")
            if id is not None:
                url_image = doc.get("uriImage", None)
                labels = doc.get("labels", None)
                comments = doc.get("comments", None)
                city = doc.get("city", None)
                state = doc.get("state", None)
                if url_image is not None:
                    imagenes.append((url_image, labels, comments, city, state, id))
                if len(imagenes) == 5:
                    break

        return imagenes

    def get_reports(self):
        """Function to get valid reports to our users."""
        reports = amixtli_manager.get_reports(is_valid=True)
        return list(
            map(lambda x: {k: v for k, v in x.items() if k != "userOwner"}, reports)
        )

    def update_report(self, id_report: str, new_value: dict, token: str):
        """Function to update a report in firebase through method API in database

        Args:
            id_report (str): id of the report
            new_value (dict): {name of the field to update: new value}
            token (str): To be able to use the endpoint
        """

        response = amixtli_manager.update_report(
            id_report=id_report, value_to_update=new_value, token=token
        )

        return response

    def delete_report(self, id_report: str, token: str):
        """Function to delete a report in firebase through method API in database

        Args:
            id_report (str): id of the report
            token (str): To be able to use the endpoint
        """
        response = amixtli_manager.delete_report(id_report=id_report, token=token)

        return response


reports_services = ReportsServices()
