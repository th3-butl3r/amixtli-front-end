import json

import requests

from config.settings import settings

pass


class AmixtliManager:
    @classmethod
    def get_reports(self):
        """Function to get all reports from API

        Returns:
            list: list of all reports
        """
        url = settings.AMIXTLI_API_REPORTS
        response = requests.get(url)
        if response.status_code in [200, 201]:
            # TODO: AÑADIR LOGS
            response = json.loads(response.text)
            reports = response.get("results", [])
        else:
            reports = []
        return reports


amixtli_manager = AmixtliManager()
