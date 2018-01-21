import scrapy
from scrapy.selector import Selector
from scraper6.items import TopshopItem
import hashlib
import re
import requests
import json


class TopshopSpider(scrapy.Spider):
    name = "topshop_spider"

    # The main start function which initializes the scraping URLs and triggers parse function
    def start_requests(self):
        urls = [
            'http://www.topshop.com/en/tsuk/?geoip=home'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.link_collection)


    # Go through the top menu in initial response to collect links of each category
    def link_collection(self, response):
        links = Selector(response).xpath('.//ul[@id = "nav_catalog_menu"]/li')

        for link in links:
            cat_urls = link.xpath('.//div[contains(@class, "dropdown")]/ul/li//a/@href').extract()
            for cat_url in cat_urls:
                print('Category URL: ' + cat_url)
                yield scrapy.Request(url=cat_url, callback=self.infinite_request)


    # Topshop has infinite scrolling, so we need to simulate ajax call to server requesting product data for scrolling
    # From ajax response then extract each product URL and trigger a scraping request
    def infinite_request(self, response):
        ajax_url_1 = 'http://www.topshop.com/webapp/wcs/stores/servlet/CatalogNavigationAjaxSearchResultCmd'

        STORE_ID_SELECTOR = './/li[@id = "header_welcome"]/a/@href'
        store_id = str(response.xpath(STORE_ID_SELECTOR).re('storeId=[0-9]{5}')[0])
        print('store id: ' + store_id)
        catalog_id = str(response.xpath(STORE_ID_SELECTOR).re('catalogId=[0-9]{5}')[0])
        print('catalog id: ' + catalog_id)

        ajax_url_2 = '?' + store_id + '&' + catalog_id + '&langId=-1&dimSelected='

        CATEGORY_NAME_SELECTOR = './/select[@name = "sort-field"]/option[@selected = "selected"]/@value'
        category_name = response.xpath(CATEGORY_NAME_SELECTOR).extract_first()

        # Some matches will not have any products on them as outdated links
        if isinstance(category_name, str):
            ajax_url_3 = category_name[0:-45]

            print('category name: ' + ajax_url_3)

            CATEGORY_ID_SELECTOR = './/p[@class = "selected_filter_label"]/a/@href'
            category_id = str(response.xpath(CATEGORY_ID_SELECTOR).re('categoryId=[0-9]{6}')[0])
            print('category id: ' + category_id)

            ajax_url_4 = '?No=0&Nrpp=20&siteId=/' + store_id[8:] + '&' + category_id

            ajax_url = ajax_url_1 + ajax_url_2 + ajax_url_3 + ajax_url_4
            print('AJAX call URL: ' + ajax_url)

            ajax_req = requests.get(ajax_url)
            json_dict = json.loads(ajax_req.text)
            results = json_dict['results']
            contents = results['contents'][0]
            total_nr_recs = contents['totalNumRecs']
            loop_count = int(total_nr_recs / 20) + 1

            # Iterate through pagination of requests/responses
            i = 0
            while i < loop_count:
                i += 1
                ajax_url_pag = ajax_url_1 + ajax_url_2 + ajax_url_3 + '?No=' + str(i * 20) + '&Nrpp=20&siteId=/' + store_id[8:] + '&' + category_id
                ajax_req = requests.get(ajax_url_pag)
                json_dict = json.loads(ajax_req.text)
                results = json_dict['results']
                contents = results['contents'][0]
                records = contents['records']

                for record in records:
                    product_url = 'http://www.topshop.com' + record['productUrl']
                    print('Product URL: ' + product_url)
                    yield scrapy.Request(url=product_url, callback=self.parse)


    def parse(self, response):

        # Write out xpath and css selectors for all fields to be retrieved
        item = TopshopItem()
        NAME_SELECTOR = './/div[contains(@class, "product_details")]/h1/text()'
        PRICE_SELECTOR = 'normalize-space(.//span[@class = "product_price"]/text())'
        IMAGE_SELECTOR = './/ul[contains(@class, "product_hero__wrapper")]/li/a/img/@src'
        SALE_WASPRICE_SELECTOR = './/div[@class = "product_prices"]/span[1]/text()'
        SALE_PRICE_SELECTOR = './/div[@class = "product_prices"]/span[3]/text()'

        # Assemble the item object which will be passed then to pipeline
        item['shop'] = 'Top Shop'
        item['name'] = response.xpath(NAME_SELECTOR).extract_first()
        item['price'] = [(response.xpath(PRICE_SELECTOR).extract_first()).lstrip("£")]

        if item['price'] == ['']:
            item['price'] = (response.xpath(SALE_WASPRICE_SELECTOR)).re('[.0-9]+')

        item['prod_url'] = response.url
        item['image_urls'] = response.xpath(IMAGE_SELECTOR).extract()
        item['saleprice'] = (response.xpath(SALE_PRICE_SELECTOR)).re('[.0-9]+')

        # Check if page is sales or not, add boolean value of result
        m = re.search('sale', response.url)

        if m:
            item['sale'] = True
        else:
            item['sale'] = False

        # Top Shop has only women fashion
        item['sex'] = 'women'

        # Calculate SHA1 hash of image URL to make it easy to find the image based on hash entry and vice versa
        # Add the hash to item
        img_strings = item['image_urls']

        item['image_hash'] = []

        for img_string in img_strings:
            # Check if image string is a string, if not then do not pass this item
            if isinstance(img_string, str):
                # print(img_string)
                hash_object = hashlib.sha1(img_string.encode('utf8'))
                hex_dig = hash_object.hexdigest()
                item['image_hash'].append(hex_dig)

        yield item
