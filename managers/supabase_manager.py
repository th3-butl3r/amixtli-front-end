import time
from typing import Any, Optional

from loguru import logger

from config.supabase_client import supabase

_TABLE = "reports"
_STATUS_APROBADO = "aprobado"
_STATUS_PENDIENTE = "pendiente"

# ── Simple TTL cache ───────────────────────────────────────────────────────────
# Avoids repeated round-trips to Supabase for data that changes infrequently.
# Write operations (approve/delete) must call _invalidate() for affected keys.
_cache: dict[str, tuple[Any, float]] = {}
_TTL: dict[str, int] = {
    "map_reports": 120,  # 2 min — new approved reports appear with slight delay
    "states": 300,  # 5 min — state list rarely changes
    "top_reports": 120,  # 2 min — ranking shifts slowly
    "count": 600,  # 10 min — home page counter, precision not critical
    "detail": 300,  # 5 min — approved report fields rarely change
}


def _cache_get(key: str) -> tuple[bool, Any]:
    """Return (hit, value) from cache if the entry exists and is still fresh."""
    if key in _cache:
        value, ts = _cache[key]
        if time.time() - ts < _TTL.get(key.split(":")[0], 120):
            return True, value
    return False, None


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (value, time.time())


def _invalidate(*keys: str) -> None:
    """Remove one or more keys from the cache (call after writes)."""
    for k in keys:
        _cache.pop(k, None)


# Columns fetched on map load — includes state for client-side filtering
_MAP_FIELDS = "id, latitude, longitude, importance_report, state, is_solved"

# Columns fetched on marker click — full detail only when the user requests it
_DETAIL_FIELDS = "id, image_path, street, city, comment, waste_type, environment_type, importance_report"

# Columns for the top-N ranking panel
_TOP_FIELDS = "id, latitude, longitude, state, city, importance_report"

# Columns for the moderation queue — includes coordinates for the inline mini-map
_PENDING_FIELDS = (
    "id, image_path, street, city, state, comment, waste_type, environment_type,"
    " importance_report, latitude, longitude"
)

_RETRY_ERRORS = ("server disconnected", "connection", "timeout", "eof")
_RETRY_WAIT = 1.5  # seconds between attempts


def _with_retry(fn, retries: int = 2):
    """Execute fn(), retrying on transient network errors.

    Args:
        fn: Zero-argument callable wrapping a supabase query.
        retries: Number of additional attempts after the first failure.

    Returns:
        Result of fn() on success.

    Raises:
        Exception: Re-raises the last exception if all attempts fail.
    """
    last_exc: Exception = Exception("unknown")
    for attempt in range(1 + retries):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if any(k in str(exc).lower() for k in _RETRY_ERRORS) and attempt < retries:
                logger.warning(
                    f"BL > _with_retry() - Transient error on attempt {attempt + 1}, retrying: {exc}"
                )
                time.sleep(_RETRY_WAIT)
            else:
                raise
    raise last_exc


class SupabaseManager:
    """Manager for Supabase operations on the reports table.

    Uses a two-phase fetch strategy:
    - get_map_reports()    → lightweight, called once on map load.
    - get_report_detail()  → full data, called only when a marker is clicked.

    Both methods filter by status = 'aprobado' so unreviewed reports never appear.
    """

    def get_map_reports(self) -> list[dict]:
        """Fetch the minimal fields needed to render markers on the map.

        Returns:
            List of dicts with keys: id, latitude, longitude, importance_report.
            Returns empty list on error.
        """
        hit, cached = _cache_get("map_reports")
        if hit:
            logger.info(
                f"BL > SupabaseManager.get_map_reports() - Cache hit ({len(cached)} reports)"
            )
            return cached

        logger.info("BL > SupabaseManager.get_map_reports() - Fetching map markers")
        try:
            response = _with_retry(
                lambda: supabase.table(_TABLE)
                .select(_MAP_FIELDS)
                .eq("status", _STATUS_APROBADO)
                .execute()
            )
            reports: list[dict] = response.data or []
            _cache_set("map_reports", reports)
            logger.info(
                f"BL > SupabaseManager.get_map_reports() - Retrieved {len(reports)} approved reports"
            )
            return reports
        except Exception as exc:
            logger.error(f"BL > SupabaseManager.get_map_reports() - Query failed: {exc}")
            return []

    def get_reports_count(self) -> int:
        """Return the total number of reports ever submitted (all statuses).

        Returns:
            Total report count, or 0 on error.
        """
        hit, cached = _cache_get("count")
        if hit:
            logger.info(
                f"BL > SupabaseManager.get_reports_count() - Cache hit ({cached})"
            )
            return cached

        logger.info("BL > SupabaseManager.get_reports_count() - Fetching total count")
        try:
            response = _with_retry(lambda: supabase.rpc("count_reports").execute())
            total: int = response.data
            _cache_set("count", total)
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

        Returns:
            Sorted list of unique state strings. Returns empty list on error.
        """
        hit, cached = _cache_get("states")
        if hit:
            logger.info(
                f"BL > SupabaseManager.get_available_states() - Cache hit ({len(cached)} states)"
            )
            return cached

        logger.info(
            "BL > SupabaseManager.get_available_states() - Fetching distinct states"
        )
        try:
            response = _with_retry(
                lambda: supabase.table(_TABLE)
                .select("state")
                .eq("status", _STATUS_APROBADO)
                .execute()
            )
            states: list[str] = sorted(
                {row["state"] for row in (response.data or []) if row.get("state")}
            )
            _cache_set("states", states)
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

        Args:
            limit: Maximum number of results to return (default 10).
            state: Optional Mexican state name to filter by.

        Returns:
            List of dicts ordered by importance_report descending.
            Returns empty list on error.
        """
        cache_key = f"top_reports:{limit}:{state or ''}"
        hit, cached = _cache_get(cache_key)
        if hit:
            logger.info(
                f"BL > SupabaseManager.get_top_reports() - Cache hit (key={cache_key})"
            )
            return cached

        logger.info(
            f"BL > SupabaseManager.get_top_reports() - limit={limit}, state={state}"
        )
        try:

            def _query():
                q = (
                    supabase.table(_TABLE)
                    .select(_TOP_FIELDS)
                    .eq("status", _STATUS_APROBADO)
                    .order("importance_report", desc=True)
                    .limit(limit)
                )
                if state:
                    q = q.eq("state", state)
                return q.execute()

            response = _with_retry(_query)
            reports: list[dict] = response.data or []
            _cache_set(cache_key, reports)
            logger.info(
                f"BL > SupabaseManager.get_top_reports() - Retrieved {len(reports)} reports"
            )
            return reports
        except Exception as exc:
            logger.error(f"BL > SupabaseManager.get_top_reports() - Query failed: {exc}")
            return []

    def get_report_detail(self, report_id: str) -> Optional[dict]:
        """Fetch the full detail of a single approved report.

        Args:
            report_id: UUID of the report to fetch.

        Returns:
            Dict with full report fields, or None if not found or on error.
        """
        cache_key = f"detail:{report_id}"
        hit, cached = _cache_get(cache_key)
        if hit:
            logger.info(
                f"BL > SupabaseManager.get_report_detail() - Cache hit for id={report_id}"
            )
            return cached

        logger.info(
            f"BL > SupabaseManager.get_report_detail() - Fetching detail for id={report_id}"
        )
        try:
            response = _with_retry(
                lambda: supabase.table(_TABLE)
                .select(_DETAIL_FIELDS)
                .eq("id", report_id)
                .eq("status", _STATUS_APROBADO)
                .single()
                .execute()
            )
            detail: Optional[dict] = response.data
            if detail:
                _cache_set(cache_key, detail)
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

    def get_pending_reports(self, limit: int = 20) -> list[dict]:
        """Fetch reports pending moderation.

        Args:
            limit: Maximum number of results to return (default 20).

        Returns:
            List of report dicts ordered by insertion order. Empty list on error.
        """
        logger.info(
            "BL > SupabaseManager.get_pending_reports() - Fetching pending reports"
        )
        try:
            response = _with_retry(
                lambda: supabase.table(_TABLE)
                .select(_PENDING_FIELDS)
                .eq("status", _STATUS_PENDIENTE)
                .limit(limit)
                .execute()
            )
            reports: list[dict] = response.data or []
            logger.info(
                f"BL > SupabaseManager.get_pending_reports() - Found {len(reports)} pending reports"
            )
            return reports
        except Exception as exc:
            logger.error(
                f"BL > SupabaseManager.get_pending_reports() - Query failed: {exc}"
            )
            return []

    def approve_report(
        self,
        report_id: str,
        waste_type: Optional[str] = None,
        environment_type: Optional[str] = None,
    ) -> bool:
        """Set a report's status to 'aprobado', optionally updating its tags.

        Args:
            report_id: UUID of the report to approve.
            waste_type: Corrected waste type label, or None to leave unchanged.
            environment_type: Corrected environment label, or None to leave unchanged.

        Returns:
            True if at least one row was updated, False otherwise.
        """
        logger.info(f"BL > SupabaseManager.approve_report() - Approving id={report_id}")
        payload: dict = {"status": _STATUS_APROBADO}
        if waste_type:
            payload["waste_type"] = waste_type
        if environment_type:
            payload["environment_type"] = environment_type

        try:
            logger.debug(f"BL > SupabaseManager.approve_report() - payload={payload}")
            response = _with_retry(
                lambda: supabase.table(_TABLE)
                .update(payload)
                .eq("id", report_id)
                .execute()
            )
            logger.debug(
                f"BL > SupabaseManager.approve_report() - response.data={response.data}"
            )
            if not response.data:
                logger.warning(
                    f"BL > SupabaseManager.approve_report() - UPDATE returned no rows for id={report_id}"
                )
                return False
            # Flush read caches so the map and detail popup reflect the changes.
            _invalidate("map_reports", "states", "count", f"detail:{report_id}")
            logger.info(
                f"BL > SupabaseManager.approve_report() - Approved id={report_id}"
            )
            return True
        except Exception as exc:
            logger.error(
                f"BL > SupabaseManager.approve_report() - Failed for id={report_id}: {exc}"
            )
            return False

    def delete_report(self, report_id: str) -> bool:
        """Delete a report record from the database.

        Args:
            report_id: UUID of the report to delete.

        Returns:
            True on success, False otherwise.
        """
        logger.info(f"BL > SupabaseManager.delete_report() - Deleting id={report_id}")
        try:
            _with_retry(
                lambda: supabase.table(_TABLE).delete().eq("id", report_id).execute()
            )
            logger.info(f"BL > SupabaseManager.delete_report() - Deleted id={report_id}")
            return True
        except Exception as exc:
            logger.error(
                f"BL > SupabaseManager.delete_report() - Failed for id={report_id}: {exc}"
            )
            return False

    def health_db(self):
        """Check connection with database.

        Returns:
            True on success, False otherwise
        """
        logger.info("BL > SupabaseManager.health_db() - CHECK DB...")
        try:
            supabase.table(_TABLE).select("id").limit(1).execute()
            logger.info("BL > SupabaseManager.health_db() - CHECK DB OK")
            return True
        except Exception as exc:
            logger.error(f"BL > SupabaseManager.health_db() - CHECK ERROR: {exc}")
            return False


supabase_manager = SupabaseManager()
