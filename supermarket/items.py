# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ProductsItem(scrapy.Item):
    name = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    brand = scrapy.Field()
    type = scrapy.Field()
    image = scrapy.Field()
    ratings = scrapy.Field()
    items_sold = scrapy.Field()
    condition = scrapy.Field()
    original_price = scrapy.Field()
    price = scrapy.Field()
    shipping_charges = scrapy.Field()
    source = scrapy.Field()
    discount = scrapy.Field()
