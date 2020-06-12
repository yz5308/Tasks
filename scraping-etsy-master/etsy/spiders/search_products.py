# -*- coding: utf-8 -*-


import scrapy
import os
import sys
import csv
import glob
from openpyxl import Workbook
from etsy.items import ProductItem
from scrapy.loader import ItemLoader

# Spider Class
class ProductsSpider(scrapy.Spider):
    # Spider name
    name = 'search_products'
    allowed_domains = ['etsy.com']
    start_urls = ['https://www.etsy.com/']

    # Max number of items
    COUNT_MAX = 10 ** 100
    # Count the number of items scraped
    COUNTER = 0
    reviews_opt = None

    def __init__(self, search, reviews_option=1, count_max=None, *args, **kwargs):

        if search:
            # Build the search URL
            self.start_urls = ['https://www.etsy.com/search?q={}&ref=pagination&page=1'.format(search)]

            # Set the maximum number of items to be scraped
            if count_max:
                self.COUNT_MAX = int(count_max)

            # Set the chosen review option
            self.reviews_opt = int(reviews_option)

        super(ProductsSpider, self).__init__(*args, **kwargs)

    # Parse the first page result and go to the next page
    def parse(self, response):

       # Get the list of products from html response
        products_list = response.xpath('//li[contains(@class, "wt-list-unstyled wt-grid__item-xs-6")]')

        # Stops if there is no product to scrape
        if len(products_list) == 0 :
            raise scrapy.CloseSpider(reason='All products scraped - {} items'.format(self.COUNTER))

        # For each product extracts the product URL
        for product in products_list:
            product_id = product.xpath(".//div/@data-palette-listing-id").extract_first()
            product_url = 'https://www.etsy.com/listing/{}'.format(product_id)


            # Stops if the COUNTER reaches the maximum set value
            if self.COUNTER < self.COUNT_MAX:
                # Go to the product's page to get the data
                yield scrapy.Request(product_url, callback=self.parse_product)

        for product in products_list:
            product_id = product.xpath("./div/@data-search-lazy-listing-id").extract_first()
            product_url = 'https://www.etsy.com/listing/{}'.format(product_id)

            if self.COUNTER < self.COUNT_MAX:
                # Go to the product's page to get the data
                yield scrapy.Request(product_url, callback=self.parse_product)



        # Pagination - Go to the next page
        current_page_number = int(response.url.split('=')[-1])
        next_page_number = current_page_number + 1
        # Build the next page URL
        next_page_url = '='.join(response.url.split('=')[:-1]) + '=' + str(next_page_number)
        yield scrapy.Request(next_page_url)


    # Get the HTML from product's page and get the data
    def parse_product(self, response):

        # Stops if the COUNTER reaches the maximum set value
        if self.COUNTER >= self.COUNT_MAX:
            raise scrapy.CloseSpider(reason='COUNT_MAX value reached - {} items'.format(self.COUNT_MAX))

        # Check if the product is available
        no_available_message = response.xpath('//h2[contains(text(), "Darn")]')
        if no_available_message:
            return []

        # Create the ItemLoader object that stores each product information
        l = ItemLoader(item=ProductItem(), response=response)

        # Get the product ID (ex: 666125766)
        product_id = response.url.split('/')[4]
        l.add_value('product_id', product_id)

        # Get the product Title
        l.add_xpath('title', '//meta[@property="og:title"]/@content')
        #l.add_xpath('title', "//h1[@data-listing-id='{}']".format(response.url.split('/')[4]))
        
        # Get the product price        
        l.add_xpath('price', '//*[contains(@class,"wt-text-title-03 wt-mr-xs-2")]/text()')

        # Get the product URL (ex: www.etsy.com/listing/666125766)
        l.add_value('url', '/'.join(response.url.split('/')[2:5]))

        # Get the product rating (ex: 4.8 )
        l.add_xpath('rating', '//a[@href="#reviews"]//input[@name="rating"]/@value')

        # Get the number of people that add the product in favorites
        l.add_xpath('favorited_by', '//a[contains(text(), " favorites")]/text()', re='(\d+)')

        # Get the number of votes (number of reviews)
        l.add_xpath('Num_reviews_for_product', '//*[contains(@class,"wt-badge wt-badge--status-02 wt-ml-xs-2")]/text()')

        # Count the store sales
        l.add_xpath('store_sales', '//a[@href="#shop_overview"]//span/text()')

        # Get the shop url
        l.add_xpath('store_url', '//meta[@property="etsymarketplace:shop"]/@content')
                
        # Get the name of the Store
        l.add_xpath('store_name', '//*[contains(@class,"wt-text-body-01 wt-mr-xs-1")]')

        # Get the number of store reviews (number of reviews)
        l.add_xpath('Num_reviews_for_store', '//*[contains(@class,"wt-badge wt-badge--status-02 wt-ml-xs-2 wt-nowrap")]/text()')

        # Get reviews date
        date = response.xpath('//a[@class= "wt-text-link wt-mr-xs-1"]/parent::*//text()').extract()
        l.add_value('reviews', date)

        # Use the chosen method to get the reviews
        self.logger.info('Reviews scraping option: ' + str(self.reviews_opt))
        # Increment the items counter
        self.COUNTER += 1
        print('\nProducts scraped: {}\n'.format(self.COUNTER))

        yield l.load_item()




    # Create the Excel file
    def close(self, reason):

        # Check if there is a CSV file in arguments
        csv_found = False
        for arg in sys.argv:
            if '.csv' in arg:
                csv_found = True

        if csv_found:
            self.logger.info('Creating Excel file')
            #  Get the last csv file created
            csv_file = max(glob.iglob('*.csv'), key=os.path.getctime)

            wb = Workbook()
            ws = wb.active

            with open(csv_file, 'r', encoding='utf-8') as f:
                for row in csv.reader(f):
                    # Check if the row is not empty
                    if row:
                        ws.append(row)
            # Saves the file
            wb.save(csv_file.replace('.csv', '') + '.xlsx')
