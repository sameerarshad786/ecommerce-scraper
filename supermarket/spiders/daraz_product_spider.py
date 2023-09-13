import os
import json
import scrapy

from decimal import Decimal

from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request

from supermarket.items import ProductsItem


class DarazProductSpider(scrapy.Spider):
    name = "daraz"
    start_urls = ["https://www.daraz.pk/"]

    def parse(self, response, **kwargs):
        brand_names = ["not defined", "apple", "samsung", "google", "lg", "huawei", "htc", "oneplus", "blackberry", "motorola", "nokia", "redmi", "xiaomi", "oppo", "vivo", "itel", "infinix", "sony", "realme", "tecno", "xiaomi", "honor"]
        categories = LinkExtractor(
            tags="a", attrs="href", restrict_xpaths="//a[@class='catLink']"
        ).extract_links(response)

        for category in categories:
            if category.text.strip().lower().split(" ")[0] in brand_names:
                brand_index = brand_names.index(category.text.strip().lower().split(" ")[0])
                brand = brand_names[brand_index]
                kwargs["type"] = "Electronics"
                kwargs["brand"] = brand
                yield Request(url=category.url, callback=self.parse_product_brands, cb_kwargs=kwargs)

    async def parse_product_brands(self, response, **kwargs):
        json_values = response.xpath("//script[contains(text(), 'window.pageData')]").get().replace("</script>", "")
        try:
            try_dump_data = json.loads(json_values.split("=", 1)[1])
        except json.JSONDecodeError:
            pass

        products = try_dump_data["mods"]["listItems"]
        for product in products:
            url = "https:" + product["productUrl"]
            name = product["name"]
            price = [Decimal(os.getenv("PKR_TO_DOLLAR_EXCHANGE_RATES")) * Decimal(product["price"])]
            original_price = self.parse_original_price(product, price[0])
            image = product["image"]
            items_sold = 0
            shipping_charges = Decimal(product["shipping_charges"]) if product.get("shipping_charges") else 0
            ratings = Decimal(product["ratingScore"]) if product.get("ratingScore") else 0
            discount = int(product["discount"].replace("%", "")) if product.get("discount") else 0
            product_type = kwargs["type"]

            item = ProductsItem()
            item["name"] = name
            item["description"] = ""
            item["brand"] = kwargs["brand"]
            item["url"] = url
            item["price"] = price
            item["source"] = "daraz"
            item["image"] = image
            item["original_price"] = original_price
            item["items_sold"] = items_sold
            item["shipping_charges"] = shipping_charges
            item["ratings"] = ratings
            item["discount"] = discount
            item["condition"] = "used"
            item["type"] = product_type
            yield item

    def parse_original_price(self, product, price):
        try:
            original_price = Decimal(os.getenv("PKR_TO_DOLLAR_EXCHANGE_RATES")) * int(product["originalPrice"])
        except:
            original_price = price
        return original_price
