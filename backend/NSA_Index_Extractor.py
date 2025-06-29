import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO

def fetch_nifty_100_dynamic():
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0"})

    # Step 1: Get the page and extract CSV link
    page_url = "https://www.nseindia.com/products-services/indices-nifty100-index"
    page_resp = sess.get(page_url, timeout=10)
    page_resp.raise_for_status()
    soup = BeautifulSoup(page_resp.text, "html.parser")
    link = soup.find("a", string=lambda t: t and "Download List of Nifty 100 stocks" in t)
    if not link or not link.get("href"):
        raise RuntimeError("CSV link not found")
    csv_url = link["href"]
    if not csv_url.startswith("http"):
        csv_url = "https://www.nseindia.com" + csv_url

    # Step 2: Download the CSV
    csv_resp = sess.get(csv_url, timeout=10)
    csv_resp.raise_for_status()

    # Step 3: Load CSV properly (do NOT skip rows)
    df = pd.read_csv(StringIO(csv_resp.text), encoding="utf-8", on_bad_lines="skip")

    print("CSV Columns:", df.columns.tolist())

    # Step 4: Match columns flexibly
    col_lower = {c.lower(): c for c in df.columns}
    required = {}
    for key in ["symbol", "company", "industry"]:
        matches = [orig for lower, orig in col_lower.items() if key in lower]
        if matches:
            required[key] = matches[0]
        else:
            raise RuntimeError(f"Couldn't find column containing '{key}' in {df.columns.tolist()}")

    # Step 5: Build list of stocks
    data = []
    for _, r in df.iterrows():
        data.append({
            "symbol": f"{r[required['symbol']].strip()}.NS",
            "display_symbol": r[required['symbol']].strip(),
            "name": r[required['company']].strip(),
            "sector": r[required['industry']].strip()
        })
    return data

# Run and print sample
if __name__ == "__main__":
    stocks = fetch_nifty_100_dynamic()
    print("Sample:", stocks[:5])
