from selenium import webdriver

from logging import config
config.fileConfig('dev.logger.conf')
from PaymentsDive import PaymentsDive

driver = webdriver.Chrome()

parser = PaymentsDive(driver)
docs = parser.content()


print(*docs, sep='\n\r\n')