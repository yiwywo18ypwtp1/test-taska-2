import re

from playwright.sync_api import sync_playwright
import time
import random

from export import save_to_json, save_to_excel


# имитируем поведение человека
def human_delay():
    time.sleep(random.uniform(0.5, 2.0))


# функция для проверки на ниличие елемента (чтоб не повторять .count() else None каждый раз и присваивать значение в одну строку, а не в две)
def get_text_or_none(page, selector):
    locator = page.locator(selector).first
    return locator.inner_text() if locator.count() else None


with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        channel="chrome",
        args=[
            "--disable-blink-features=AutomationControlled",
            "--start-maximized"
        ],
        slow_mo=500  # замедление действий (специально)
    )

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        viewport={"width": 1920, "height": 1080}
    )

    page = context.new_page()

    try:
        page.goto('https://rozetka.com.ua/', timeout=15000)
        human_delay()

        search = page.locator("input[name='search']")
        search.click(delay=100)
        human_delay()

        search.fill("Apple iPhone 15 128GB Black")
        human_delay()

        search.press("Enter", delay=100)
        human_delay()

        page.screenshot(path="result/images/search_result.png")

        page.wait_for_selector("div.goods-tile", timeout=5000)

        item = page.locator("div.goods-tile").first

        # кликаем по товару
        with page.expect_navigation():
            item.locator("a").first.click(delay=100)

        human_delay()
        page.screenshot(path="result/images/product_page.png")


        product = {}

        page.wait_for_selector("xpath=//*[@class='desktop']//*[contains(@class, 'title__font')]")


        product['title'] = get_text_or_none(page, "xpath=//h1[contains(@class, 'title__font')]")

        product['color'] = get_text_or_none(page, "xpath=//span[contains(text(), 'Колір')]/following-sibling::span")
        product['memory'] = get_text_or_none(page, "xpath=//span[contains(text(), 'Вбудована')]/following-sibling::span")

        product['default_price'] = get_text_or_none(page, "xpath=//*[contains(@class, 'product-price__small')]")
        product['discount_price'] = get_text_or_none(page, "xpath=//*[contains(@class, 'product-price__big')]")

        item_code = get_text_or_none(page, "xpath=//*[@class='desktop']//div[@class='rating text-base']//span")
        product['item_code'] = ''.join(filter(str.isdigit, item_code))

        images = []
        for img in page.locator("xpath=//div[@class='product-about__left']//img[contains(@src, 'goods/images')]").all():
            src = img.get_attribute("src")
            if src:
                images.append(src.split(' ')[0])
        product['item_photos'] = images

        product['serial'] = re.search(r"\(([\w\-\/]+)\)", product['title']).group(1)

        about_section = page.locator("xpath=//*[contains(@class, 'product-about__sticky')]").first
        if about_section.count() > 0:
            display_element = about_section.locator("xpath=.//*[contains(@class, 'mt-4')]").first
            display_text = display_element.inner_text() if display_element.count() > 0 else None
            if display_text:
                product['display_res'] = re.search(r"\b(\d+x\d+)\b", display_text).group(1)


        page.goto('https://rozetka.com.ua/ua/apple-iphone-15-128gb-black/p395460480/characteristics/')

        specs = {}

        page.wait_for_selector("xpath=//main[contains(@class, 'product-tabs__content')]", timeout=30000)

        items = page.locator("xpath=//main[contains(@class, 'product-tabs__content')]//*[contains(@class, 'item')]").all()

        for item in items:
            title_element = item.locator("xpath=.//*[contains(@class, 'label')]//span").first
            value_element = item.locator("xpath=.//*[contains(@class, 'value')]").first

            if title_element.count() > 0 and value_element.count() > 0:
                title = title_element.inner_text() if title_element.count() else None
                value = value_element.inner_text() if value_element.count() else None
                specs[title] = value

        product['item_spec'] = specs



        for key, value in product.items():
            print(f'{key}: {value}')

        # експорт в xlsx
        save_to_excel(product)

        # експорт .json (для теста/себя)
        save_to_json(product)

    except Exception as e:
        print(f"error: {e}")
        page.screenshot(path="result/images/error_final.png")



    finally:
        browser.close()
