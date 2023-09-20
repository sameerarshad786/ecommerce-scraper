import re
import scrapy

from decimal import Decimal

from lxml import html
from scrapy.http import Request

from supermarket.items import ProductsItem


class AmazonProductSpider(scrapy.Spider):
    name = "amazon"
    domain = "https://www.amazon.com"
    start_urls = [f"{domain}/"]

    def parse(self, response, **kwargs):
        electronics_section = response.xpath("//div/div[contains(div/h2, 'Electronics')]/a").attrib.get("href")
        yield Request(
            url=f"{response.request.url}{electronics_section}",
            callback=self.parse_electronic
        )
    
    def parse_electronic(self, response, **kwargs):
        page = html.fromstring(response.text, "lxml")
        see_all_results = page.xpath("//a[@class='a-link-normal']")[0].get("href")
        full_url = f"{self.domain}{see_all_results}"
        yield Request(
            url=full_url,
            callback=self.parse_products,
            meta={"next": full_url}
        )

    def parse_products(self, response, **kwargs):
        page = html.fromstring(response.text, "lxml")
        products = page.xpath("//div[@class='a-section a-spacing-base']")

        for product in products:
            url = f"{self.domain}{self.parse_url(product)}"
            name = self.parse_name(product)
            price = self.parse_price(product)
            original_price = self.parse_original_price(product, price)
            items_sold = self.parse_items_sold(product)
            image = self.parse_image(product)
            ratings = self.parse_ratings(product)
            discount = self.calulate_discount(price, original_price)
            shipping_charges = 0

            item = ProductsItem()
            item["name"] = name
            item["description"] = ""
            item["brand"] = "not defined"
            item["url"] = url
            item["price"] = price
            item["source"] = "amazon"
            item["items_sold"] = items_sold
            item["shipping_charges"] = shipping_charges
            item["original_price"] = original_price
            item["image"] = image
            item["condition"] = "not defined"
            item["ratings"] = ratings
            item["discount"] = discount
            yield item

        if next := page.xpath("//a[contains(text(), 'Next')]/@href")[0]:
            full_url = f"{self.domain}{next}"
            yield Request(
                url=full_url,
                callback=self.parse_products,
                meta={"next": full_url, "Referer": response.request.url},
                cb_kwargs=kwargs
            )

    def parse_name(self, product):
        if name := product.xpath(".//img[@class='s-image']/@alt"):
            return name[0]
        elif name := product.xpath(".//a/div/h2/span/text()"):
            return name[0]
        else:
            return ""

    def parse_image(self, product):
        if image := product.xpath(".//img[@class='s-image']/@src"):
            return image[0]
        else:
            return ""

    def parse_url(self, product):
        url = product.xpath(".//a[@class='a-link-normal s-underline-text s-underline-link-text s-link-style']/@href")
        return url[0] if url else ""

    def parse_price(self, product):
        price_list = product.xpath(".//span[@class='a-offscreen']/text()")
        try:
            valid_price =  list(map(lambda x:re.sub(r"[^\d.]", "", x), price_list))
        except:
            price_list = product.xpath(".//span[@class='a-offscreen']/text()")
            price_exception = [price.extract() for price in price_list]
            valid_price =  list(map(lambda x:re.sub(r"[^\d.]", "", x), price_exception))

        return valid_price

    def parse_original_price(self, product, price):
        original_price = product.xpath(".//span[@class='a-price a-text-price']/span/text()")
        if original_price:
            valid_price =  list(map(lambda x:re.sub(r"[^\d.]", "", x), original_price))
            return Decimal(valid_price[0]) + Decimal(price[0])
        return 0

    def parse_items_sold(self, product):
        if item_sold := product.xpath("//span[@class='a-size-mini a-color-secondary']/text()"):
            sold = item_sold[0].split(" ")[0]
            if "k" in sold.lower():
                item_sold = sold.replace("k+", "000").replace("K+", "000")
            elif "m" in sold.lower():
                item_sold = sold.replace("m+", "000000").replace("M+", "000000")
            return item_sold
        return 0

    def parse_ratings(self, product):
        ratings = product.xpath(".//span/span[@class='a-size-mini puis-normal-weight-text']/text()")
        if ratings:
            return Decimal(re.sub(r"[^\d.]", "", ratings[0]))
        else:
            return 0.00

    def calulate_discount(self, price, original_price):
        if original_price:
            price = Decimal(price[0])
            return ((original_price-price)/original_price)*100
        return 0
