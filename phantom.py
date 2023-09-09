from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

phantom_instance = None
locked = False

def get():
    global phantom_instance, locked

    if locked:
        # Wait for 100 milliseconds and try again if locked
        time.sleep(0.1)
        return get()

    locked = True

    if phantom_instance is not None:
        locked = False
        return phantom_instance

    # Create a PhantomJS instance
    desired_capabilities = DesiredCapabilities.PHANTOMJS.copy()
    desired_capabilities['phantomjs.page.settings.userAgent'] = (
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    )
    phantom_instance = webdriver.PhantomJS(desired_capabilities=desired_capabilities)

    locked = False
    return phantom_instance

def close():
    global phantom_instance

    if phantom_instance is not None:
        phantom_instance.quit()
        phantom_instance = None
