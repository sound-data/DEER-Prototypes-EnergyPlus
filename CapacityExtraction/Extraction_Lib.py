import os
import re
import pandas as pd
import numpy as np
import math
from io import StringIO


# Define the dictionary for mapping abbreviations
building_type_map = {
    "Asm": "Assembly",
    "ECC": "Education - Community College",
    "EPr": "Education - Primary School",
    "ERC": "Education - Relocatable Classroom",
    "ESe": "Education - Secondary School",
    "EUn": "Education - University",
    "Fin": "Financial buildings, incl. banks",
    "Gro": "Grocery",
    "Hsp": "Health/Medical - Hospital",
    "Htl": "Lodging - Hotel",
    "Lib": "Libraries",
    "MBT": "Manufacturing Biotech",
    "MLI": "Manufacturing Light Industrial",
    "Mtl": "Lodging - Motel",
    "Nrs": "Health/Medical - Nursing Home",
    "OfL": "Office - Large",
    "OfS": "Office - Small",
    "Rel": "Religious assembly buildings",
    "RFF": "Restaurant - Fast-Food",
    "RSD": "Restaurant - Sit-Down",
    "Rt3": "Retail - Multistory Large",
    "RtL": "Retail - Single-Story Large",
    "RtS": "Retail - Small",
    "SCn": "Storage - Conditioned",
    "SUn": "Storage - Unconditioned",
    "WRf": "Warehouse - Refrigerated"
}

# Building Type
def get_building_type(filename):
    # Extract the first part of the filename (e.g., "Asm" from "Asm&0...")
    abbrev = filename.split('_')[0]
    return building_type_map.get(abbrev, "Unknown Type")

# Category
def get_building_category(filename):
    abbrev = filename.split('_')[0]
    # If the abbreviation exists in our map, it is Nonresidential
    if abbrev in building_type_map:
        return "Nonresidential"
    return "Unknown"

# Vintage
def get_vintage():
    # Hardcoded as per requirements
    return "Existing, New Construction"

def extract_fan_data(idf_path, htm_path=None):
    """
    Read Fans table from *_etc.htm (or *_etctbl.htm).

    IDF name example: ECC_0_cPVVG_Ex_etc.idf
      - HVAC name    = cPVVG
      - Vintage token = Ex -> Existing; New -> New Construction
      - HTM sibling  = ECC_0_cPVVG_Ex_etc.htm (same stem, .htm extension)

    For each fan row outputs a dict with:
      Vintage, HVAC name, System name,
      Rated Electricity Rate [W]
    """
    import re
    from pathlib import Path

    idf_path = Path(idf_path)

    # Parse Vintage + HVAC name from IDF filename
    parts = idf_path.stem.split("_")  # e.g., ECC, 0, cPVVG, Ex, etc
    hvac_name     = parts[2] if len(parts) >= 3 else "Unknown"
    vintage_token = parts[3] if len(parts) >= 4 else "Unknown"
    vintage = {"Ex": "Existing", "New": "New Construction"}.get(vintage_token, vintage_token)

    def _coerce_float(x):
        try:
            s = str(x).strip().replace("\u00A0", " ")
            s = re.sub(r"[,\s]+", "", s)
            return float(s)
        except Exception:
            return None

    def _html_unescape(s: str) -> str:
        return (s.replace("&nbsp;", " ")
                 .replace("&amp;", "&")
                 .replace("&lt;",  "<")
                 .replace("&gt;",  ">")
                 .replace("&quot;", '"')
                 .replace("&#39;", "'"))

    def _clean_cell(cell_html: str) -> str:
        cell_html = re.sub(r"(?is)<br\s*/?>", " ", cell_html)
        cell_html = re.sub(r"(?is)<.*?>",     " ", cell_html)
        cell_html = _html_unescape(cell_html)
        return re.sub(r"\s+", " ", cell_html).strip()

    def _infer_htm_path(p: Path) -> Path | None:
        if htm_path:
            hp = Path(htm_path)
            if hp.exists():
                return hp

        cand = p.with_suffix(".htm")
        if cand.exists():
            return cand

        cand = p.with_suffix(".html")
        if cand.exists():
            return cand

        if p.name.lower().endswith("_etc.idf"):
            cand = p.with_name(p.stem + "tbl.htm")
            if cand.exists():
                return cand

        prefix = "_".join(p.stem.split("_")[:4])
        cands = sorted(p.parent.glob(prefix + "*_etctbl.htm"))
        if cands:
            return cands[0]

        cands = sorted(p.parent.glob("*_etctbl.htm"))
        if cands:
            return cands[0]

        cands = sorted(p.parent.glob("*.htm")) + sorted(p.parent.glob("*.html"))
        return cands[0] if cands else None

    def _find_fans_table_html(html: str) -> str | None:
        tables = re.findall(r"(?is)<table\b.*?>.*?</table>", html)
        # Strict: prefer table with all three key columns
        for t in tables:
            tl = t.lower()
            if (("end use subcategory" in tl) or ("end-use subcategory" in tl)) and \
               "rated electricity rate" in tl and \
               "rated power per max air flow rate" in tl:
                return t
        # Fallback
        for t in tables:
            tl = t.lower()
            if (("end use subcategory" in tl) or ("end-use subcategory" in tl)) and \
               "rated power per max air flow rate" in tl:
                return t
        return None

    def _parse_html_table(table_html: str):
        trs = re.findall(r"(?is)<tr\b.*?>(.*?)</tr>", table_html)
        all_rows = []
        for tr in trs:
            cells = re.findall(r"(?is)<t[dh]\b.*?>(.*?)</t[dh]>", tr)
            cells = [_clean_cell(c) for c in cells]
            if cells and any(c != "" for c in cells):
                all_rows.append(cells)
        if not all_rows:
            return [], []

        # Find header row
        hdr_idx = 0
        for i, r in enumerate(all_rows[:30]):
            joined = " | ".join(r).lower()
            if "rated power per max air flow rate" in joined and \
               (("end use subcategory" in joined) or ("end-use subcategory" in joined)):
                hdr_idx = i
                break

        header = all_rows[hdr_idx][:]
        header[0] = "System name"
        rows = all_rows[hdr_idx + 1:]
        return header, rows

    htm_file = _infer_htm_path(idf_path)
    if not htm_file or not htm_file.exists():
        return []

    html = htm_file.read_text(encoding="utf-8", errors="ignore")
    fans_table_html = _find_fans_table_html(html)
    if not fans_table_html:
        return []

    header, rows = _parse_html_table(fans_table_html)
    if not header or not rows:
        return []

    # Find column index for Rated Electricity Rate
    idx_rated_w = None
    for i, h in enumerate(header):
        if "rated electricity rate" in str(h).lower():
            idx_rated_w = i
            break

    out = []
    for r in rows:
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))

        system_name_raw = str(r[0]).strip()
        if not system_name_raw or system_name_raw.lower() in {"nan", "type", "system name"}:
            continue

        rated_w = "N/A"
        if idx_rated_w is not None:
            v = _coerce_float(r[idx_rated_w])
            if v is not None:
                rated_w = v

        out.append({
            "Vintage":                  vintage,
            "HVAC name":                hvac_name,
            "System name":              system_name_raw,
            "Rated Electricity Rate [W]": rated_w,
        })

    return out


def extract_dx_cooling_coil_data(idf_path, htm_path=None):
    """
    Read DX Cooling Coils [SEER2] table from *_etc.htm (or *_etctbl.htm).

    IDF name example: ECC_0_cPVVG_Ex_etc.idf
      - HVAC name    = cPVVG
      - Vintage token = Ex -> Existing; New -> New Construction
      - HTM sibling  = ECC_0_cPVVG_Ex_etc.htm  (same stem, .htm extension)

    For each coil row outputs a dict with:
      Vintage, HVAC name, Coil name,
      Standard Rated Net Cooling Capacity [W]

    Table column layout (fixed by EnergyPlus):
      col 0: Coil name  (blank header in HTML)
      col 1: DX Cooling Coil Type
      col 2: Standard Rated Net Cooling Capacity [W]
    """
    import re
    from pathlib import Path

    idf_path = Path(idf_path)

    # Parse Vintage + HVAC name from IDF filename
    parts = idf_path.stem.split("_")  # e.g., ECC, 0, cPVVG, Ex, etc
    hvac_name     = parts[2] if len(parts) >= 3 else "Unknown"
    vintage_token = parts[3] if len(parts) >= 4 else "Unknown"
    vintage = {"Ex": "Existing", "New": "New Construction"}.get(vintage_token, vintage_token)

    def _coerce_float(x):
        try:
            s = str(x).strip().replace("\u00A0", " ")
            s = re.sub(r"[,\s]+", "", s)
            return float(s)
        except Exception:
            return None

    def _html_unescape(s: str) -> str:
        return (s.replace("&nbsp;", " ")
                 .replace("&amp;", "&")
                 .replace("&lt;",  "<")
                 .replace("&gt;",  ">")
                 .replace("&quot;", '"')
                 .replace("&#39;", "'"))

    def _clean_cell(cell_html: str) -> str:
        cell_html = re.sub(r"(?is)<br\s*/?>", " ", cell_html)
        cell_html = re.sub(r"(?is)<.*?>",     " ", cell_html)
        cell_html = _html_unescape(cell_html)
        return re.sub(r"\s+", " ", cell_html).strip()

    def _infer_htm_path(p: Path):
        if htm_path:
            hp = Path(htm_path)
            if hp.exists():
                return hp
            
        cand = p.with_suffix(".htm")
        if cand.exists():
            return cand

    # Requiring "seer2"
    def _find_seer2_tables(html: str):
        tables = re.findall(r"(?is)<table\b.*?>.*?</table>", html)

        # Strict: must contain "seer2", coil-type column, and capacity column
        matched = [t for t in tables
                   if "seer2"                            in t.lower()
                   and "dx cooling coil type"            in t.lower()
                   and "standard rated net cooling capacity" in t.lower()]
        if matched:
            return matched


    # parse one HTML table -> data rows only
    def _parse_html_table(table_html: str):
        trs = re.findall(r"(?is)<tr\b.*?>(.*?)</tr>", table_html)
        all_rows = []
        for tr in trs:
            cells = re.findall(r"(?is)<t[dh]\b.*?>(.*?)</t[dh]>", tr)
            cells = [_clean_cell(c) for c in cells]
            if cells and any(c != "" for c in cells):
                all_rows.append(cells)
        if not all_rows:
            return []

        # Locate header row
        hdr_idx = 0
        for i, r in enumerate(all_rows[:30]):
            joined = " | ".join(r).lower()
            if "standard rated net cooling capacity" in joined and \
               "dx cooling coil type" in joined:
                hdr_idx = i
                break

        # Data rows — skip any repeated header rows (from joined tables)
        data_rows = []
        for r in all_rows[hdr_idx + 1:]:
            joined = " | ".join(r).lower()
            if "standard rated net cooling capacity" in joined and \
               "dx cooling coil type" in joined:
                continue
            data_rows.append(r)
        return data_rows

    htm_file = _infer_htm_path(idf_path)
    if not htm_file or not htm_file.exists():
        return []

    html   = htm_file.read_text(encoding="utf-8", errors="ignore")
    tables = _find_seer2_tables(html)
    if not tables:
        return []

    IDX_COIL_NAME  = 0
    IDX_CAPACITY_W = 2

    out = []
    for t in tables:
        for r in _parse_html_table(t):
            if len(r) < 3:
                continue

            coil_name_raw = str(r[IDX_COIL_NAME]).strip()
            if not coil_name_raw:
                continue
            if coil_name_raw.lower() in {"nan", "coil name"}:
                continue
            if coil_name_raw.lower().startswith(("ansi", "note")):
                continue

            capacity_val = "N/A"
            v = _coerce_float(r[IDX_CAPACITY_W])
            if v is not None:
                capacity_val = v

            out.append({
                "Vintage":                                 vintage,
                "HVAC name":                               hvac_name,
                "Coil name":                               coil_name_raw,
                "Standard Rated Net Cooling Capacity [W]": capacity_val,
            })

    return out

def extract_cooling_coil_load(idf_path, htm_path=None):
    """
    Read Cooling Coils table from *_etc.htm (or *_etctbl.htm).

    IDF name example: ECC_0_cAVVG_Ex_etc.idf
      - HVAC name    = cAVVG
      - Vintage token = Ex -> Existing; New -> New Construction

    Table column layout (fixed by EnergyPlus):
      col 0: Coil name       (blank header in HTML)
      col 1: Type
      col 2: Design Coil Load [W]
      col 3+: other columns  (ignored)

    For each coil row outputs a dict with:
      Vintage, HVAC name, Coil name, Design Coil Load [W]

    NOTE: DX coils have blank (&nbsp;) for Design Coil Load — output as "N/A".
    """
    import re
    from pathlib import Path

    idf_path = Path(idf_path)

    # Parse Vintage + HVAC name from IDF filename
    parts = idf_path.stem.split("_")  # e.g., ECC, 0, cAVVG, Ex, etc
    hvac_name     = parts[2] if len(parts) >= 3 else "Unknown"
    vintage_token = parts[3] if len(parts) >= 4 else "Unknown"
    vintage = {"Ex": "Existing", "New": "New Construction"}.get(vintage_token, vintage_token)

    def _coerce_float(x):
        try:
            s = str(x).strip().replace("\u00A0", " ")
            s = re.sub(r"[,\s]+", "", s)
            return float(s)
        except Exception:
            return None

    def _html_unescape(s: str) -> str:
        return (s.replace("&nbsp;", " ")
                 .replace("&amp;", "&")
                 .replace("&lt;",  "<")
                 .replace("&gt;",  ">")
                 .replace("&quot;", '"')
                 .replace("&#39;", "'"))

    def _clean_cell(cell_html: str) -> str:
        cell_html = re.sub(r"(?is)<br\s*/?>", " ", cell_html)
        cell_html = re.sub(r"(?is)<.*?>",     " ", cell_html)
        cell_html = _html_unescape(cell_html)
        return re.sub(r"\s+", " ", cell_html).strip()

    def _infer_htm_path(p: Path) -> Path | None:
        if htm_path:
            hp = Path(htm_path)
            if hp.exists():
                return hp

        cand = p.with_suffix(".htm")
        if cand.exists():
            return cand

        cand = p.with_suffix(".html")
        if cand.exists():
            return cand

        if p.name.lower().endswith("_etc.idf"):
            cand = p.with_name(p.stem + "tbl.htm")
            if cand.exists():
                return cand

        prefix = "_".join(p.stem.split("_")[:4])
        cands = sorted(p.parent.glob(prefix + "*_etctbl.htm"))
        if cands:
            return cands[0]

        cands = sorted(p.parent.glob("*_etctbl.htm"))
        if cands:
            return cands[0]

        cands = sorted(p.parent.glob("*.htm")) + sorted(p.parent.glob("*.html"))
        return cands[0] if cands else None

    def _find_cooling_coils_table(html: str) -> str | None:
        tables = re.findall(r"(?is)<table\b.*?>.*?</table>", html)

        # Strict: all three key cooling columns present
        for t in tables:
            tl = t.lower()
            if "design coil load"         in tl and \
               "nominal total capacity"   in tl and \
               "nominal sensible capacity" in tl:
                return t

        return None

    def _parse_html_table(table_html: str):
        trs = re.findall(r"(?is)<tr\b.*?>(.*?)</tr>", table_html)
        all_rows = []
        for tr in trs:
            cells = re.findall(r"(?is)<t[dh]\b.*?>(.*?)</t[dh]>", tr)
            cells = [_clean_cell(c) for c in cells]
            if cells and any(c != "" for c in cells):
                all_rows.append(cells)
        if not all_rows:
            return []

        # Find header row: contains "design coil load"
        hdr_idx = 0
        for i, r in enumerate(all_rows[:30]):
            if "design coil load" in " | ".join(r).lower():
                hdr_idx = i
                break

        # Data rows only
        data_rows = []
        for r in all_rows[hdr_idx + 1:]:
            joined = " | ".join(r).lower()
            # skip repeated headers or footer notes
            if "design coil load" in joined:
                continue
            if joined.strip().startswith("nominal"):
                continue
            data_rows.append(r)

        return data_rows

    htm_file = _infer_htm_path(idf_path)
    if not htm_file or not htm_file.exists():
        return []

    html = htm_file.read_text(encoding="utf-8", errors="ignore")
    table_html = _find_cooling_coils_table(html)
    if not table_html:
        return []

    IDX_COIL_NAME      = 0
    IDX_DESIGN_LOAD_W  = 2   # Design Coil Load [W] — always col 2

    out = []
    for r in _parse_html_table(table_html):
        if len(r) < 3:
            continue

        coil_name_raw = str(r[IDX_COIL_NAME]).strip()
        if not coil_name_raw:
            continue
        if coil_name_raw.lower() in {"nan", "coil name", "type"}:
            continue
        if coil_name_raw.lower().startswith(("nominal", "note", "ansi")):
            continue

        design_load = "N/A"
        v = _coerce_float(r[IDX_DESIGN_LOAD_W])
        if v is not None:
            design_load = v

        out.append({
            "Vintage":              vintage,
            "HVAC name":            hvac_name,
            "Coil name":            coil_name_raw,
            "Design Coil Load [W]": design_load,
        })

    return out