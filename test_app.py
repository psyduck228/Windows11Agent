from playwright.sync_api import sync_playwright

def test_chat_rate_limit():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")

        # Click the first button we find
        page.locator('button', has_text="Analyze Startup Processes").first.wait_for(state="visible", timeout=10000)
        page.locator('button', has_text="Analyze Startup Processes").first.click()
        page.wait_for_timeout(3000) # give time for run and stream

        # Type first message
        chat_input = page.locator('textarea[placeholder="Ask a question about the diagnostic results..."]')
        chat_input.fill("Hello")
        chat_input.press("Enter")

        # Immediate second message
        chat_input.fill("World")
        chat_input.press("Enter")

        page.wait_for_timeout(1000)
        page.screenshot(path="screenshot.png")
        print("Screenshot saved to screenshot.png")

        browser.close()

test_chat_rate_limit()
