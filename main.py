from selenium import webdriver

from logging import config
config.fileConfig('dev.logger.conf')
from PayPal import PayPal

driver = webdriver.Chrome()

parser = PayPal(driver)
docs = parser.content()


print(*docs, sep='\n\r\n')