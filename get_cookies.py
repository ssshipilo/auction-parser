import time
import json
import os
import configparser
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import capsolver

config = configparser.ConfigParser()
config.read("config.ini")
EMAIL = config["LOGIN"]["email"]
PASSWORD = config["LOGIN"]["password"]
CAPSOLVER = config["CAPTHA"]["capsolver"]
COOKIE_FILE = 'cookies.json'
capsolver.api_key = CAPSOLVER

def load_cookies():
    print("Loading cookies...")
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r') as f:
            cookies = json.load(f)
            print("Cookies loaded successfully.")
            return cookies
    print("No cookies found.")
    return None

def save_cookies(cookies_dict):
    print("Saving cookies...")
    with open(COOKIE_FILE, 'w') as f:
        json.dump(cookies_dict, f, indent=4)
    print("Cookies saved successfully.")

def solve_hcaptcha(site_key, url):
    try:
        print("Капча")
        solution = capsolver.solve({
            "type":"HCaptchaTaskProxyLess",
            "websiteKey": site_key,
            "websiteURL": url,
        })

        if solution['captchaKey']:
            return solution['captchaKey']
        else:
            return False
    except:
        return None

def get_cookies():
    while True:
        try:
            print("Setting up browser options...")
            options = Options()
            options.add_argument("--headless")
            options.set_preference("network.http.connection-timeout", 60)
            options.set_preference("network.http.response-timeout", 60)
            options.set_preference("dom.max_script_run_time", 60)

            print("Starting the browser...")
            driver = webdriver.Firefox(options=options)
            driver.set_page_load_timeout(300)
            print("Browser started.")

            driver.get("https://www.hemmings.com/auctions/account/sign-in")
            try:
                iframe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "main-iframe"))
                )
                if iframe:
                    iframe_src = iframe.get_attribute('src')
                    driver.get(iframe_src)
                    print(f"Successfully navigated to iframe")

                    site_key = driver.find_element(By.CSS_SELECTOR, '.h-captcha').get_attribute("data-sitekey")
                    iframe_url = driver.find_element(By.CSS_SELECTOR, '.h-captcha iframe').get_attribute("src")
                    token = solve_hcaptcha(site_key, iframe_url)
                    if token:
                        try:
                            print(token)
                            driver.execute_script(f"document.querySelector('[name=\"g-recaptcha-response\"]').value = '{token}';")
                            driver.execute_script(f"document.querySelector('[name=\"h-captcha-response\"]').value = '{token}';")
                            driver.get(f"https://www.hemmings.com/_Incapsula_Resource?g-recaptcha-response={token}&h-captcha-response={token}")
                            driver.get("https://www.hemmings.com/auctions/account/sign-in")
                        except Exception as e:
                            print(e)
                            pass
                        break
                    else:
                        print("Failed to solve CAPTCHA.")
                        continue
            except Exception as e:
                pass
            
            cookies_dict = load_cookies()
            if cookies_dict:
                print("Loaded cookies from file.")
                driver.get("https://www.hemmings.com")
                for cookie in cookies_dict:
                    driver.add_cookie(cookie)
                driver.get("https://www.hemmings.com/account")
                time.sleep(5)
                if driver.find_elements(By.CSS_SELECTOR, '.member-name'):
                    print("User is already logged in.")
                    driver.quit()
                    return cookies_dict
                else:
                    print("Cookies loaded but user not logged in. Trying to log in...")

            print("Navigating to the login page...")
            driver.get("https://www.hemmings.com/auctions/account/sign-in")
            time.sleep(5)

            try:
                print("Accepting cookies consent...")
                driver.find_element(By.CSS_SELECTOR, '.fc-cta-consent').click()
            except Exception as e:
                pass

            try:
                driver.execute_script("document.querySelector('.fc-cta-consent').click();")
            except Exception as e:
                pass

            print("Entering login credentials...")
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

            email_input.send_keys(EMAIL)
            password_input.send_keys(PASSWORD)
            submit_button.click()
            time.sleep(5)

            print("Checking login status...")
            driver.get("https://www.hemmings.com/account")
            time.sleep(5)

            if driver.find_elements(By.CSS_SELECTOR, '.member-name'):
                print("Login successful. Saving new cookies.")
                cookies = driver.get_cookies()
                cookie_jar = []
                for cookie in cookies:
                    try:
                        cookie_jar.append({
                            "name": cookie['name'],
                            "value": cookie['value'],
                            "domain": cookie['domain'],
                            "path": cookie['path']
                        })
                    except Exception as e:
                        print(f"Error processing cookie: {e}")
                save_cookies(cookie_jar)
                driver.quit()
                return cookie_jar
            else:
                print("Failed to log in.")
                driver.quit()
                return False
        except:
            continue

if __name__ == "__main__":
    print("Starting the cookie retrieval process...")
    cookies = get_cookies()
    print("Cookies:", cookies)
    print("Process completed.")

    