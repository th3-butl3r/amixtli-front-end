from typing import Optional

from loguru import logger

from config.supabase_client import supabase

_TABLE = "reports"
_STATUS_APROBADO = "aprobado"

# Columns fetched on map load — includes state for client-side filtering
_MAP_FIELDS = "id, latitude, longitude, importance_report, state"

# Columns fetched on marker click — full detail only when the user requests it
_DETAIL_FIELDS = "id, image_path, street, city, comment, waste_type, environment_type, importance_report"

# Columns for the top-N ranking panel
_TOP_FIELDS = "id, latitude, longitude, state, city, importance_report"


class SupabaseManager:
    """Manager for Supabase operations on the reports table.

    Uses a two-phase fetch strategy:
    - get_map_reports()    → lightweight, called once on map load.
    - get_report_detail()  → full data, called only when a marker is clicked.

    Both methods filter by status = 'aprobado' so unreviewed reports never appear.
    """

    def get_map_reports(self) -> list[dict]:
        """Fetch the minimal fields needed to render markers on the map.

        Selects only id, coordinates and importance score to keep the initial
        payload small regardless of the total number of reports.

        Returns:
            List of dicts with keys: id, latitude, longitude, importanceReport.
            Returns empty list on error.
        """
        logger.info("BL > SupabaseManager.get_map_reports() - Fetching map markers")
        try:
            response = (
                supabase.table(_TABLE)
                .select(_MAP_FIELDS)
                .eq("status", _STATUS_APROBADO)
                .execute()
            )
            reports: list[dict] = response.data or []
            logger.info(
                f"BL > SupabaseManager.get_map_reports() - Retrieved {len(reports)} approved reports"
            )
            return reports
        except Exception as exc:
            logger.error(f"BL > SupabaseManager.get_map_reports() - Query failed: {exc}")
            return []

    def get_reports_count(self) -> int:
        """Return the total number of reports ever submitted (all statuses).

        Uses a count-only query so no row data is transferred.

        Returns:
            Total report count, or 0 on error.
        """
        logger.info("BL > SupabaseManager.get_reports_count() - Fetching total count")
        try:
            response = supabase.rpc("count_reports").execute()
            total: int = response.data
            logger.info(
                f"BL > SupabaseManager.get_reports_count() - Total reports: {total}"
            )
            return total
        except Exception as exc:
            logger.error(
                f"BL > SupabaseManager.get_reports_count() - Query failed: {exc}"
            )
            return 0

    def get_available_states(self) -> list[str]:
        """Return sorted distinct state values that have at least one approved report.

        Used to populate the state filter select so options always match exactly
        what is stored in the database, regardless of naming conventions.

        Returns:
            Sorted list of unique state strings. Returns empty list on error.
        """
        logger.info(
            "BL > SupabaseManager.get_available_states() - Fetching distinct states"
        )
        try:
            response = (
                supabase.table(_TABLE)
                .select("state")
                .eq("status", _STATUS_APROBADO)
                .execute()
            )
            states: list[str] = sorted(
                {row["state"] for row in (response.data or []) if row.get("state")}
            )
            logger.info(
                f"BL > SupabaseManager.get_available_states() - Found {len(states)} distinct states"
            )
            return states
        except Exception as exc:
            logger.error(
                f"BL > SupabaseManager.get_available_states() - Query failed: {exc}"
            )
            return []

    def get_top_reports(self, limit: int = 10, state: Optional[str] = None) -> list[dict]:
        """Fetch the top N approved reports ordered by importance score.

        Used to populate the ranking panel on the map. When a state is provided
        the results are scoped to that state only, enabling the panel to update
        in sync with the state filter.

        Args:
            limit: Maximum number of results to return (default 10).
            state: Optional Mexican state name to filter by.

        Returns:
            List of dicts ordered by importance_report descending.
            Returns empty list on error.
        """
        logger.info(
            f"BL > SupabaseManager.get_top_reports() - limit={limit}, state={state}"
        )
        try:
            query = (
                supabase.table(_TABLE)
                .select(_TOP_FIELDS)
                .eq("status", _STATUS_APROBADO)
                .order("importance_report", desc=True)
                .limit(limit)
            )
            if state:
                query = query.eq("state", state)
            response = query.execute()
            reports: list[dict] = response.data or []
            logger.info(
                f"BL > SupabaseManager.get_top_reports() - Retrieved {len(reports)} reports"
            )
            return reports
        except Exception as exc:
            logger.error(f"BL > SupabaseManager.get_top_reports() - Query failed: {exc}")
            return []

    def get_report_detail(self, report_id: str) -> Optional[dict]:
        """Fetch the full detail of a single approved report.

        Called only when the user clicks a marker on the map, so the heavier
        payload (image URL, address, comments, etc.) is loaded on demand.

        Args:
            report_id: UUID of the report to fetch.

        Returns:
            Dict with full report fields, or None if not found or on error.
        """
        logger.info(
            f"BL > SupabaseManager.get_report_detail() - Fetching detail for id={report_id}"
        )
        try:
            response = (
                supabase.table(_TABLE)
                .select(_DETAIL_FIELDS)
                .eq("id", report_id)
                .eq("status", _STATUS_APROBADO)
                .single()
                .execute()
            )
            detail: Optional[dict] = response.data
            if detail:
                logger.info(
                    f"BL > SupabaseManager.get_report_detail() - Found report id={report_id}"
                )
            else:
                logger.warning(
                    f"BL > SupabaseManager.get_report_detail() - No approved report found for id={report_id}"
                )
            return detail
        except Exception as exc:
            logger.error(
                f"BL > SupabaseManager.get_report_detail() - Query failed for id={report_id}: {exc}"
            )
            return None


supabase_manager = SupabaseManager()
