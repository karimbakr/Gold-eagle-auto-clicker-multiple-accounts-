import time
import asyncio
import aiohttp
import json
import random

count = int(input("Your energy: "))
REQUEST_LIMIT = 67  # الحد الأقصى للطلبات قبل التوقف
PAUSE_DURATION = 10 * 60  # مدة التوقف بالثواني (10 دقائق)

def get_current_timestamp():
    """Retrieve the current timestamp."""
    return int(time.time())

def get_tokens_from_file(file_path):
    """Retrieve all tokens from an external file."""
    try:
        with open(file_path, 'r') as file:
            tokens = file.read().strip().splitlines()
            return tokens
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []

async def send_request(token):
    """Send an asynchronous HTTP POST request for a specific token."""
    url = "https://api-gw.geagle.online/tap"
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 12; K) Telegram-Android/11.2.3 (Nubia NX669J; Android 12; SDK 32; HIGH)",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Android\"",
        'authorization': f"Bearer {token}",
        'sec-ch-ua': "\"Android WebView\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        'sec-ch-ua-mobile': "?1",
        'origin': "https://telegram.geagle.online",
        'x-requested-with': "org.telegram.messenger",
        'sec-fetch-site': "same-site",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://telegram.geagle.online/",
        'accept-language': "en,en-US;q=0.9",
        'priority': "u=1, i"
    }

    request_count = 0

    async with aiohttp.ClientSession() as session:
        while True:
            if request_count >= REQUEST_LIMIT:
                print(f"Reached {REQUEST_LIMIT} requests. Pausing for {PAUSE_DURATION // 60} minutes...")
                await asyncio.sleep(PAUSE_DURATION)
                request_count = 0  # Reset the counter after the pause

            payload = {
                "available_taps": count,
                "count": 15,
                "timestamp": get_current_timestamp(),
                "salt": "e40d7aaa-5ba2-4d81-a384-c1b39a9ac6b3"
            }

            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        print(f"Response for token {token[:10]}...: {response_text}")
                    else:
                        print(f"Error: Received status code {response.status} for token {token[:10]}")

            except aiohttp.ClientError as e:
                print(f"Network error for token {token[:10]}: {e}. Retrying...")
                await asyncio.sleep(5)  # انتظار 5 ثوانٍ قبل المحاولة مجددًا
                continue
            except Exception as e:
                print(f"Unexpected error for token {token[:10]}: {e}. Retrying...")
                await asyncio.sleep(5)  # انتظار 5 ثوانٍ قبل المحاولة مجددًا
                continue

            request_count += 1
            await asyncio.sleep(random.uniform(10, 15))  # انتظار بين الطلبات

async def main():
    """Main function to handle sending requests for all tokens."""
    tokens = get_tokens_from_file("data.txt")

    if not tokens:
        print("No tokens found. Exiting...")
        return

    tasks = [send_request(token) for token in tokens]
    await asyncio.gather(*tasks)

# Run the main asynchronous function
asyncio.run(main())