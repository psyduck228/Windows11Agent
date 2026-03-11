from playwright.sync_api import sync_playwright

def test_visual():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        page.screenshot(path="screenshot_init.png")
        print("Screenshot saved to screenshot_init.png")

        # Check what the tooltip looks like on a disabled button
        # Clear Chat button
        page.hover('button:has-text("Clear Chat History")')
        page.wait_for_timeout(1000)
        page.screenshot(path="screenshot_tooltip.png")

        browser.close()

test_visual()
