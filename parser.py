import asyncio
import aiohttp
import random
import re
import settings
from bs4 import BeautifulSoup


class OlxParser:

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self._queue = asyncio.Queue()
        self._run_loop = True
        self._sess = None
        self._urls = []
        self.data = {}

    async def _sleep(self):
        sleep_time = random.randint(*settings.SLEEP_RANGE)
        await asyncio.sleep(sleep_time)

    async def get_soup(self, html):
        return BeautifulSoup(html, 'html.parser')

    async def get_ad_data(self, html):
        ad = {}
        soup = await self.get_soup(html)
        price_label = soup.find('div', {'class': 'price-label'})
        if price_label is not None:
            price = price_label.find('strong')
            price = re.sub(r'\D', '', price.get_text())
            if len(price) > 0:
                ad['price'] = int(price)
        bottom_bar = soup.find('div', {'id': 'offerbottombar'})
        ad['views'] = bottom_bar.find('strong').get_text()
        details = soup.find('table', {'class': 'details'})
        items = details.find_all('table', {'class': 'item'})
        for row in items:
            if row.find('th').get_text() == 'Марка планшета':
                ad['brand'] = row.find('a').get_text().strip()
                break
        return ad

    async def _consume(self):
        while True:
            url = await self._queue.get()
            url = url.replace(';promoted', '')
            html = None
            if url not in self._urls:
                self._urls.append(url)
                async with self._sess.get(url, headers={
                    'User-Agent': random.choice(settings.USER_AGENTS)
                }) as res:
                    if res.status == 200:
                        html = await res.text()
                        print('Fetching:', url)
            if html is not None:
                ad = await self.get_ad_data(html)
                if set(ad.keys()) >= {'brand', 'price'}:
                    if ad['brand'] not in self.data:
                        self.data[ad['brand']] = {
                            'prices': [],
                            'views': 0
                        }
                    self.data[ad['brand']]['prices'].append(ad['price'])
                    self.data[ad['brand']]['views'] += int(ad['views'])
                await self._sleep()
            self._queue.task_done()

    async def _produce(self, page_num):
        url = settings.URL
        if page_num > 1:
            url += '&page={}'.format(page_num)
        html = None
        async with self._sess.get(
                url,
                allow_redirects=False,
                headers={
                    'User-Agent': random.choice(settings.USER_AGENTS)
                }
        ) as res:
            if res.status == 200:
                html = await res.text()
                print('Fetching:', url)
            else:
                self._run_loop = False
        if html is not None:
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', {'id': 'offers_table'})
            links = table.find_all('a', {'class': 'detailsLink'})
            for link in links:
                await self._queue.put(link['href'])
        await self._sleep()

    async def run(self):
        consumer = asyncio.ensure_future(self._consume(), loop=self.loop)
        page_num = 1
        async with aiohttp.ClientSession(loop=self.loop) as sess:
            self._sess = sess
            while self._run_loop:
                await self._produce(page_num)
                page_num += 1
            await self._queue.join()
        consumer.cancel()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.loop.stop()
        return exc_type is None
