"""
Load Test: Frame Parser API
============================
Tests the /v1/parse endpoint with "The buyer purchased the goods"
- 4 concurrency scenarios (1, 2, 3, 4 concurrent threads)
- 60 seconds per run
- 10 repeats per scenario
- Outputs Excel report with per-run details and averages

Requirements: pip install requests openpyxl
"""

import requests
import time
import concurrent.futures
import json
import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# ── Configuration ──────────────────────────────────────────
API_URL = "http://10.119.105.69/v1/parse"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test1234"
}
PAYLOAD = json.dumps({"text": "The buyer purchased the goods"})
DURATION = 60        # seconds per run
REPEATS = 10         # runs per concurrency level
CONCURRENCY_LEVELS = [1, 2, 3, 4]
# ───────────────────────────────────────────────────────────


def single_request():
    try:
        r = requests.post(API_URL, headers=HEADERS, data=PAYLOAD, timeout=30)
        return r.status_code == 200
    except Exception:
        return False


def run_load_test(concurrency, duration=DURATION):
    total = 0
    success = 0
    errors = 0
    end_time = time.time() + duration

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        while time.time() < end_time:
            futures = []
            for _ in range(concurrency):
                if time.time() >= end_time:
                    break
                futures.append(executor.submit(single_request))
            for f in concurrent.futures.as_completed(futures):
                total += 1
                if f.result():
                    success += 1
                else:
                    errors += 1

    return total, success, errors


def build_report(results):
    wb = Workbook()
    thin = Side(style='thin')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    hdr_font = Font(bold=True, color="FFFFFF", size=11)
    hdr_fill = PatternFill('solid', fgColor='2F5496')
    avg_fill = PatternFill('solid', fgColor='D6E4F0')
    avg_font = Font(bold=True, size=11)
    center = Alignment(horizontal='center', vertical='center')

    # ── Per-concurrency sheets ──
    for idx, c in enumerate(CONCURRENCY_LEVELS):
        ws = wb.active if idx == 0 else wb.create_sheet()
        ws.title = f"Concurrency {c}"

        ws.merge_cells('A1:E1')
        ws['A1'] = f"Concurrency = {c}  |  Duration = 60s/run  |  10 Runs"
        ws['A1'].font = Font(bold=True, size=13, color='2F5496')
        ws['A1'].alignment = Alignment(horizontal='center')

        cols = ["Run", "Total Hits", "Successful Hits", "Errors", "Hits/min"]
        for ci, h in enumerate(cols, 1):
            cell = ws.cell(row=3, column=ci, value=h)
            cell.font = hdr_font
            cell.fill = hdr_fill
            cell.alignment = center
            cell.border = border

        for ri in range(REPEATS):
            row = 4 + ri
            t, s, e = results[c][ri]
            for ci, v in enumerate([ri + 1, t, s, e, s], 1):
                cell = ws.cell(row=row, column=ci, value=v)
                cell.alignment = center
                cell.border = border

        # Average row
        avg_row = 4 + REPEATS
        cell = ws.cell(row=avg_row, column=1, value="Average")
        cell.font = avg_font
        cell.fill = avg_fill
        cell.alignment = center
        cell.border = border

        for ci in range(2, 6):
            start = ws.cell(row=4, column=ci).coordinate
            end = ws.cell(row=3 + REPEATS, column=ci).coordinate
            cell = ws.cell(row=avg_row, column=ci)
            cell.value = f'=AVERAGE({start}:{end})'
            cell.number_format = '0.00'
            cell.font = avg_font
            cell.fill = avg_fill
            cell.alignment = center
            cell.border = border

        # Std Dev row
        std_row = avg_row + 1
        cell = ws.cell(row=std_row, column=1, value="Std Dev")
        cell.font = avg_font
        cell.fill = avg_fill
        cell.alignment = center
        cell.border = border

        for ci in range(2, 6):
            start = ws.cell(row=4, column=ci).coordinate
            end = ws.cell(row=3 + REPEATS, column=ci).coordinate
            cell = ws.cell(row=std_row, column=ci)
            cell.value = f'=STDEV({start}:{end})'
            cell.number_format = '0.00'
            cell.font = avg_font
            cell.fill = avg_fill
            cell.alignment = center
            cell.border = border

        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 14
        ws.column_dimensions['C'].width = 18
        ws.column_dimensions['D'].width = 10
        ws.column_dimensions['E'].width = 14

    # ── Summary sheet ──
    ws_s = wb.create_sheet("Summary", 0)
    ws_s.merge_cells('A1:F1')
    ws_s['A1'] = "Load Test Summary — Frame Parser API"
    ws_s['A1'].font = Font(bold=True, size=14, color='2F5496')
    ws_s['A1'].alignment = Alignment(horizontal='center')

    info = [
        ("Endpoint:", API_URL),
        ("Payload:", '"The buyer purchased the goods"'),
        ("Duration/run:", "60 seconds"),
        ("Repeats:", "10"),
    ]
    for i, (k, v) in enumerate(info, 3):
        ws_s.cell(row=i, column=1, value=k).font = Font(bold=True)
        ws_s.cell(row=i, column=2, value=v)

    sum_hdrs = ["Concurrency", "Avg Total Hits", "Avg Successful", "Avg Errors", "Avg Hits/min", "Std Dev Hits/min"]
    for ci, h in enumerate(sum_hdrs, 1):
        cell = ws_s.cell(row=8, column=ci, value=h)
        cell.font = hdr_font
        cell.fill = hdr_fill
        cell.alignment = center
        cell.border = border

    for ri, c in enumerate(CONCURRENCY_LEVELS):
        row = 9 + ri
        data = results[c]
        avg_total = sum(d[0] for d in data) / REPEATS
        avg_success = sum(d[1] for d in data) / REPEATS
        avg_errors = sum(d[2] for d in data) / REPEATS
        std_success = (sum((d[1] - avg_success) ** 2 for d in data) / REPEATS) ** 0.5
        vals = [c, avg_total, avg_success, avg_errors, avg_success, std_success]
        for ci, v in enumerate(vals, 1):
            cell = ws_s.cell(row=row, column=ci, value=round(v, 2))
            cell.alignment = center
            cell.border = border
            if ci > 1:
                cell.number_format = '0.00'

    for col, w in zip('ABCDEF', [14, 16, 16, 12, 16, 18]):
        ws_s.column_dimensions[col].width = w

    out = "load_test_report.xlsx"
    wb.save(out)
    print(f"\nReport saved to: {out}")


def main():
    # Quick connectivity check
    print("Testing API connectivity...", end=" ", flush=True)
    if not single_request():
        print("FAILED. Check API URL and auth.")
        sys.exit(1)
    print("OK\n")

    results = {}
    total_runs = len(CONCURRENCY_LEVELS) * REPEATS
    current = 0

    for c in CONCURRENCY_LEVELS:
        results[c] = []
        print(f"{'='*60}")
        print(f" Concurrency = {c}")
        print(f"{'='*60}")
        for rep in range(1, REPEATS + 1):
            current += 1
            print(f"  [{current}/{total_runs}] Run {rep}/10 (60s)...", end=" ", flush=True)
            t, s, e = run_load_test(c)
            results[c].append((t, s, e))
            print(f"hits={s}  errors={e}")

    # Print console summary
    print(f"\n{'='*60}")
    print(" SUMMARY")
    print(f"{'='*60}")
    print(f"{'Concurrency':>12} {'Avg Hits/min':>14} {'Std Dev':>10} {'Avg Errors':>12}")
    print(f"{'-'*50}")
    for c in CONCURRENCY_LEVELS:
        data = results[c]
        avg_s = sum(d[1] for d in data) / REPEATS
        std_s = (sum((d[1] - avg_s) ** 2 for d in data) / REPEATS) ** 0.5
        avg_e = sum(d[2] for d in data) / REPEATS
        print(f"{c:>12} {avg_s:>14.2f} {std_s:>10.2f} {avg_e:>12.2f}")

    build_report(results)


if __name__ == "__main__":
    main()
