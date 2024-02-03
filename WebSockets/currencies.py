import platform
import aiohttp
import asyncio
from datetime import datetime, timedelta
import sys
import json


async def main(days_range):
    dates = [today - timedelta(days=i) for i in range(days_range)]
    tasks = [fetch_data(date) for date in dates]
    results = await asyncio.gather(*tasks)
    return results


async def fetch_data(date):
    date_str = date.strftime('%d.%m.%Y')
    url = f'https://api.privatbank.ua/p24api/exchange_rates?date={date_str}'
    main_response = {}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.text()
                data_json = json.loads(data)
                currencies_info = await get_currency_info(data_json['exchangeRate'], currencies_codes)
                main_response[data_json['date']] = currencies_info
                return main_response
    except aiohttp.ClientError as e:
        print(f"An error occurred during the request: {e}")
        return None


async def get_currency_info(rows: list, currencies_codes: list):
    response = {}
    for row in rows:
        for currency_code in currencies_codes:
            if row['currency'] == currency_code:
                response[row['currency']] = {'sale': row['saleRateNB'], 'purchase': row['purchaseRateNB']}
    return response


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    currencies_codes = ['USD', 'EUR']

    if len(sys.argv) == 1:
        days_range = 1
    elif len(sys.argv) == 2:
        days_range = int(sys.argv[1])
        if days_range > 10:
            days_range = 10

    today = datetime.today().date()
    r = asyncio.run(main(days_range))
    print(r)