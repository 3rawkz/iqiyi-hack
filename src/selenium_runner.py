import os
import threading
import sys

from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.common.exceptions import TimeoutException
try:
    import pyvirtualdisplay
except ImportError:
    pass

from config import PORT


class SeleniumRunner(threading.Thread):
    def __init__(self, lock, page_url):
        self.lock = lock
        self.page_url = page_url

        super(SeleniumRunner, self).__init__()

    def run(self):
        if 'pyvirtualdisplay' in globals():
            display = pyvirtualdisplay.Display()
            display.start()

        self.run_firefox()

        if 'pyvirtualdisplay' in globals():
            display.stop()

    def run_firefox(self):
        proxy = Proxy({
            'proxyType': ProxyType.PAC,
            'proxyAutoconfigUrl': 'http://localhost:%d/proxy.pac' % PORT,
        })

        kwargs = {'log_file': sys.stdout}
        if os.getenv('FIREFOX_PATH'):
            kwargs['firefox_path'] = os.getenv('FIREFOX_PATH')
        firefox_binary = FirefoxBinary(**kwargs)
        driver = webdriver.Firefox(proxy=proxy, firefox_binary=firefox_binary)
        driver.set_page_load_timeout(10)
        try:
            driver.get(self.page_url)
        except TimeoutException:
            # Not requiring fully loading the page. Just need proxied requests
            pass

        print('Waiting for the proxy server')

        self.lock.acquire()

        print('Leaving...')

        driver.quit()

        self.lock.release()
