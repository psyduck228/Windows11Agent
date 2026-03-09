from playwright.sync_api import sync_playwright
import time

def visual_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")

        # Click the button once
        button = page.locator('button', has_text="Analyze Startup Processes").first
        button.wait_for(state="visible", timeout=10000)
        button.click()

        # Click it again quickly to trigger the rate limit error
        button.click()

        # Wait a moment for the toast to appear
        time.sleep(2)

        page.screenshot(path="screenshot_toast.png")
        print("Screenshot saved to screenshot_toast.png")

        browser.close()

if __name__ == "__main__":
    visual_test()
