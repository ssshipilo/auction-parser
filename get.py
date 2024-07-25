import asyncio
import aiohttp
import requests
from tqdm import tqdm
import json
import unicodedata
from bs4 import BeautifulSoup
from get_cookies import *
import re

cookies_dict = {}
cookies = get_cookies()
for item in cookies:
    try:
        cookies_dict[item['name']] = item['value']
    except:
        continue
cookies = cookies_dict
print(cookies)

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}

headers1 = {
    'Accept': 'application/json',
    'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Hemmings-Client': '1',
    'Hemmings-Secret': 'mN5mDUiaLCnULpNgpYzHIPCEpPlFVeoprsKP15fy',
    'Origin': 'https://www.hemmings.com',
    'Referer': 'https://www.hemmings.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

async def get_page(session, url, proxy, headers, cookies):
    while True:
        try:
            # Fetch the page using an HTTP GET request
            async with session.get(url, headers=headers, proxy=proxy, cookies=cookies) as r:
                if r.status == 200:
                    return await r.text()  # Return the page content
                else:
                    print(f"Failed to fetch data from {url}, status code: {r.status}")
        except Exception as e:
            pass

# Asynchronous function to get multiple web pages
async def get_all(session, urls, proxy, headers, cookies):
    tasks = []
    for url in urls:
        task = asyncio.create_task(get_page(session, url, proxy, headers, cookies))
        tasks.append(task)
    results = await asyncio.gather(*tasks)  # Gather results of all tasks
    return results

# Asynchronous function to get data from multiple URLs with a limit on connections
async def get_all_data_urls(urls, limit=20, proxy=None, headers=None, cookies=None):
    timeout = aiohttp.ClientTimeout(total=20)  # Set a timeout for requests
    connector = aiohttp.TCPConnector(limit=limit)  # Limit the number of simultaneous connections
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        data = await get_all(session, urls, proxy, headers, cookies)
        return data

def get_all_car_listings():
    result_list = []
    while True:
        try:
            response = requests.get('https://api.hemmings.com/v2/search/listings', headers=headers1, timeout=20)
            if response.status_code == 200:
                break
            else:
                print(response.status_code)
        except Exception as e:
            print(e)
    page_json = json.loads(response.text)
    last_page = page_json.get('total_count') // 30 + 1
    links = [
        f'https://api.hemmings.com/v2/search/listings?adtype=cars-for-sale&distance=50&page={index}&per_page=30&sort_by=recommended'
        for index in range(1, last_page+1)]
    data = asyncio.run(get_all_data_urls(links, 10, headers=headers1))
    for listing_data in data:
        listing_json = json.loads(listing_data)
        part_links = [item.get('url').replace('\\/', '/') for item in listing_json.get('results')]
        result_list.extend([link for link in part_links])

    print("[INFO] We got all the links 🔥")
    return result_list

async def parse_data(link_list: list, offset: int = 0, page_limit: int = 10, filename: str = 'final3'):
    total_links = len(link_list)
    if offset >= total_links:
        print("[ERROR] Offset is greater than the total number of links.")
        return

    if page_limit == 0:
        end_offset = total_links
    else:
        end_offset = min(offset + page_limit * 50, total_links)

    print(f"[INFO] Getting information from link {offset} to {end_offset} ...")

    temp_dict = []
    with open(f'{filename}.json', 'w', encoding='utf-8') as outfile:
        for part_index in tqdm(range(offset // 50, (end_offset + 49) // 50), desc="Processing Parts"):
            start_index = 50 * part_index
            end_index = min(50 * (part_index + 1), end_offset)

            part_data = await get_all_data_urls(link_list[start_index:end_index], 10, headers=headers, cookies=cookies)

            for page_data in part_data:
                text = unicodedata.normalize("NFKD", page_data.replace('\\/', '/'))
                soup = BeautifulSoup(text, 'lxml')
                if soup.find('classified-gallery'):
                    car_json = json.loads(soup.find('classified-gallery').get(':classified'))
                    temp_dict.append(car_json)

                    # with open('./car.json', 'w') as f:
                    #     f.write(json.dumps(my_json, indent=4))

                    # while True:
                    #     time.sleep(1)
                elif soup.find('script', id="auction-json"):
                    my_json = json.loads(soup.find('script', id="auction-json").text)

                    my_json['asking_price'] = extract_numbers(my_json['asking_price_in_dollars'])

                    # with open('./auction.json', 'w') as f:
                    #     f.write(json.dumps(my_json, indent=4))

                    # while True:
                    #     time.sleep(1)

                    temp_dict.append(my_json)
            json.dump(temp_dict, outfile, ensure_ascii=False, indent=4)
            outfile.flush()

    print(f"[INFO] Completed and saved to {filename}.json")

def extract_numbers(s):
    return re.sub(r'\D', '', s)

if __name__ == '__main__':
    links = get_all_car_listings()
    offset=0
    page_limit=0 # If the number is 0, then all pages
    asyncio.run(parse_data(links, offset=offset, page_limit=page_limit, filename="final3_all"))