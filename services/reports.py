from loguru import logger

from managers.amixtli_manager import amixtli_manager


class ReportsServices:
    @classmethod
    def get_reports_to_validate(cls) -> list[tuple]:
        """Fetch and structure unvalidated reports for the moderation page.

        Returns:
            List of tuples: (url_image, labels, comments, city, state, id).
            Capped at 5 items.
        """
        logger.info("BL > ReportsServices.get_reports_to_validate() - Fetching reports to validate")
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

        logger.info(f"BL > ReportsServices.get_reports_to_validate() - Returning {len(imagenes)} reports")
        return imagenes

    def update_report(self, id_report: str, new_value: dict, token: str) -> object:
        """Update a report's validation status via the API.

        Args:
            id_report: ID of the report to update.
            new_value: Dict with the field(s) and new value(s) to set.
            token: Bearer token for authorization.

        Returns:
            The HTTP response from the API.
        """
        logger.info(f"BL > ReportsServices.update_report() - Updating report id={id_report}")
        response = amixtli_manager.update_report(
            id_report=id_report, value_to_update=new_value, token=token
        )
        return response


reports_services = ReportsServices()
