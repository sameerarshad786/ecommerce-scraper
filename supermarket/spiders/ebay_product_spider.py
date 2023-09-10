import scrapy

from urllib.request import urlopen
from decimal import Decimal

from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request
from lxml import html

from supermarket.items import ProductsItem


class EbayProductsSpider(scrapy.Spider):
    name = "ebay"
    url = "https://www.ebay.com/"

    def start_requests(self):
        yield Request(
            self.url,
            callback=self.parse
        )

    def parse(self, response, **kwargs):
        electronic_section = LinkExtractor(
            tags="a", attrs="href", restrict_text="Electronics"
        )
        _data = {}
        for data in electronic_section.extract_links(response):
            _data["url"] = data.url
            _data["type"] = data.text
        kwargs = {
            "icon": response.xpath("//link[@rel='icon']/@href").get(),
            "type": _data["type"]
        }
        yield Request(_data["url"], callback=self.parse_electronics, meta=kwargs)

    def parse_electronics(self, response, **kwargs):
        a_elements = response.xpath("//section/div/a[div[contains(text(), 'Cell Phones, Smart Watches & Accessories')]]/@href").get()
        yield Request(a_elements, callback=self.parse_brands_products, meta=response.meta)

    def parse_brands_products(self, response, **kwargs):
        brand_urls = response.xpath("//section/div/a[@class='b-visualnav__tile b-visualnav__tile__default']/@href")[10:].getall()
        brand_names = response.xpath("//a/div[@class='b-visualnav__title']/text()")[10:].getall()

        for brand_url, brand_name in zip(brand_urls, brand_names):
            url = urlopen(brand_url)
            page = html.fromstring(url.read(), "lxml")
            products = page.xpath("//li/div[@class='s-item__wrapper clearfix']")
            for product in products:
                url = self.parse_url(product)
                name = self.parse_name(product)
                price = self.parse_price(product)
                original_price = self.parse_original_price(product)
                image = self.parse_image(product)
                items_sold = self.parse_items_sold(product)
                shipping_charges = self.parse_shipping_charges(product)
                ratings = self.parse_ratings(product)
                discount = self.calulate_discount(product)
                product_type = response.meta.get("type")

                item = ProductsItem()
                item["name"] = name
                item["description"] = ""
                item["brand"] = brand_name.split(" ")[0].lower()
                item["url"] = url
                item["price"] = price
                item["source"] = "ebay"
                item["image"] = image
                item["original_price"] = original_price
                item["items_sold"] = items_sold
                item["shipping_charges"] = shipping_charges
                item["ratings"] = ratings
                item["discount"] = discount
                item["condition"] = "used"
                item["type"] = product_type
                yield item

    def parse_name(self, product):
        name = product.xpath(".//a/h3[@class='s-item__title']/text() | .//a/h3[@class='s-item__title']/span/text()")
        filtered_name = list(filter(lambda x:x.lower() != "new listing", name))
        return filtered_name[0]

    def parse_url(self, product):
        return product.xpath(".//div/a[@class='s-item__link']/@href")[0]

    def parse_price(self, product):
        price = product.xpath(".//div/span[@class='s-item__price']/text()")
        return list(map(lambda x:x.replace('$', '').replace(",", ""), price))

    def parse_original_price(self, product):
        original_price = product.xpath(".//div/span[@class='s-item__trending-price']/span/text()")
        if  original_price:
            print(list(map(lambda x:x.replace("was", "").replace("$", ""), original_price)))
            if "was" in original_price[0].lower():
                return original_price[0].replace("$", "")
            else:
                return 0
        return 0.00

    def parse_image(self, product):
        image = product.xpath(".//div[@class='s-item__image-helper']/img[@class='s-item__image-img']")[0].attrib
        try:
            image = image["data-src"]
        except KeyError:
            image = image["src"]
        return image

    def parse_items_sold(self, product):
        sold = product.xpath(".//span[@class='s-item__hotness s-item__itemHotness']/span/text()")
        items_sold = 0
        if sold:
            items_sold = sold[0]
            if "sold" in items_sold:
                items_sold = int(items_sold.replace("sold", "").replace(",", ""))
            else:
                items_sold = 0
        return items_sold

    def parse_shipping_charges(self, product):
        shipping = product.xpath(".//div[@class='s-item__detail s-item__detail--primary']/span/text()")
        if shipping:
            return Decimal(shipping[0].replace("$", "").replace("shipping", "").replace(",", ""))
        else:
            return 0.00

    def parse_ratings(self, product):
        ratings = product.xpath(".//span[@class='b-rating__rating-count']/span/text()")
        if ratings:
            return Decimal(ratings[0].replace("(", "").replace(")", ""))
        else:
            return 0.00

    def calulate_discount(self, product):
        price = product.xpath(".//div/span[@class='s-item__price']/text()")
        if len(price) > 1:
            price = price[0].replace("$", "")
        original_price = product.xpath(".//div/span[@class='s-item__trending-price']/span/text()")
        if  original_price:
            if "was" in original_price[0].lower():
                original_price = original_price[0].replace("$", "")
                return ((original_price-price)/original_price)*100 if original_price != price else 0
        return 0
