from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Reports"])

# In-memory report storage (for demo purposes)
_report_store: dict = {}


def store_report(report_id: str, report: dict) -> None:
    """Store a report in memory."""
    _report_store[report_id] = report


def get_stored_report(report_id: str) -> dict | None:
    """Retrieve a stored report."""
    return _report_store.get(report_id)


@router.get("/reports/{report_id}", summary="Retrieve a stored report")
async def get_report(report_id: str):
    """
    Retrieve a previously generated quality report by its ID.

    Note: Reports are stored in-memory and will be lost on server restart.
    """
    report = get_stored_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")
    return report


@router.get("/reports", summary="List all stored reports")
async def list_reports():
    """List all stored report IDs."""
    return {"report_ids": list(_report_store.keys()), "count": len(_report_store)}
