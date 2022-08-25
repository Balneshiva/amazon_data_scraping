import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import json
from datetime import datetime

from amazon_config import (
    get_web_driver_options,
    get_chrome_web_driver,
    set_ignore_certificate_error,
    set_browser_as_incognito,
    set_automation_as_head_less,
    NAME,
    CURRENCY,
    FILTERS,
    BASE_URL,
    DIRECTORY
)
class GenerateReport:
    def __init__(self,file_name,filters,base_link,currency,data) -> None:
        self.data = data
        self.file_name = file_name
        self.filters = filters
        self.base_link = base_link
        self.currency = currency
        report = {
            'title': self.file_name,
            'date': self.get_now(),
            'best_item': self.get_best_item(),
            'currency':self.currency,
            'filters':self.filters,
            'base_link':self.base_link,
            'products':self.data
        }
        print("Creating report....")
        with open(f'{DIRECTORY}/{file_name}.json','w') as f:
            json.dump(report,f)
        print("done....")

    @staticmethod
    def get_now():
        now = datetime.now()
        return now.strftime("%d/%m/Y %H:%M:%S")

    def get_best_item(self):
        try:
            return sorted(self.data,key=lambda k:k['price'])[0]
        except Exception as e:
            print(e)
            print("problem with sorting items")
            return None




class AmazonAPI:
    def __init__(self, search_term, filters, base_url, currency):
        self.base_url = base_url
        self.search_term = search_term
        options = get_web_driver_options()
        # set_automation_as_head_less(options)
        set_ignore_certificate_error(options)
        set_browser_as_incognito(options)
        self.driver = get_chrome_web_driver(options)
        self.currency = currency
        self.price_filter = f"&rh=p_36%3A{filters['min']}00-{filters['max']}00"

    def run(self):
        print("Starting Script...")
        print(f"Looking for {self.search_term} products...")
        links = self.get_products_links()   #gets all the product links and stores in this variable
        #time.sleep(1)
        if not links:
            print("Stopped script. ")
            return
        print(f"Got {len(links)} links to products...")
        print("getting info about products...")
        products = self.get_products_info(links) 
        print(f"got info about {len(products)} products...")
        self.driver.quit()
        return products
    
    def get_products_links(self):
        self.driver.get(self.base_url)
        element = self.driver.find_element(By.ID,'twotabsearchtextbox')
        element.send_keys(self.search_term)
        element.send_keys(Keys.ENTER)
        time.sleep(2)  #waits to load page
        self.driver.get(f'{self.driver.current_url}{self.price_filter}')
        print(f"Our url: {self.driver.current_url}")
        time.sleep(2) # wait to load page
        result_list = self.driver.find_element(By.CLASS_NAME,'s-result-list') #returns the list of all result items 
        links = []  #empty array to store 
        try:
            results = result_list.find_elements(By.XPATH, "//a[@class = 'a-link-normal s-no-outline']")
            links = [link.get_attribute('href') for link in results]  #iterating through each results and extract the link of each item
            #print(links)
            return links
        except Exception as e:
            print("Didn't get any products...")
            print(e)
            return links

    def get_products_info(self,links):
        asins = self.get_asins(links)
        products = []
        for asin in asins:
            product = self.get_single_product_info(asin)
            if product:
                products.append(product)
        return products    


    def get_single_product_info(self,asin):
        print(f"product ID: {asin} - getting data...")
        product_short_url = self.shorten_url(asin)
        self.driver.get(f"{product_short_url}?language=en_GB")
        time.sleep(2)
        title = self.get_title()
        seller = self.get_seller()
        price = self.get_price()
        if title and seller and price:
            product_info = {
                'asin': asin,
                'url': product_short_url,
                'title':title,
                'seller':seller,
                'price':price
            }
            return product_info
        return None

    def get_title(self):
        try:
            #temp =    #find_elements(By.XPATH, "//span[@id = 'productTitle']")
            return self.driver.find_element(By.CLASS_NAME,'a-size-large product-title-word-break')[0].text  #find_element(By.ID,'productTitle').text 
        except Exception as e:
            print(e)
            print(f"can't get the title of the product - {self.driver.current_url}")
            return None
    def get_seller(self):
        try:
            #temp = 
            return self.driver.find_elements(By.XPATH, "//a[@id = 'bylineInfo']").text  #temp[0].text #find_element(By.ID,'bylineInfo').text
        except Exception as e:
            print(e)
            print(f"can't get the price of the product - {self.driver.current}")
            return None
    def get_price(self):
        price = None
        try:
            price = self.driver.find_element(By.ID,'priceblockprice_ourprice').text
            #price = price[0].text
            price = self.convert_price(price)
        except NoSuchElementException:
            try:
                availability = self.driver.find_element(By.ID,'availability').text
                #availability = availability[0].text
                if 'Available' in availability:
                    price = self.driver.find_element(By.CLASS_NAME,'olp-padding-right').text
                    #price = price[0].text
                    price = price[price.find(self.currency):]
                    price = self.convert_price(price)
            except Exception as e:
                print(e)
                print(f"can't get the price of a product - {self.driver.current_url}")
                return None
        except Exception as e:
            print(e)
            print(f"can't get the price of a product - {self.driver.current_url}")
            return None
        return price
    @staticmethod
    def convert_price(self,price):
        price = price.split(self.currencr)[1]
        try:
            price = price.split("\n")[0]+"."+price.split("\n")[1]
        except:
            Exception()
        try:
            price = price.split(",")[0]+price.split(",")[1]
        except:
            Exception()
        return float(price)

    def shorten_url(self, asin):
        return self.base_url + asin

    def get_asins(self,links):
        return [self.get_asin(link) for link in links]  #iterate through the links

    def get_asin(self,product_link):
        return product_link[product_link.find('/dp/'):product_link.find('/ref')]  # returns the id of the 

if __name__ == '__main__':
    amazon = AmazonAPI(NAME, FILTERS, BASE_URL, CURRENCY)
    data = amazon.run()
    print(data)
    GenerateReport(NAME, FILTERS, BASE_URL, CURRENCY, data)
