from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, linregress, spearmanr

SEGMENT_BASE = "unit_price"  # "unit_price" or "log_unit_price"
PRICE_BAND_QUANTILES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
PRICE_BAND_LABELS = ["P0-20", "P20-40", "P40-60", "P60-80", "P80-100"]

STOPWORDS = {
    "패드",
    "대용량",
    "기획",
    "세트",
    "증정",
    "본품",
    "리필",
    "한정",
    "특가",
    "정품",
    "미니",
    "휴대용",
    "증정품",
    "기획전",
    "단독",
    "구성",
}


def load_inputs() -> pd.DataFrame:
    input_dir = Path("input")
    files = sorted(input_dir.glob("*.csv")) if input_dir.exists() else []
    if not files:
        files = sorted(Path(".").glob("*.csv"))
    if not files:
        raise FileNotFoundError("No input CSV files found in ./input or current directory.")
    frames = []
    for csv_path in files:
        frame = pd.read_csv(csv_path)
        frame["source_file"] = csv_path.name
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def extract_sheets_per_unit(name: str) -> float:
    if pd.isna(name):
        return np.nan
    match = re.search(r"(\d+)\s*매", str(name))
    return float(match.group(1)) if match else np.nan


def extract_units(name: str) -> int:
    if pd.isna(name):
        return 1
    text = str(name)
    for pattern in (r"(\d+)\s*개", r"(\d+)\s*팩", r"[xX]\s*(\d+)"):
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return 1


def normalize_category(df: pd.DataFrame) -> pd.Series:
    category2 = df.get("category2", pd.Series("", index=df.index)).fillna("").astype(str).str.strip()
    category1 = df.get("category1", pd.Series("", index=df.index)).fillna("").astype(str).str.strip()
    group = category2.copy()
    group[group == ""] = category1[group == ""]
    group = group.replace("", np.nan)
    return group


def compute_price_band(df: pd.DataFrame, group_cols: list[str], value_col: str) -> pd.Series:
    output = pd.Series(index=df.index, dtype="object")
    for _, idx in df.groupby(group_cols).groups.items():
        values = df.loc[idx, value_col]
        valid = values.dropna()
        if valid.size < 2:
            continue
        quantiles = valid.quantile(PRICE_BAND_QUANTILES).to_numpy()
        quantiles = np.maximum.accumulate(quantiles)
        array = values.to_numpy()
        mask = ~pd.isna(array)
        band_idx = np.searchsorted(quantiles, array[mask], side="right") - 1
        band_idx = np.clip(band_idx, 0, len(PRICE_BAND_LABELS) - 1)
        output.loc[np.asarray(idx)[mask]] = [PRICE_BAND_LABELS[i] for i in band_idx]
    return output


def tokenize(text: str) -> list[str]:
    if pd.isna(text):
        return []
    cleaned = re.sub(r"[^0-9a-zA-Z가-힣]+", " ", str(text).lower())
    tokens = []
    for token in cleaned.split():
        if token in STOPWORDS:
            continue
        if len(token) < 2:
            continue
        tokens.append(token)
    return tokens


def main() -> None:
    df = load_inputs()

    df["price"] = pd.to_numeric(df["price"].astype(str).str.replace(",", ""), errors="coerce")
    df["page_rank"] = pd.to_numeric(df["page_rank"], errors="coerce")
    df["week_start_date"] = df["week_start_date"].astype(str)
    df["brand"] = df["brand"].fillna("Unknown").astype(str)

    df["category_group"] = normalize_category(df)

    df["sheets_per_unit"] = df["product_name"].apply(extract_sheets_per_unit)
    df["units"] = df["product_name"].apply(extract_units)
    df["total_sheets"] = df["sheets_per_unit"] * df["units"]
    df["has_sheets"] = df["sheets_per_unit"].notna()
    df["is_unrealistic_sheets"] = df["total_sheets"].notna() & (
        (df["total_sheets"] < 10) | (df["total_sheets"] > 1000)
    )
    df["is_valid_sheets"] = df["total_sheets"].notna() & (~df["is_unrealistic_sheets"]) & (
        df["total_sheets"] > 0
    )

    df["unit_price"] = np.where(df["total_sheets"] > 0, df["price"] / df["total_sheets"], np.nan)
    df["log_unit_price"] = np.where(
        (df["unit_price"] > 0) & (df["is_valid_sheets"]),
        np.log(df["unit_price"]),
        np.nan,
    )

    group_cols = ["week_start_date", "category_group"]

    mean_log = df.groupby(group_cols)["log_unit_price"].transform("mean")
    std_log = df.groupby(group_cols)["log_unit_price"].transform(lambda x: x.std(ddof=0))
    std_log = std_log.where(std_log > 0)
    df["z_log"] = (df["log_unit_price"] - mean_log) / std_log

    median_log = df.groupby(group_cols)["log_unit_price"].transform("median")
    mad_log = df.groupby(group_cols)["log_unit_price"].transform(
        lambda x: np.median(np.abs(x.dropna() - np.median(x.dropna())))
        if x.dropna().size > 0
        else np.nan
    )
    mad_log = mad_log.where(mad_log > 0)
    df["robust_z"] = (df["log_unit_price"] - median_log) / (1.4826 * mad_log)

    if SEGMENT_BASE not in {"unit_price", "log_unit_price"}:
        raise ValueError("SEGMENT_BASE must be 'unit_price' or 'log_unit_price'.")
    segment_col = SEGMENT_BASE
    df["_segment_value"] = df[segment_col].where(df["is_valid_sheets"])
    quantiles = (
        df["_segment_value"]
        .groupby([df[col] for col in group_cols])
        .quantile([0.5, 0.85])
        .unstack()
        .rename(columns={0.5: "p50", 0.85: "p85"})
    )
    df = df.join(quantiles, on=group_cols)
    df["segment"] = np.select(
        [
            df["_segment_value"].notna() & df["p50"].notna() & (df["_segment_value"] <= df["p50"]),
            df["_segment_value"].notna()
            & df["p50"].notna()
            & df["p85"].notna()
            & (df["_segment_value"] > df["p50"])
            & (df["_segment_value"] <= df["p85"]),
            df["_segment_value"].notna() & df["p85"].notna() & (df["_segment_value"] > df["p85"]),
        ],
        ["Mass", "Premium", "Luxury"],
        default=pd.NA,
    )

    df["price_band"] = compute_price_band(df, group_cols, "_segment_value")

    rank_bucket_4 = []
    for rank in df["page_rank"].fillna(-1):
        if 1 <= rank <= 10:
            rank_bucket_4.append("1-10")
        elif 11 <= rank <= 20:
            rank_bucket_4.append("11-20")
        elif 21 <= rank <= 50:
            rank_bucket_4.append("21-50")
        elif 51 <= rank <= 100:
            rank_bucket_4.append("51-100")
        else:
            rank_bucket_4.append("101+")
    df["rank_bucket_4"] = rank_bucket_4

    quantiles_iqr = df.groupby(group_cols)["log_unit_price"].quantile([0.25, 0.75]).unstack()
    quantiles_iqr = quantiles_iqr.rename(columns={0.25: "q1", 0.75: "q3"})
    df = df.join(quantiles_iqr, on=group_cols)
    df["iqr"] = df["q3"] - df["q1"]
    df["lower_bound"] = df["q1"] - 1.5 * df["iqr"]
    df["upper_bound"] = df["q3"] + 1.5 * df["iqr"]
    df["is_outlier_iqr"] = (
        df["log_unit_price"].notna()
        & df["lower_bound"].notna()
        & df["upper_bound"].notna()
        & ((df["log_unit_price"] < df["lower_bound"]) | (df["log_unit_price"] > df["upper_bound"]))
    )

    df = df.drop(columns=["_segment_value"])

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    clean_long_path = output_dir / "clean_long.csv"
    df.to_csv(clean_long_path, index=False)

    scatter_cols = [
        "week_start_date",
        "category1",
        "category2",
        "category3",
        "category_group",
        "brand",
        "product_name",
        "page_rank",
        "unit_price",
        "log_unit_price",
        "segment",
        "is_valid_sheets",
    ]
    positioning_scatter = df[scatter_cols].copy()
    positioning_scatter.to_csv(output_dir / "positioning_scatter.csv", index=False)

    positioning_summary = (
        df[df["is_valid_sheets"]]
        .groupby(group_cols + ["rank_bucket_4"])["unit_price"]
        .agg(
            item_count="count",
            median="median",
            q1=lambda x: x.quantile(0.25),
            q3=lambda x: x.quantile(0.75),
        )
        .reset_index()
    )
    positioning_summary["iqr"] = positioning_summary["q3"] - positioning_summary["q1"]
    positioning_summary.to_csv(output_dir / "positioning_summary.csv", index=False)

    corr_rows = []
    for (week, category), group in df.groupby(group_cols):
        subset = group[["page_rank", "log_unit_price"]].dropna()
        n = len(subset)
        if n < 2:
            corr_rows.append(
                {
                    "week_start_date": week,
                    "category_group": category,
                    "n": n,
                    "spearman_corr": np.nan,
                    "spearman_p": np.nan,
                    "kendall_corr": np.nan,
                    "kendall_p": np.nan,
                    "slope": np.nan,
                    "r2": np.nan,
                }
            )
            continue
        spear = spearmanr(subset["page_rank"], subset["log_unit_price"], nan_policy="omit")
        kend = kendalltau(subset["page_rank"], subset["log_unit_price"], nan_policy="omit")
        lin = linregress(subset["log_unit_price"], subset["page_rank"])
        corr_rows.append(
            {
                "week_start_date": week,
                "category_group": category,
                "n": n,
                "spearman_corr": spear.correlation,
                "spearman_p": spear.pvalue,
                "kendall_corr": kend.correlation,
                "kendall_p": kend.pvalue,
                "slope": lin.slope,
                "r2": lin.rvalue ** 2 if not math.isnan(lin.rvalue) else np.nan,
            }
        )
    corr_rank_price = pd.DataFrame(corr_rows)
    corr_rank_price.to_csv(output_dir / "corr_rank_price.csv", index=False)

    df["rank_weight_inv"] = np.where(df["page_rank"] > 0, 1.0 / df["page_rank"], np.nan)
    df["rank_weight_inv_sqrt"] = np.where(
        df["page_rank"] > 0, 1.0 / np.sqrt(df["page_rank"]), np.nan
    )

    category_totals = (
        df.groupby(group_cols)
        .agg(
            total_count=("product_name", "count"),
            total_weight_inv=("rank_weight_inv", "sum"),
            total_weight_inv_sqrt=("rank_weight_inv_sqrt", "sum"),
        )
        .reset_index()
    )

    category_sov = (
        df.groupby(group_cols + ["brand"])
        .agg(
            item_count=("product_name", "count"),
            weight_inv=("rank_weight_inv", "sum"),
            weight_inv_sqrt=("rank_weight_inv_sqrt", "sum"),
        )
        .reset_index()
        .merge(category_totals, on=group_cols, how="left")
    )
    category_sov["sov"] = category_sov["item_count"] / category_sov["total_count"]
    category_sov["weighted_sov_inv_rank"] = category_sov["weight_inv"] / category_sov["total_weight_inv"]
    category_sov["weighted_sov_inv_sqrt"] = (
        category_sov["weight_inv_sqrt"] / category_sov["total_weight_inv_sqrt"]
    )
    category_sov.to_csv(output_dir / "category_sov.csv", index=False)

    market_gap = (
        df[df["price_band"].notna()]
        .groupby(group_cols + ["price_band"])
        .agg(
            item_count=("product_name", "count"),
            brand_count=("brand", "nunique"),
            weight_inv_sqrt=("rank_weight_inv_sqrt", "sum"),
        )
        .reset_index()
        .merge(category_totals[group_cols + ["total_count", "total_weight_inv_sqrt"]], on=group_cols, how="left")
    )
    market_gap["weighted_sov"] = market_gap["weight_inv_sqrt"] / market_gap["total_weight_inv_sqrt"]
    market_gap["supply_share"] = market_gap["item_count"] / market_gap["total_count"]
    market_gap["gap_score"] = market_gap["weighted_sov"] / market_gap["supply_share"]
    market_gap.to_csv(output_dir / "market_gap.csv", index=False)

    keyword_rows = []
    for (week, category), group in df.groupby(group_cols):
        counter = Counter()
        for name in group["product_name"].dropna():
            counter.update(tokenize(name))
        for rank, (token, count) in enumerate(counter.most_common(20), start=1):
            keyword_rows.append(
                {
                    "week_start_date": week,
                    "category_group": category,
                    "token": token,
                    "count": count,
                    "token_rank": rank,
                }
            )
    top_keywords = pd.DataFrame(keyword_rows)
    top_keywords.to_csv(output_dir / "top_keywords.csv", index=False)

    brand_norm = df["brand"].str.lower().str.replace(" ", "", regex=False)
    df["is_calmf"] = brand_norm.str.contains("calmf", na=False) | brand_norm.str.contains("캄프", na=False)

    calmf_products = df[df["is_calmf"]][
        [
            "week_start_date",
            "category_group",
            "brand",
            "product_name",
            "page_rank",
            "price",
            "unit_price",
            "log_unit_price",
            "segment",
            "z_log",
            "robust_z",
        ]
    ].copy()
    calmf_products.to_csv(output_dir / "calmf_products.csv", index=False)

    market_median = (
        df[df["is_valid_sheets"]]
        .groupby(group_cols)["unit_price"]
        .median()
        .rename("market_median_unit_price")
        .reset_index()
    )
    calmf_median = (
        df[df["is_calmf"] & df["is_valid_sheets"]]
        .groupby(group_cols)["unit_price"]
        .median()
        .rename("calmf_median_unit_price")
        .reset_index()
    )
    calmf_count = (
        df[df["is_calmf"]]
        .groupby(group_cols)["product_name"]
        .count()
        .rename("calmf_item_count")
        .reset_index()
    )
    calmf_vs_market = (
        market_median.merge(calmf_median, on=group_cols, how="left")
        .merge(calmf_count, on=group_cols, how="left")
    )
    calmf_vs_market["premium_index"] = (
        calmf_vs_market["calmf_median_unit_price"] / calmf_vs_market["market_median_unit_price"]
    )
    calmf_vs_market.to_csv(output_dir / "calmf_vs_market.csv", index=False)

    outliers = df[df["is_outlier_iqr"]][
        [
            "week_start_date",
            "category_group",
            "brand",
            "product_name",
            "page_rank",
            "price",
            "unit_price",
            "log_unit_price",
            "lower_bound",
            "upper_bound",
        ]
    ].copy()
    outliers.to_csv(output_dir / "outliers.csv", index=False)

    data_quality = (
        df.groupby(group_cols)
        .agg(
            total_count=("product_name", "count"),
            has_sheets_rate=("has_sheets", "mean"),
            invalid_sheets_rate=("is_unrealistic_sheets", "mean"),
            outlier_rate=("is_outlier_iqr", "mean"),
        )
        .reset_index()
    )
    data_quality["missing_sheets_rate"] = 1 - data_quality["has_sheets_rate"]
    data_quality.to_csv(output_dir / "data_quality.csv", index=False)


if __name__ == "__main__":
    main()
