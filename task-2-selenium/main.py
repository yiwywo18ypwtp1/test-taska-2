import time
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import re

# from parse_details import get_details
# from parse_spec import get_specs
from export import save_to_json, save_to_excel

driver = webdriver.Chrome()

try:
    driver.get('https://rozetka.com.ua/')

    search_field = driver.find_element(By.XPATH, "//input[@name='search']")
    search_field.clear()
    search_field.send_keys("Apple iPhone 15 128GB Black", Keys.RETURN)

    # подгружаем динамические файлы
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='goods-tile']"))
    )
    print("current page:", driver.title)
    driver.save_screenshot("result/images/search_results.png")

    item_tile = driver.find_element(By.XPATH, "//div[@class='goods-tile']")

    item_page = item_tile.find_element(
        By.XPATH,
        ".//*[@class='product-link']//a"
    ).get_attribute('href')
    print(item_page)

    if item_page:
        driver.get(item_page)
        print("current page:", driver.title)
    else:
        print("page unfound")

    time.sleep(3)
    print("current page:", driver.title)
    driver.save_screenshot("result/images/product_page.png")

    product = {}

    # Ожидание загрузки страницы
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'title__font')]"))
    )

    # product['title'] = driver.find_element(By.XPATH, "//h1[contains(@class, 'title__font')]").text - более короткий вариант тайтла (без "– фото, відгуки, характеристики в інтернет-магазині ROZETKA...." в конце)
    product['title'] = driver.title

    # цвет
    try:
        product['color'] = driver.find_element(By.XPATH, "//span[text()='Колір: ']/following-sibling::span").text.strip()
    except NoSuchElementException:
        product['color'] = None

    # память
    try:
        product['memory'] = driver.find_element(By.XPATH, "//span[contains(text(), 'Вбудована')]/following-sibling::span").text.strip()
    except NoSuchElementException:
        product['memory'] = None

    # цена
    try:
        product['default_price'] = driver.find_element(By.XPATH, "//*[contains(@class, 'product-price__small')]").text
        product['discount_price'] = driver.find_element(By.XPATH, "//*[contains(@class, 'product-price__big')]").text.strip()
    except NoSuchElementException:
        default_price, discount_price = None, None

    # код
    try:
        item_code = driver.find_element(By.XPATH, "//*[@class='desktop']//div[@class='rating text-base']//span").text.strip()
        product['item_code'] = ''.join(filter(str.isdigit, item_code)) if item_code else None
    except NoSuchElementException as e:
        product['item_code'] = None

    # картинки
    images = []
    for img in driver.find_elements(By.XPATH, "//div[@class='product-about__left']//img[contains(@src, 'goods/images')]"):
        src = img.get_attribute('src').split(' ')[0]
        images.append(src)
    product['item_photos'] = images

    # серийный номер
    product['serial'] = re.search(r"\(([\w\-\/]+)\)", product['title']).group(1)

    # дисплей
    try:
        about_section = driver.find_element(By.XPATH, "//*[contains(@class, 'product-about__sticky')]//*[contains(@class, 'mt-4')]").text.strip()
        product['display_res'] = re.search(r"\b(\d+x\d+)\b", about_section).group(1)
    except NoSuchElementException:
        product['display_res'] = None

    # характеристики
    driver.get('https://rozetka.com.ua/ua/apple-iphone-15-128gb-black/p395460480/characteristics/')
    item_characteristics = {}

    items = driver.find_elements(By.XPATH, "//main[contains(@class, 'product-tabs__content')]//*[contains(@class, 'item')]")
    for item in items:
        try:
            title = item.find_element(By.XPATH, ".//*[contains(@class, 'label')]//span").text

            value = item.find_element(By.XPATH, ".//*[contains(@class, 'value')]").text

            item_characteristics[title] = value

        except NoSuchElementException:
            continue
    product['item_spec'] = item_characteristics

    # принтим детали в консоль
    for key, value in product.items():
        print(f'{key}: {value}')

    # експорт в xlsx
    save_to_excel(product)

    # експорт .json (для теста/себя)
    save_to_json(product)

finally:
    driver.quit()
