from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor

from supermarket.spiders import DarazProductSpider, EbayProductsSpider


def run_spiders():
    configure_logging()

    settings = get_project_settings()
    settings.update({
        "TWISTED_REACTOR": "twisted.internet.epollreactor.EPollReactor"
    })
    runner = CrawlerRunner(settings=settings)
    runner.crawl(DarazProductSpider)
    runner.crawl(EbayProductsSpider)

    d = runner.join()
    d.addBoth(lambda _: reactor.stop())

    reactor.run()

run_spiders()
