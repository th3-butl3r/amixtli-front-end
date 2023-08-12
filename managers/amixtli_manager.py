import json

import requests

from config.settings import settings

pass


class AmixtliManager:
    @classmethod
    def get_reports(self, is_valid: bool = None):
        """Function to get all reports from API

        Returns:
            list: list of all reports
        """
        url = settings.AMIXTLI_API_REPORTS
        if is_valid is not None:
            params = {"is_valid": is_valid}
            response = requests.get(url, params=params)
        else:
            response = requests.get(url)

        if response.status_code in [200, 201]:
            # TODO: AÑADIR LOGS
            response = json.loads(response.text)
            reports = response.get("results", [])
        else:
            reports = []
        return reports


amixtli_manager = AmixtliManager()
