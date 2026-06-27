"""
Build the 8760 load-shape compilation files from a template (per Robert/Chau).

Each row of the template defines one output file. The output file has 8760 rows:
  - columns A-K  : the constant metadata from that template row (repeated 8760x)
  - column L     : Hour of Year, 1..8760
  - column M     : the 8760 UECproportion (normalized load-shape) values read from
                   the per-run file named in template column M (looked up in
                   <source_dir>, i.e. the run's load_shapes folder).

Usage:
  python make_loadshape_compilation.py "<template.xlsx>" "<load_shapes dir>" "<output dir>"
"""
import sys, os, csv, re, openpyxl

def main(template_xlsx, source_dirs, out_dir, sub=None):
    # source_dirs may be ';'-separated (e.g. SFm 1975 + 1985 load_shapes).
    dirs = [d for d in source_dirs.split(";") if d]
    # sub: optional "OLD=NEW" applied to the col-M filename (e.g. "SFm&0=SFm&1").
    sub_old = sub_new = None
    if sub and "=" in sub:
        sub_old, sub_new = sub.split("=", 1)
    os.makedirs(out_dir, exist_ok=True)
    wb = openpyxl.load_workbook(template_xlsx, data_only=True)
    ws = wb["8760 post processing"] if "8760 post processing" in wb.sheetnames else wb.active
    rows = list(ws.iter_rows(values_only=True))
    header = ["" if c is None else str(c) for c in rows[0]]
    # 13 cols: A-K = 0..10 (constants), L = 11 (Hour of Year), M = 12 (source filename)
    # Each row is unique by TechID (col K = idx 10) + BldgLoc/CZ (col E = idx 4).
    used = {}
    written = skipped = fixed_loc = 0
    for r in rows[1:]:
        if r is None or all(c is None for c in r):
            continue
        vals = ["" if c is None else str(c) for c in r]
        while len(vals) < 13:
            vals.append("")
        constants = vals[0:11]          # A-K
        src_name = vals[12].strip()     # M = filename
        if not src_name:
            continue
        if sub_old:
            src_name = src_name.replace(sub_old, sub_new)
        src_path = next((os.path.join(d, src_name) for d in dirs
                         if os.path.exists(os.path.join(d, src_name))), None)
        if src_path is None:
            print("  MISSING source:", src_name); skipped += 1; continue
        with open(src_path, newline="") as f:
            rd = csv.reader(f)
            next(rd)                     # skip "Hour,LoadShape" header
            shape = [row[1] for row in rd if row]
        if len(shape) != 8760:
            print(f"  SKIP ({len(shape)} values): {src_name}"); skipped += 1; continue
        # Climate zone = the source file's CZ (reliable). The template's BldgLoc
        # column (col E) is misaligned by +1 on some rows, so correct it here.
        m = re.match(r'CZ0*(\d+)__', src_name)
        if m:
            cznum = int(m.group(1))
            if constants[4] != str(cznum):
                fixed_loc += 1
            constants = constants[:4] + [str(cznum)] + constants[5:]
            cz = "CZ%02d" % cznum
        else:
            cz = "CZ" + constants[4]
        # unique, eTRM-style output name: <TechID>__CZxx.csv
        techid = vals[10]
        base = re.sub(r'[\\/:*?"<>|]', '_', f"{techid}__{cz}")
        name = base + ".csv"
        if name in used:
            used[name] += 1
            name = f"{base}__{used[name]}.csv"
            print("  WARNING duplicate key, suffixed:", name)
        else:
            used[name] = 1
        out_path = os.path.join(out_dir, name)
        with open(out_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            for i in range(8760):
                w.writerow(constants + [i + 1, shape[i]])
        written += 1
    print(f"wrote {written} compilation files to {out_dir}  (skipped {skipped}, BldgLoc corrected on {fixed_loc} rows)")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3],
         sys.argv[4] if len(sys.argv) > 4 else None)
