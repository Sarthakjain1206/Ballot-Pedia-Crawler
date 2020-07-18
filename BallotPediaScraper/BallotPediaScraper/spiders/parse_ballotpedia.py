import scrapy
from scrapy.http import Request
from BallotPediaScraper.items import BallotpediascraperItem
import re
class ParseBallotpediaSpider(scrapy.Spider):
    name = 'parse_ballotpedia'
    allowed_domains = ['ballotpedia.org']
    start_urls = ['https://ballotpedia.org/United_States_Congress_elections,_2020']

    def parse(self, response):
        table = response.xpath('//*[@id="mw-content-text"]/table[20]')
        rows = table.xpath(".//tr")[2:]
        for row in rows:
            columns = row.xpath(".//td")
            url = columns[0].xpath(".//@href").extract_first()
            state = columns[0].xpath(".//text()").extract_first()
            abs_url = "https://ballotpedia.org" + url

            item = BallotpediascraperItem()
            item['state'] = state

            request1 = Request(abs_url, callback=self.parse_page)
            request1.meta['item'] = item
            yield request1

    def parse_page(self, response):
        rows = response.xpath("//table[@id='offices']//tr")
        url = rows[2].xpath(".//td//@href").extract_first()
        office = rows[2].xpath(".//td//text()").extract_first()

        item = response.meta['item']

        item['office'] = office

        abs_url = "https://ballotpedia.org" + url
        request2 = Request(abs_url, callback=self.parse_us_home_election_page)
        request2.meta['item'] = item
        yield request2

    def parse_us_home_election_page(self, response):
        lists = response.xpath("//*[contains(text(), '\xa0Democratic primary candidates')]")
        for lst in lists:
            sub_lists = lst.xpath(".//following::ul")
            # profile_urls = sublists[0].xpath(".//li//@href").extract()
            #
            item = response.meta['item']
            # for urls in profile_urls:
            #     request3 = Request(urls, callback=self.parse_profile)
            #     request3.meta['item'] = item
            #     yield request3
            temp_lists = sub_lists[0].xpath(".//li")

            for i in temp_lists:
                temp = i.xpath(".//span")
                if temp:
                    link = i.xpath(".//@href").extract_first()
                    request3 = Request(link, callback=self.parse_profile)
                    request3.meta['item'] = item
                    yield request3
                else:
                    continue


    def parse_profile(self, response):
        name = response.xpath("//h1[@id='firstHeading']/span/text()").extract_first()
        list_of_profiles = response.xpath("//div[@class='widget-row value-only white']")[1:]
        dictionary_data = {
            'Campaign website': '',
            'Campaign Facebook': '',
            'Campaign Twitter': '',
            'Personal Facebook': '',
            'Personal Twitter': '',
        }
        allowed_profiles = ['Campaign website', 'Campaign Facebook', 'Campaign Twitter', 'Personal Facebook',
                            'Personal Twitter', 'Official Twitter', 'Official Facebook']

        for lst in list_of_profiles:
            key = lst.xpath(".//p/a/text()").extract_first()
            if key == 'Official Twitter':
                key = 'Personal Twitter'
            elif key == 'Official Facebook':
                key = "Personal Facebook"
            value = lst.xpath(".//p//@href").extract_first()
            if key in allowed_profiles:
                dictionary_data.update({
                    key: value
                })

        item = response.meta['item']
        state = item['state']
        office = item['office']

        # Extract email--
        email = ""
        clickable_email = ""
        email_selector = response.xpath("//*[contains(@alt,'Email')]")
        if email_selector:
            clickable_email = email_selector.xpath(".//ancestor::a/@href").extract_first()
            emails = re.findall(r"[a-zA-Z0-9\.\-+_]+@[a-zA-Z0-9\.\-+_]+\.[a-zA-Z]+", clickable_email)
            if emails:
                email = emails[0]


        yield {
            "Name": name,
            "Website": dictionary_data['Campaign website'],
            "Office": office,
            "State": state,
            "Campaign Facebook": dictionary_data['Campaign Facebook'],
            "Campaign Twitter": dictionary_data['Campaign Twitter'],
            "Personal Facebook": dictionary_data['Personal Facebook'],
            "Personal Twitter": dictionary_data['Personal Twitter'],
            "Email address": email,
            "Direct Mail": clickable_email
        }
