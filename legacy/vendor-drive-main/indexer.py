"""
File indexing.

When a file is uploaded we keep the ORIGINAL on disk untouched. Separately we
read it once and build a plain-text index of what's inside -- sheet names and
every row as "Header=value | Header=value" lines, each tagged with where it
came from ([Sheet1 | row 12]). That text is what the search scans, so the AI
can answer "which file / which sheet / which row" and point you straight back
to the real file. Nothing here rewrites or "imports rows into a database" --
the spreadsheet stays a spreadsheet.

Supported for deep indexing: .xlsx .xlsm .xls .csv .tsv .txt
Anything else is still stored and searchable by its file name.
"""
import os
import re
import csv

# Cap how much extracted text we store/scan per file (keeps the DB and the AI
# context sane even with hundreds of big spreadsheets).
MAX_INDEX_CHARS = int(os.getenv("MAX_INDEX_CHARS", "60000"))

TABULAR = {".xlsx", ".xlsm", ".xltx", ".xls"}
DELIMITED = {".csv", ".tsv", ".txt"}


def _clip(text: str) -> str:
    if len(text) > MAX_INDEX_CHARS:
        return text[:MAX_INDEX_CHARS] + "\n...[index truncated -- open the file for the rest]"
    return text


def _header_index(rows):
    """Find where the table really starts: the row with the most filled cells
    in the first several rows. This just skips a title/blurb line above the
    headers -- it does NOT map columns into any fixed schema."""
    best_idx, best_score = 0, -1
    for idx, row in enumerate(rows[:12]):
        non_empty = sum(1 for c in row if c not in (None, ""))
        if non_empty < 2:
            continue
        if non_empty > best_score:
            best_score, best_idx = non_empty, idx
    return best_idx


def _rows_to_text(sheet_name, rows, max_rows=1000):
    """Turn a table into tagged, searchable lines (header row auto-located)."""
    if not rows:
        return "", 0
    h = _header_index(rows)
    rows = rows[h:]
    headers = [str(c).strip() if c not in (None, "") else f"Col{i+1}"
               for i, c in enumerate(rows[0])]
    lines = [f"[{sheet_name}] columns: " + " | ".join(headers)]
    body = rows[1:max_rows + 1]
    for ridx, row in enumerate(body, start=2):
        cells = []
        for i, val in enumerate(row):
            if val in (None, ""):
                continue
            head = headers[i] if i < len(headers) else f"Col{i+1}"
            cells.append(f"{head}={str(val).strip()}")
        if cells:
            lines.append(f"[{sheet_name} | row {ridx}] " + " | ".join(cells))
    return "\n".join(lines), max(0, len(body))


def build_index(path: str, ext: str):
    """
    Read the file once and return (search_text, sheet_count, row_count).
    Never raises -- on any problem it degrades to an empty index so the upload
    still succeeds and the file is at least searchable by name.
    """
    ext = (ext or "").lower()
    try:
        if ext in TABULAR:
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            blocks, total_rows = [], 0
            for ws in wb.worksheets:
                rows = list(ws.iter_rows(values_only=True))
                # drop fully-empty rows
                rows = [r for r in rows if any(c not in (None, "") for c in r)]
                if not rows:
                    continue
                text, n = _rows_to_text(ws.title, rows)
                total_rows += n
                blocks.append(text)
            wb.close()
            return _clip("\n\n".join(blocks)), len(blocks), total_rows

        if ext in DELIMITED:
            delim = "\t" if ext == ".tsv" else ","
            with open(path, encoding="utf-8-sig", errors="replace") as f:
                if ext == ".txt":
                    raw = f.read()
                    return _clip(raw), 1, raw.count("\n")
                rows = [r for r in csv.reader(f, delimiter=delim)
                        if any(str(c).strip() for c in r)]
            text, n = _rows_to_text("Sheet1", rows)
            return _clip(text), 1, n
    except Exception as e:
        return f"(could not read file contents: {e})", 0, 0

    # Unknown type -- filename-only index (still findable).
    return "", 0, 0


EDITABLE = TABULAR | {".csv", ".tsv"}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


def _read_headers(path, ext):
    """Return the header list of the first/active sheet (header row auto-located)."""
    ext = (ext or "").lower()
    if ext in TABULAR:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        rows = [r for r in wb.active.iter_rows(values_only=True)
                if any(c not in (None, "") for c in r)]
        wb.close()
    else:
        delim = "\t" if ext == ".tsv" else ","
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            rows = [r for r in csv.reader(f, delimiter=delim) if any(str(c).strip() for c in r)]
    if not rows:
        return []
    rows = rows[_header_index(rows):]
    return [str(c).strip() if c not in (None, "") else f"Col{i+1}"
            for i, c in enumerate(rows[0])]


def _aligned(headers, values):
    """Map a {header: value} dict onto the sheet's real columns, in order."""
    norm = {_norm(k): v for k, v in (values or {}).items()}
    return [norm.get(_norm(h), "") for h in headers]


def append_row(path: str, ext: str, values: dict):
    """Add ONE row to the first/active sheet, aligned to its columns. Edits in place."""
    ext = (ext or "").lower()
    headers = _read_headers(path, ext)
    if not headers:
        raise ValueError("This file has no header row to add under.")
    row = _aligned(headers, values)
    if ext in TABULAR:
        import openpyxl
        wb = openpyxl.load_workbook(path)          # writable (keeps other sheets)
        wb.active.append(row)
        wb.save(path); wb.close()
    elif ext in {".csv", ".tsv"}:
        delim = "\t" if ext == ".tsv" else ","
        with open(path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f, delimiter=delim).writerow(row)
    else:
        raise ValueError("Rows can only be added to spreadsheets or CSV files.")
    return headers


def write_table(path: str, ext: str, headers: list, rows: list):
    """Replace the first/active sheet's data with the given headers + rows.
    Other sheets in an .xlsx are left untouched."""
    ext = (ext or "").lower()
    if ext in TABULAR:
        import openpyxl
        wb = openpyxl.load_workbook(path)
        ws = wb.active
        if ws.max_row:
            ws.delete_rows(1, ws.max_row)
        ws.append([str(h) for h in headers])
        for r in rows:
            ws.append([("" if c is None else c) for c in r])
        wb.save(path); wb.close()
    elif ext in {".csv", ".tsv"}:
        delim = "\t" if ext == ".tsv" else ","
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=delim)
            w.writerow(headers)
            for r in rows:
                w.writerow(["" if c is None else c for c in r])
    else:
        raise ValueError("Only spreadsheets or CSV files can be edited.")


def preview(path: str, ext: str, max_rows: int = 50):
    """
    Build a light preview for the file viewer: sheet names + the first rows.
    Returns {"sheets": [{"name","headers","rows"}]} or {"error": "..."}.
    """
    ext = (ext or "").lower()
    try:
        if ext in TABULAR:
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            sheets = []
            for ws in wb.worksheets:
                rows = list(ws.iter_rows(values_only=True))
                rows = [r for r in rows if any(c not in (None, "") for c in r)]
                if not rows:
                    continue
                rows = rows[_header_index(rows):]
                headers = [str(c).strip() if c not in (None, "") else f"Col{i+1}"
                           for i, c in enumerate(rows[0])]
                body = [[("" if c is None else str(c)) for c in r]
                        for r in rows[1:max_rows + 1]]
                sheets.append({"name": ws.title, "headers": headers, "rows": body,
                               "total_rows": len(rows) - 1})
            wb.close()
            return {"sheets": sheets}

        if ext in DELIMITED:
            delim = "\t" if ext == ".tsv" else ","
            with open(path, encoding="utf-8-sig", errors="replace") as f:
                if ext == ".txt":
                    return {"text": f.read()[:20000]}
                rows = [r for r in csv.reader(f, delimiter=delim)]
            rows = [r for r in rows if any(str(c).strip() for c in r)]
            if not rows:
                return {"sheets": []}
            rows = rows[_header_index(rows):]
            headers = [str(c).strip() or f"Col{i+1}" for i, c in enumerate(rows[0])]
            body = rows[1:max_rows + 1]
            return {"sheets": [{"name": "Sheet1", "headers": headers,
                               "rows": body, "total_rows": len(rows) - 1}]}
    except Exception as e:
        return {"error": str(e)}

    return {"error": "Preview not available for this file type -- use Download."}
