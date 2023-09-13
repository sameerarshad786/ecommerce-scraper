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

    def get_brand(self, brand):
        if brand:
            brand_names = ["not defined", "apple", "samsung", "google", "lg", "huawei", "htc", "oneplus", "blackberry", "motorola", "nokia", "redmi", "oppo", "vivo", "itel", "infinix", "sony", "realme", "tecno", "xiaomi", "honor"]
            brand = brand.lower().split(" ")[0]
            brand = brand_names.index(brand)
            return brand_names[brand]
        else:
            return brand[0]
