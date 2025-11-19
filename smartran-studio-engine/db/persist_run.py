from datetime import datetime
from typing import List, Dict, Any

def _build_user_docs(run_id: str, ue_meas_reports: List[Dict[str, Any]]) -> list[dict]:
    batch = []
    for row in ue_meas_reports:
        user_id = row.get("user_id")
        x = float(row.get("x", 0.0))
        y = float(row.get("y", 0.0))
        readings = {k: v for k, v in row.items() if k not in ("user_id", "x", "y")}
        batch.append({
            "_key": f"{run_id}:{user_id}",
            "run_id": run_id,
            "user_id": user_id,
            "x": x,
            "y": y,
            "readings": readings,
        })
    return batch

def persist_run(
    sim_runs,                 # arango.collection handle
    sim_reports,              # arango.collection handle
    run_id: str,
    ue_meas_reports: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    threshold_dbm: float,
    label_mode: str,
) -> None:
    """Write one run header + one doc per user. Idempotent by run_id."""
    # Upsert run header
    sim_runs.insert({
        "_key": run_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "threshold_dbm": float(threshold_dbm),
        "label_mode": label_mode,
        "num_reports": len(ue_meas_reports),
        "metadata": metadata,
    }, overwrite=True)

    # Bulk insert/update per-user docs
    batch = _build_user_docs(run_id, ue_meas_reports)
    if batch:
        # on_duplicate="update" lets you safely re-run same run_id
        sim_reports.import_bulk(batch, on_duplicate="update")