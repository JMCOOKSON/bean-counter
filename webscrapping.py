from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import time
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, redirect, url_for, request, session

#Flask set up
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# driver set up
CHROME_DRIVER_LOCATION = "C:/Users/cooks/Documents/chromedriver.exe"
service = Service(CHROME_DRIVER_LOCATION)
driver = webdriver.Chrome(service=service)

#database setup
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vege_price.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class CountdownPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produce = db.Column(db.String(250), nullable=False)
    produce_formatted = db.Column(db.String(250), nullable=True)
    single_price = db.Column(db.Integer, nullable=True)
    per_kg_price = db.Column(db.Integer, nullable= True)


    def __repr__(self):
        return f'{self.produce},{self.price},{self.result_XPATH}'

with app.app_context():
    db.create_all()
    db.session.commit()

prices = []

def scrap_fruit():
    # driver.get("https://www.countdown.co.nz/shop/browse/fruit-veg/")
    driver.get('https://www.countdown.co.nz/shop/browse/fruit-veg/fresh-fruit')
    time.sleep(30)
    # element = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, "itemsperpage-dropdown-1")))
    # dropdown = Select(driver.find_element(By.NAME, "itemsperpage-dropdown-1"))
    # dropdown.select_by_visible_text("120")
    fruit = driver.find_elements(By.XPATH, '/html/body/wnz-content/div/wnz-search/div[1]/main/product-grid/cdx-card/product-stamp-grid/a')
    for product in fruit:
        single_unit_price = product.find_element(By.XPATH, './/product-price-single-unit-average//p[@class="price-single-unit-text"]')
        kg_dollar = str(product.find_element(By.TAG_NAME, 'em').text)
        kg_cents = str(product.find_element(By.CSS_SELECTOR, 'h3.presentPrice span').text)

            #concatinating the two strings together, splicing off the none number characters and then the dash
        per_kg_price_element = ((kg_dollar + kg_cents)[:3]).strip("/")

        prices.append({
            'name': product.find_element(By.TAG_NAME, 'h3').text,
            'single_unit_price': single_unit_price.text,
            'kg_price': per_kg_price_element
        })
# <div _ngcontent-app-c155="" class="dropdownList ng-star-inserted" dropdown-constrain-width="true"><select _ngcontent-app-c155="" name="itemsperpage-dropdown-1" id="itemsperpage-dropdown-1"><!----><option _ngcontent-app-c155="" value="24" selected="true" class="ng-star-inserted"> 24 </option><option _ngcontent-app-c155="" value="48" class="ng-star-inserted"> 48 </option><option _ngcontent-app-c155="" value="120" class="ng-star-inserted"> 120 </option><!----></select></div>
# <select _ngcontent-app-c155="" name="itemsperpage-dropdown-1" id="itemsperpage-dropdown-1"><!----><option _ngcontent-app-c155="" value="24" selected="true" class="ng-star-inserted"> 24 </option><option _ngcontent-app-c155="" value="48" class="ng-star-inserted"> 48 </option><option _ngcontent-app-c155="" value="120" class="ng-star-inserted"> 120 </option><!----></select>
def scrap_veges():
    driver.get('https://www.countdown.co.nz/shop/browse/fruit-veg/fresh-vegetables')
    # element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "itemsperpage-dropdown-1")))
    time.sleep(30)
    # dropdown = Select(driver.find_element(By.ID, "itemsperpage-dropdown-1"))
    # dropdown.select_by_visible_text("120")
    veges = driver.find_elements(By.XPATH,
                                 '/html/body/wnz-content/div/wnz-search/div[1]/main/product-grid/cdx-card/product-stamp-grid/a')
    for product in veges:
        single_unit_price = product.find_element(By.XPATH,
                                                 './/product-price-single-unit-average//p[@class="price-single-unit-text"]')
        kg_dollar = str(product.find_element(By.TAG_NAME, 'em').text)
        kg_cents = str(product.find_element(By.CSS_SELECTOR, 'h3.presentPrice span').text)

        # concatinating the two strings together, splicing off the none number characters and then the dash
        per_kg_price_element = ((kg_dollar + kg_cents)[:3]).strip("/")

        prices.append({
            'name': product.find_element(By.TAG_NAME, 'h3').text,
            'single_unit_price': single_unit_price.text,
            'kg_price': per_kg_price_element
        })
# with app.app_context():
#     produce = "Apples"
#     item = db.session.execute(db.select(CountdownPrice).filter_by(produce_formatted=produce)).scalar_one()
#     print(item.per_kg_price)
price_info_further = scrap_fruit()
price_info = scrap_veges()


with app.app_context():
    for product in prices:
        item = CountdownPrice.query.filter_by(produce= product['name']).first()
        if item:
            current_price = item.per_kg_price
            updated_price = product['kg_price']
            if updated_price != current_price:
                item.per_kg_price = updated_price

        else:
            new_product = CountdownPrice(produce=product['name'], single_price=product['single_unit_price'],
                                     per_kg_price=product['kg_price'])
            db.session.add(new_product)


        db.session.commit()

with app.app_context():
    items = CountdownPrice.query.all()
    for item in items:
        if item.produce.startswith("Value "):
            item.produce_formatted = item.produce.replace("Value Fresh Vegetable ", "")
        if item.produce.startswith("The Odd "):
            item.produce_formatted = item.produce.replace("The Odd Bunch Fresh Fruit ", "")
        if item.produce.startswith("Countdown "):
            item.produce_formatted = item.produce.replace("Countdown Fresh Tomatoes ", "")
        if item.produce.startswith("Countdown "):
            item.produce_formatted = item.produce.replace("Countdown Fresh Vegetable ", "")
        if item.produce.startswith("Meadow "):
            item.produce_formatted = item.produce.replace("Meadow Fresh Vegetable ", "")
        elif item.produce.startswith("Fresh Fruit "):
            item.produce_formatted = item.produce.replace("Fresh Fruit ", "")
        elif item.produce.startswith("Fresh Vegetable "):
            item.produce_formatted = item.produce.replace("Fresh Vegetable ", "")
        item.per_kg_price = (float(item.per_kg_price) * 0.01)

    db.session.commit()
# get_product_current_price()
"""To run once per week to update prices in db"""
# def get_product_current_price(harvested_item, XPATH):
#
#     driver.get("https://richmond.store.freshchoice.co.nz/")
#
#     #wait for page to load
#     time.sleep(5)
#     driver.find_element(By.ID, "q").send_keys(f"{harvested_item}" + Keys.ENTER)
#     time.sleep(10)
#     get_result = driver.find_element(By.XPATH, XPATH).text
#     product_price = float(get_result.strip("$"))
#     return product_price
# """To run once per week to update prices in db"""
# with app.app_context():
#     db.create_all()
#     db.session.commit()
#     """create list of all items in db, for each item find Xpath"""
#     result = db.session.execute(db.select(Price).order_by(Price.produce)).scalars()
#     for item in result:
#         print(f"{item.produce}")
#         price = get_product_current_price(harvested_item=item.produce,XPATH=item.result_XPATH)
#         print(price)
#         if item.produce == "tomato":
#             price_per_kg = 4 * price
#         else:
#             price_per_kg = price
#         """locate harvest item in database to modify price once it has been scrapped """
#         with app.app_context():
#             current_produce = db.session.execute(db.select(Price).filter_by(produce=item.produce)).scalar_one()
#             current_produce.price = price_per_kg
#             db.session.commit()

# what i used to get data from Fresh Choice website
# driver.get("https://richmond.store.freshchoice.co.nz/")
# driver.get("https://www.countdown.co.nz/shop/browse/fruit-veg")

# #wait for page to load
# time.sleep(5)
# driver.find_element(By.ID, "q").send_keys(f"{harvested_item}" + Keys.ENTER)
# time.sleep(10)
# get_result = driver.find_element(By.XPATH, XPATH).text
# product_price = float(get_result.strip("$"))
# return product_price