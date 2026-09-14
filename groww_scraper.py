from importlib import import_module
import csv

def scrape_groww_portfolio(email_id):
    try:
        webdriver = import_module("selenium.webdriver")
        By = import_module("selenium.webdriver.common.by").By
        Keys = import_module("selenium.webdriver.common.keys").Keys
        WebDriverWait = import_module("selenium.webdriver.support.ui").WebDriverWait
        EC = import_module("selenium.webdriver.support.expected_conditions")
    except ModuleNotFoundError as exc:
        if exc.name == "selenium" or exc.name.startswith("selenium."):
            raise RuntimeError(
                "Selenium is not installed. Run: python -m pip install selenium"
            ) from exc
        raise

    driver = webdriver.Chrome()
    driver.get("https://groww.in/login")

    wait = WebDriverWait(driver, 30)

    # Locate the email/phone input field directly
    email_input = wait.until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='text' or @type='email' or @type='tel']"))
    )
    email_input.send_keys(email_id)
    email_input.send_keys(Keys.RETURN)

    print("⚠️ Please complete OTP login in the browser window.")
    input("Press Enter here after OTP login is successful...")

    # Navigate to portfolio after login
    driver.get("https://groww.in/portfolio/stocks")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    portfolio_data = []
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if cols:
            values = [col.text.strip() for col in cols]
            stock_index = next((index for index, value in enumerate(values) if value), None)
            if stock_index is None:
                continue

            stock = values[stock_index]
            remaining_values = values[stock_index + 1:]
            quantity = remaining_values[0] if remaining_values else ""
            price = remaining_values[1] if len(remaining_values) > 1 else ""
            portfolio_data.append([stock, quantity, price])

    with open("groww_portfolio.csv", "w", newline="", encoding="utf-8") as portfolio_file:
        writer = csv.writer(portfolio_file)
        writer.writerow(["Stock", "Quantity", "Price"])
        writer.writerows(portfolio_data)
    print("✅ Portfolio saved to groww_portfolio.csv")

    driver.quit()

if __name__ == "__main__":
    scrape_groww_portfolio("raviteja.kamisetti@gmail.com")
