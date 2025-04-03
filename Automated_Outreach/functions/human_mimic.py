import time
import random
from selenium.webdriver.common.action_chains import ActionChains

def human_sleep(base=2, variance=1):
    delay = max(0, random.uniform(base - variance, base + variance))
    time.sleep(delay)

def human_scroll(driver, total_scrolls=5):
    for _ in range(total_scrolls):
        scroll_amount = random.randint(300, 900)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        human_sleep(1, 0.5)

def random_hover(driver, selector="a"):
    try:
        elements = driver.find_elements("css selector", selector)
        if elements:
            el = random.choice(elements)
            ActionChains(driver).move_to_element(el).perform()
            human_sleep(1, 0.3)
    except Exception:
        pass
