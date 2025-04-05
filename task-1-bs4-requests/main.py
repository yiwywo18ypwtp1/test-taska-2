from xml.sax.handler import property_dom_node

from bs4 import BeautifulSoup
import requests
import json
import re

# from parse_spec import get_specs
# from parse_details import get_details
from export import save_to_excel, save_to_json


def get_soup(url):
    response = requests.get(url)

    if response.status_code == 200:
        html_content = response.text
        print(f'page loaded successful: {response.status_code}')

        return BeautifulSoup(html_content, 'html.parser')
    else:
        print(f'cant load page: {response.status_code}')

        return None



soup = get_soup('https://rozetka.com.ua/apple-iphone-15-128gb-black/p395460480/')

product = {}

try:
    product['title'] = soup.find(class_='title__font').text.strip()
except (AttributeError, AssertionError):
    product['title'] = None

try:
    product['color'] = soup.find('span', string='Колір: ').find_next('span').text.strip()
    product['memory'] = soup.find('span', string="Вбудована пам'ять: ").find_next('span').text.strip()
except (AttributeError, AssertionError, IndexError):
    product['color'] = None
    product['memory'] = None

try:
    product['default_price'] = soup.find(class_='product-price__small').text.strip()
    product['discount_price'] = soup.find(class_='product-price__big').text.strip()
except (AttributeError, AssertionError):
    product['default_price'] = None
    product['discount_price'] = None

try:
    product['item_code'] = ''.join(filter(str.isdigit, soup.find('div', class_='rating').find('span').text))
except (AttributeError, AssertionError):
    product['item_code'] = None

try:
    images = []
    for img in soup.find_all('img'):
        src = img.get('src')
        if 'goods/images' in src:
            src = src.split(' ')[0]  # убираем все лишнее после нужной ссылки
            images.append(src)

    product['item_photos'] = images
except (AttributeError, AssertionError):
    product['item_photos'] = None

try:
    product['serial'] = re.search(r"\(([\w\-\/]+)\)", soup.find(class_='title__font').text).group(1)
except (AttributeError, AssertionError):
    product['serial'] = None

try:
    product['display_res'] = re.search(r"\b(\d+x\d+)\b",
                                       soup.find(class_='product-about__sticky').find(class_='mt-4').text).group(1)
except (AttributeError, AssertionError):
    product['display_res'] = None

try:
    soup = get_soup('https://rozetka.com.ua/ua/apple-iphone-15-128gb-black/p395460480/characteristics/')

    characteristics = soup.find(class_='product-tabs__content').find_all(class_='item')
    item_characteristics = {}

    for item in characteristics:
        title = item.find(class_='label').find('span').text
        value = item.find(class_='value').text

        item_characteristics[title] = value

    product['item_spec'] = item_characteristics

except Exception as e:
    product['item_spec'] = None
    print(f"cant get specs - {e}")

# експорт в xlsx
save_to_excel(product)

# експорт .json (для теста/себя)
save_to_json(product)

# принтим в консоль
for key, value in product.items():
    print(f"{key}: {value}")
