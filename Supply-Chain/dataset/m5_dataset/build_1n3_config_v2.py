import json
import math
from pathlib import Path
from typing import Tuple, Optional, List

import pandas as pd


# -------- column autodetect --------
DATE_CANDIDATES = ["date", "Date", "ds", "d", "timestamp", "time"]
QTY_CANDIDATES  = ["quantity", "qty", "demand", "sales", "value", "y", "units", "qty_sold"]


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur] + list(cur.parents):
        if (p / "engine").exists() and ((p / "config").exists() or (p / "dataset").exists()):
            return p
    return cur


def detect_cols(df: pd.DataFrame) -> Tuple[str, str]:
    # date
    date_col = None
    for c in DATE_CANDIDATES:
        if c in df.columns:
            date_col = c
            break
    if date_col is None:
        # try infer: first datetime-like column
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                date_col = c
                break
    if date_col is None:
        # fallback: create synthetic date index
        date_col = "date"
        df[date_col] = pd.RangeIndex(len(df))

    # qty
    qty_col = None
    for c in QTY_CANDIDATES:
        if c in df.columns:
            qty_col = c
            break
    if qty_col is None:
        # pick first numeric column that isn't the date column
        num_cols = [c for c in df.columns if c != date_col and pd.api.types.is_numeric_dtype(df[c])]
        if not num_cols:
            raise ValueError(f"Could not detect quantity column in columns={list(df.columns)}")
        qty_col = num_cols[0]

    return date_col, qty_col


def read_series(path: Path, date_hint: Optional[str] = None, qty_hint: Optional[str] = None) -> pd.DataFrame:
    df = pd.read_csv(path)
    # detect columns
    dcol, qcol = detect_cols(df) if (date_hint is None or qty_hint is None) else (date_hint, qty_hint)

    # normalize date column
    if dcol in df.columns:
        try:
            df[dcol] = pd.to_datetime(df[dcol])
            df = df.sort_values(dcol)
        except Exception:
            # leave as-is if not parseable
            pass
    else:
        df[dcol] = pd.RangeIndex(len(df))

    out = pd.DataFrame({
        dcol: df[dcol],
        "quantity": df[qcol].fillna(0).clip(lower=0).round().astype(int)
    })
    out = out.rename(columns={dcol: "date"})  # standardize to 'date'
    return out[["date", "quantity"]]


def aggregate_from_manifest(manifest_path: Path, store_ids: List[str]) -> pd.DataFrame:
    man = json.loads(manifest_path.read_text())
    files = man["files"]  # { "CA_1": "processed/CA_1.csv", ... }
    series_list = []
    for sid in store_ids:
        rel = files[str(sid)]
        p = (manifest_path.parent / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
        s = read_series(p).set_index("date")
        series_list.append(s.rename(columns={"quantity": f"{sid}"}))
    if not series_list:
        raise ValueError("No series to aggregate.")
    joined = pd.concat(series_list, axis=1, join="outer").fillna(0)
    agg = joined.sum(axis=1).astype(int).reset_index()
    agg.columns = ["date", "quantity"]
    return agg


def base_stock_S(series: pd.Series, L: int, z: float = 1.64, review: int = 1) -> int:
    mu = float(series.mean())
    sd = float(series.std(ddof=1))
    PT = L + review
    S = mu * PT + z * sd * (PT ** 0.5)
    return int(math.ceil(S)), mu, sd


def write_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def main(
    m5_config_path: str = "config/m5_csv_10stores.json",
    out_config_path: str = "config/1n3_from_m5.json",
    out_csv_dir: str = "dataset/m5_dataset/processed/retailers",
):
    here = Path(__file__).resolve()
    root = find_repo_root(here.parent)
    print(f"[info] repo root: {root}")

    # Load existing 10-store config; get manifest if present (else fallback to standard path)
    cfg_path = (root / m5_config_path) if not Path(m5_config_path).is_absolute() else Path(m5_config_path)
    m5_cfg = json.loads(cfg_path.read_text())
    manifest_rel = None
    for d in m5_cfg.get("demand", []):
        g = d["generator"]
        if g.get("type") == "csv" and "manifest" in g:
            manifest_rel = g["manifest"]
            break
    if manifest_rel is None:
        manifest_rel = "dataset/m5_dataset/processed/manifest.json"

    manifest_path = (root / manifest_rel).resolve() if not Path(manifest_rel).is_absolute() else Path(manifest_rel)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")

    # Unequal 4–3–3 split across 3 retailers
    groups = {
        "R1": ["CA_1", "CA_2", "WI_1", "TX_1"],
        "R2": ["CA_3", "CA_4", "WI_2"],
        "R3": ["WI_3", "TX_2", "TX_3"],
    }

    # Lead times (1–2–3 topology: Supplier -> {W1,W2} -> {R1,R2,R3})
    L_sup_W1 = 5
    L_sup_W2 = 6
    L_W1_R1  = 2
    L_W1_R2  = 3
    L_W2_R3  = 4

    out_dir = (root / out_csv_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Aggregate and write retailer CSVs
    agg_csv_paths = {}
    for r_id, stores in groups.items():
        df = aggregate_from_manifest(manifest_path, stores)
        out_csv = out_dir / f"{r_id}.csv"
        write_csv(df, out_csv)
        agg_csv_paths[r_id] = str(out_csv.relative_to(root))  # store relative path in config

    # Compute S for retailers
    R_info = {}
    for r_id, rel_csv in agg_csv_paths.items():
        df = read_series(root / rel_csv)  # returns standardized 'date','quantity'
        series = df["quantity"]
        L = {"R1": L_W1_R1, "R2": L_W1_R2, "R3": L_W2_R3}[r_id]
        S, mu, sd = base_stock_S(series, L=L, z=1.64, review=1)
        R_info[r_id] = {"S": S, "mu": mu, "sd": sd, "T": len(series)}

    T = int(min(v["T"] for v in R_info.values()))

    # Warehouse S levels (normal approx)
    mu_W1 = R_info["R1"]["mu"] + R_info["R2"]["mu"]
    sd_W1 = (R_info["R1"]["sd"] ** 2 + R_info["R2"]["sd"] ** 2) ** 0.5
    S_W1  = int(math.ceil(mu_W1 * (L_sup_W1 + 1) + 1.64 * sd_W1 * ((L_sup_W1 + 1) ** 0.5)))

    mu_W2 = R_info["R3"]["mu"]
    sd_W2 = R_info["R3"]["sd"]
    S_W2  = int(math.ceil(mu_W2 * (L_sup_W2 + 1) + 1.64 * sd_W2 * ((L_sup_W2 + 1) ** 0.5)))

    # Final config
    cfg = {
        "seed": 42,
        "time_horizon": T,
        "nodes": [
            {"id": "Supplier", "type": "supplier", "infinite_supply": True,
             "policy": {"type": "base_stock", "base_stock_level": 0}},

            {"id": "W1", "type": "warehouse", "initial_inventory": S_W1,
             "policy": {"type": "base_stock", "base_stock_level": S_W1}},
            {"id": "W2", "type": "warehouse", "initial_inventory": S_W2,
             "policy": {"type": "base_stock", "base_stock_level": S_W2}},

            {"id": "R1", "type": "retailer", "initial_inventory": R_info["R1"]["S"],
             "policy": {"type": "base_stock", "base_stock_level": R_info["R1"]["S"]}},
            {"id": "R2", "type": "retailer", "initial_inventory": R_info["R2"]["S"],
             "policy": {"type": "base_stock", "base_stock_level": R_info["R2"]["S"]}},
            {"id": "R3", "type": "retailer", "initial_inventory": R_info["R3"]["S"],
             "policy": {"type": "base_stock", "base_stock_level": R_info["R3"]["S"]}},
        ],
        "edges": [
            {"from": "Supplier", "to": "W1", "lead_time": {"type": "deterministic", "value": L_sup_W1}},
            {"from": "Supplier", "to": "W2", "lead_time": {"type": "deterministic", "value": L_sup_W2}},
            {"from": "W1", "to": "R1", "lead_time": {"type": "deterministic", "value": L_W1_R1}},
            {"from": "W1", "to": "R2", "lead_time": {"type": "deterministic", "value": L_W1_R2}},
            {"from": "W2", "to": "R3", "lead_time": {"type": "deterministic", "value": L_W2_R3}},
        ],
        "demand": [
            {"node": "R1", "generator": {"type": "csv", "path": agg_csv_paths["R1"], "date_col": "date", "qty_col": "quantity", "strategy": "wrap"}},
            {"node": "R2", "generator": {"type": "csv", "path": agg_csv_paths["R2"], "date_col": "date", "qty_col": "quantity", "strategy": "wrap"}},
            {"node": "R3", "generator": {"type": "csv", "path": agg_csv_paths["R3"], "date_col": "date", "qty_col": "quantity", "strategy": "wrap"}},
        ]
    }

    out_cfg = (root / out_config_path).resolve() if not Path(out_config_path).is_absolute() else Path(out_config_path)
    out_cfg.parent.mkdir(parents=True, exist_ok=True)
    out_cfg.write_text(json.dumps(cfg, indent=2))
    print(f"[ok] wrote config: {out_cfg}")
    for r_id, rel in agg_csv_paths.items():
        print(f"[ok] wrote CSV for {r_id}: {root/rel}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--m5_config", default="config/m5_csv_10stores.json")
    ap.add_argument("--out_config", default="config/1n3_from_m5.json")
    ap.add_argument("--out_csv_dir", default="dataset/m5_dataset/processed/retailers")
    args = ap.parse_args()
    main(args.m5_config, args.out_config, args.out_csv_dir)
