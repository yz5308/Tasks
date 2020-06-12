# -*- coding: utf-8 -*-


# This Pipeline processes several items scraped.
class EtsyPipeline(object):
    def process_item(self, item, spider):
        
        # Format the price output
        if 'price' in item:
            # Check if there is a currency symbol
            if len(item['price'].split()) > 1:
                # Remove the currency symbol and the + signal
                item['price'] = item['price'].split()[1].replace('+','')
            else:
                # Remove the currency symbol and the + signal
                item['price'] = item['price'].replace('+','').replace('$','')


        if 'store_sales' in item:
            item['store_sales'] = item['store_sales'].replace(' sales', '')


        # Sometimes the spider take the rate in the wrong format (ex: 48.333 instead of 4.8333)
        if 'rating' in item:
            rating = item['rating']
            if float(rating) > 5:
                # Ex: Transform this 48.333 in 4.83)
                rating = rating[0] + '.' + rating[1:2]
            else:
                rating = round(float(rating), 2)

            item['rating'] = rating
        
        return item
