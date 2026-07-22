import sys, os, django, time
sys.path.append(os.path.join(os.getcwd(), 'backend_v4'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.osint.services import chromedriver_context

with chromedriver_context() as driver:
    driver.get('https://www.volanteomaleta.com/')
    time.sleep(3)
    from selenium.webdriver.common.by import By
    search_box = driver.find_element(By.XPATH, "//form[contains(@action, 'patente')]//input[@name='term']")
    search_box.send_keys('PBHF56')
    btn = driver.find_element(By.XPATH, "//form[contains(@action, 'patente')]//button[@type='submit']")
    btn.click()
    time.sleep(4)
    html = driver.find_element(By.XPATH, "/html/body/div[2]/div").get_attribute('innerHTML')
    print('Result HTML:', html[:2000])
