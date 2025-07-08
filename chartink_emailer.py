from playwright.sync_api import sync_playwright

def fetch():
    url = "https://chartink.com/screener/volumeshocker-p-100-2"
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)

        # Wait for the table to load (based on class name)
        page.wait_for_selector("table.table tbody tr")

        rows = page.query_selector_all("table.table tbody tr")

        for row in rows:
            cols = row.query_selector_all("td")
            if len(cols) < 4:
                continue
            symbol = cols[2].inner_text().strip()
            name = cols[1].inner_text().strip()
            price = cols[4].inner_text().strip()
            data.append({
                "nsecode": symbol,
                "name": name,
                "close": price
            })

        browser.close()
    return data
