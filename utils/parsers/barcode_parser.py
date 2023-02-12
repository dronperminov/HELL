from typing import Optional

import requests
from bs4 import BeautifulSoup


class BarCodeParser:
    def parse(self, barcode: str) -> Optional[str]:
        try:
            url = f"https://barcodes.olegon.ru/?c={barcode}"
            response = requests.get(url, headers={
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'cache-control': 'max-age=0',
                'cookie': '_okhp=35b8941020e03869bdd87a9411856f84; _okuri=1674834691',
                'if-none-match': 'W/"460700299590501"',
                'referer': 'https://barcodes.olegon.ru/index.php?r=2f6bbdc26f4e5c3ef4520592ef9bacfe',
                'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Googlebot (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            })
        except requests.exceptions.ConnectionError:
            return None

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        print(soup)
        div = soup.find("div", {"itemprop": "acceptedAnswer"})

        if not div:
            return None

        title = div.text
        return title


if __name__ == '__main__':
    parser = BarCodeParser()
    barcodes = [
        "4607002995905",
        "4690363103799",
        "4690388111441",
        "4690228006906",
        "4870112003925"
    ]

    for code in barcodes:
        result = parser.parse(code)
        print(code, result)
