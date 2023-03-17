import json
import datetime
from models import Author, Quotes
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.item import Item, Field
from itemadapter import ItemAdapter


class QuoteItem(Item):
    keywords = Field()
    author = Field()
    quote = Field()


class AuthorItem(Item):
    fullname = Field()
    date_born = Field()
    location_born = Field()
    description = Field()


class Q_Pipline:
    quotes = []
    authors = []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if 'fullname' in adapter.keys():
            self.authors.append({
                "fullname": adapter["fullname"],
                "date_born": adapter["date_born"],
                "location_born": adapter["location_born"],
                "description": adapter["bio"],
            })
        if 'quote' in adapter.keys():
            self.quotes.append({
                "keywords": adapter["keywords"],
                "author": adapter["author"],
                "quote": adapter["quote"],
            })
        return

    def close_spider(self, spider):
        with open('quotes.json', 'w', encoding='utf-8') as fd:
            json.dump(self.quotes, fd, ensure_ascii=False)
        with open('authors.json', 'w', encoding='utf-8') as fd:
            json.dump(self.authors, fd, ensure_ascii=False)


class AuthorsSpider(scrapy.Spider):
    name = 'authors'
    custom_settings = {"ITEM_PIPELINES": {Q_Pipline: 100}}
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['http://quotes.toscrape.com/']

    def parse(self, response):
        for quote in response.xpath("/html//div[@class='quote']"):
            keywords = quote.xpath("div[@class='tags']/a/text()").extract()
            author = quote.xpath("span/small/text()").get().strip()
            quote_text = quote.xpath("span[@class='text']/text()").get().strip()
            yield QuoteItem(keywords=keywords, author=author, quote=quote_text)
            yield response.follow(url=self.start_urls[0] + quote.xpath('span/a/@href').get(),
                                  callback=self.parse_author)
        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link)


    def parse_author(self, response):
        author = response.xpath('/html//div[@class="author-details"]')
        fullname = author.xpath('h3[@class="author-title"]/text()').get().strip()
        date_born = author.xpath('p/span[@class="author-born-date"]/text()').get().strip()
        location_born = author.xpath('p/span[@class="author-born-location"]/text()').get().strip()
        bio = author.xpath('div[@class="author-description"]/text()').get().strip()
        yield AuthorItem(fullname=fullname, date_born=date_born, location_born=location_born, bio=bio)


def load_json():
    with open('authors.json', 'r', encoding='utf-8') as fh:
        rez = json.load(fh)
        for itr in rez:
            new_author = Author()
            new_author.description = itr['description']
            new_author.born_date = datetime.strptime(itr['born_date'], '%B %d, %Y').date()
            new_author.born_location = itr['born_location']
            new_author.fullname = itr['fullname']
            new_author.save()

    with open('quotes.json', 'r', encoding='utf-8') as fh:
        rez = json.load(fh)
        for itr in rez:
            authors = Author.objects(fullname=itr['author'])
            if len(authors) > 0:
                cur_author = [0]
            new_quote = Quotes(author=cur_author)
            new_quote.quote = itr['quote']
            new_quote.tags = itr['tags']
            new_quote.save()


if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(AuthorsSpider)
    process.start()
    #from 8 HW
    load_json()
