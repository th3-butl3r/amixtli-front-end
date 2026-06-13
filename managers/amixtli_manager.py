import json
from typing import Optional

import requests
from loguru import logger

from config.settings import settings


class AmixtliManager:
    def __init__(self) -> None:
        self.url = settings.AMIXTLI_API_REPORTS

    def get_reports(self, is_valid: Optional[bool] = None) -> list:
        """Get all reports from the API.

        Args:
            is_valid: Filter reports by validation status. If None, returns all.

        Returns:
            List of report dicts, or empty list on failure.
        """
        logger.info(
            f"BL > AmixtliManager.get_reports() - Fetching reports with is_valid={is_valid}"
        )
        if is_valid is not None:
            params = {"is_valid": is_valid}
            response = requests.get(self.url, params=params)
        else:
            response = requests.get(self.url)

        if response.status_code in [200, 201]:
            response = json.loads(response.text)
            reports = response.get("results", [])
        else:
            logger.warning(
                f"BL > AmixtliManager.get_reports() - API returned status {response.status_code}"
            )
            reports = []
        return reports

    def update_report(
        self, id_report: str, value_to_update: dict, token: str
    ) -> requests.Response:
        """Update a report field via the API.

        Args:
            id_report: ID of the report to update.
            value_to_update: Dict with the field(s) and new value(s) to set.
            token: Bearer token for authorization.

        Returns:
            The HTTP response from the API.
        """
        logger.info(
            f"BL > AmixtliManager.update_report() - Updating report id={id_report}"
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.patch(
            f"{self.url}/{id_report}", json=value_to_update, headers=headers
        )
        return response


amixtli_manager = AmixtliManager()
