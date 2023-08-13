import json

import requests

from config.settings import settings


class AmixtliManager:
    def __init__(self):
        self.url = settings.AMIXTLI_API_REPORTS

    def get_reports(self, is_valid: bool = None):
        """Function to get all reports from API

        Returns:
            list: list of all reports
        """
        if is_valid is not None:
            params = {"is_valid": is_valid}
            response = requests.get(self.url, params=params)
        else:
            response = requests.get(self.url)

        if response.status_code in [200, 201]:
            response = json.loads(response.text)
            reports = response.get("results", [])
        else:
            reports = []
        return reports

    def update_report(self, id_report: str, value_to_update: dict, token: str):
        """Function to update a report in firebase through method API

        Args:
            id_report (str): id of the report
            value_to_update (dict): {name of the field to update: new value}
            token (str): To be able to use the endpoint
        """

        new_value = value_to_update
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.patch(
            f"{self.url}/{id_report}", json=new_value, headers=headers
        )
        return response


amixtli_manager = AmixtliManager()
