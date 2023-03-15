import json
import datetime
from models import Author, Quotes
import scrapy
from scrapy.crawler import CrawlerProcess


class AuthorsSpider(scrapy.Spider):
    name = 'authors'
    custom_settings = {"FEED_FORMAT": "json", "FEED_URI": "authors.json"}
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['http://quotes.toscrape.com/']

    def parse(self, response):
        for quote in response.xpath("/html//div[@class='quote']"):
            author_response = scrapy.Request(self.start_urls[0][:-1] + quote.xpath("span/a/@href").get())
            for author_page in author_response.response.xpath("/html//div[@class='author-details']"):
                print(author_page)
            #print()
            #yield {
            #    "keywords": quote.xpath("div[@class='tags']/a/text()").extract(),
            #    "author": quote.xpath("span/small/text()").extract(),
            #    "quote": quote.xpath("span[@class='text']/text()").get()
            #}


class QuotesSpider(scrapy.Spider):
    name = 'quotes'
    custom_settings = {"FEED_FORMAT": "json", "FEED_URI": "quotes.json"}
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['http://quotes.toscrape.com/']

    def parse(self, response):
        for quote in response.xpath("/html//div[@class='quote']"):
            yield {
                "keywords": quote.xpath("div[@class='tags']/a/text()").extract(),
                "author": quote.xpath("span/small/text()").extract(),
                "quote": quote.xpath("span[@class='text']/text()").get()
            }
        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link)

def load_json():
    with open('json-files/authors.json', 'r', encoding='utf-8') as fh:
        rez = json.load(fh)
        for itr in rez:
            new_author = Author()
            new_author.description = itr['description']
            new_author.born_date = datetime.strptime(itr['born_date'], '%B %d, %Y').date()
            new_author.born_location = itr['born_location']
            new_author.fullname = itr['fullname']
            new_author.save()

    with open('json-files/qoutes.json', 'r', encoding='utf-8') as fh:
        rez = json.load(fh)
        for itr in rez:
            authors = Author.objects(fullname=itr['author'])
            if len(authors) > 0:
                cur_author = [0]
            new_quote = Quotes(author=cur_author)
            new_quote.quote = itr['quote']
            new_quote.tags = itr['tags']
            new_quote.save()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(AuthorsSpider)
    process.start()

