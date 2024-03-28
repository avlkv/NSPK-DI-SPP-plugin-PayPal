"""
Парсер плагина SPP

1/2 документ плагина
"""
import logging
import time
import dateparser
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from src.spp.types import SPP_document
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class PayPal:
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """

    SOURCE_NAME = 'PayPal'
    HOST = "https://newsroom.paypal-corp.com/news"
    _content_document: list[SPP_document]

    def __init__(self, webdriver: WebDriver, last_document: SPP_document = None, max_count_documents: int = 100,
                 *args, **kwargs):
        """
        Конструктор класса парсера

        По умолчанию внего ничего не передается, но если требуется (например: driver селениума), то нужно будет
        заполнить конфигурацию
        """
        # Обнуление списка
        self._content_document = []

        self.driver = webdriver
        self.wait = WebDriverWait(self.driver, timeout=20)
        self.max_count_documents = max_count_documents
        self.last_document = last_document

        # Логер должен подключаться так. Вся настройка лежит на платформе
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Parser class init completed")
        self.logger.info(f"Set source: {self.SOURCE_NAME}")
        ...

    def content(self) -> list[SPP_document]:
        """
        Главный метод парсера. Его будет вызывать платформа. Он вызывает метод _parse и возвращает список документов
        :return:
        :rtype:
        """
        self.logger.debug("Parse process start")
        try:
            self._parse()
        except Exception as e:
            self.logger.debug(f'Parsing stopped with error: {e}')
        else:
            self.logger.debug("Parse process finished")
        return self._content_document

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -

        self.driver.get(self.HOST)  # Открыть первую страницу с материалами
        time.sleep(5)

        # Окно с куками пропадает самостоятельно через 2-3 секунды
        try:
            cookies_btn = self.driver.find_element(By.ID, 'acceptAllButton').find_element(By.XPATH,
                                                                                          '//*[@id="acceptAllButton"]')
            self.driver.execute_script('arguments[0].click()', cookies_btn)
            self.logger.debug('Cookies убран')
        except:
            self.logger.exception('Не найден cookies')
            pass

        # self.logger.info('Прекращен поиск Cookies')
        # time.sleep(3)
        counter = 0
        flag = True
        while flag:

            self.logger.debug('Загрузка списка элементов...')
            doc_table = self.driver.find_element(By.CLASS_NAME, 'wd_item_list').find_elements(By.CLASS_NAME,
                                                                                              'wd_has-image')
            self.logger.debug('Обработка списка элементов...')

            # Цикл по всем строкам таблицы элементов на текущей странице
            for element in doc_table:

                element_locked = False

                try:
                    title = element.find_element(By.CLASS_NAME, 'wd_title').text
                    # title = element.find_element(By.XPATH, '//*[@id="feed-item-title-1"]/a').text

                except:
                    self.logger.exception('Не удалось извлечь title')
                    title = ' '

                # try:
                #    other_data = element.find_elements(By.CLASS_NAME, "wd_category_link_list").text
                # except:
                #    self.logger.exception('Не удалось извлечь other_data')
                #    other_data = ''
                # // *[ @ id = "main-content"] / ul / li[1] / div[2] / span[2]
                # // *[ @ id = "main-content"] / ul / li[2] / div[2] / span[2]

                try:
                    date = dateparser.parse(element.find_element(By.CLASS_NAME, 'wd_date').text)
                except:
                    self.logger.exception('Не удалось извлечь date_text')
                    date = None
                    continue

                # try:
                #    date = dateparser.parse(date_text)
                # except:
                #    self.logger.exception('Не удалось извлечь date')
                #    date = None

                try:
                    abstract = element.find_element(By.CLASS_NAME, 'wd_summary').text
                except:
                    self.logger.exception('Не удалось извлечь abstract')
                    abstract = ''

                try:
                    web_link = element.find_element(By.TAG_NAME, 'a').get_attribute('href')
                except:
                    self.logger.exception('Не удалось извлечь web_link')
                    web_link = None
                    continue

                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[1])
                self.driver.get(web_link)
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.wd_news_body')))

                text_content = self.driver.find_element(By.CLASS_NAME, 'wd_news_body').text

                cats = [x.text for x in self.driver.find_elements(By.CLASS_NAME, 'wd_category_link')]

                other_data = {'categories': cats}

                doc = SPP_document(
                    doc_id=None,
                    title=title,
                    abstract=abstract,
                    text=text_content,
                    web_link=web_link,
                    local_link=None,
                    other_data=other_data,
                    pub_date=date,
                    load_date=datetime.now(),
                )

                self.find_document(doc)

                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

            try:
                pagination_arrow = self.driver.find_element(By.XPATH, '//li[contains(@class, \'wd_page_next\')]')
                self.driver.execute_script('arguments[0].click()', pagination_arrow)
                # pagination_arrow.click()
                time.sleep(3)
                # pg_num = self.driver.find_element(By.ID, 'current_page').text
                self.logger.debug(f'Выполнен переход на след. страницу')

                # if int(pg_num) > 3:
                #    self.logger.info('Выполнен переход на 4-ую страницу. Принудительное завершение парсинга.')
                # break

            except:
                self.logger.exception('Не удалось найти переход на след. страницу. Прерывание цикла обработки')
                break

        # Логирование найденного документа
        # self.logger.info(self._find_document_text_for_logger(_content_document))

        # ---
        # ========================================
        ...

    def _find_document_text_for_logger(self, doc: SPP_document):
        """
        Единый для всех парсеров метод, который подготовит на основе SPP_document строку для логера
        :param doc: Документ, полученный парсером во время своей работы
        :type doc:
        :return: Строка для логера на основе документа
        :rtype:
        """
        return f"Find document | name: {doc.title} | link to web: {doc.web_link} | publication date: {doc.pub_date}"

    def find_document(self, _doc: SPP_document):
        """
        Метод для обработки найденного документа источника
        """
        if self.last_document and self.last_document.hash == _doc.hash:
            raise Exception(f"Find already existing document ({self.last_document})")

        if self.max_count_documents and len(self._content_document) >= self.max_count_documents:
            raise Exception(f"Max count articles reached ({self.max_count_documents})")

        self._content_document.append(_doc)
        self.logger.info(self._find_document_text_for_logger(_doc))
