import time
import asyncio
import aiohttp
import json
import uuid
import secrets
from datetime import datetime
from colorama import Fore, Style, init
import random

# Initialize colorama
init(autoreset=True)

count = int(input("Your energy: "))
PAUSE_DURATION = 7 * 60
PAUSE = 2 * 60   # مدة التوقف بالثواني (10 دقائق)
TOTAL_LIMIT = 1000  # الحد الأقصى لمجموع الأرقام العشوائية قبل التوقف لكل توكن

# قاموس لتتبع المجموع لكل توكن
token_counts = {}
EDGE_USERAGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.57",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.52",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.46",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.128",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.112",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.98",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.83",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.133",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.121",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.91"
]

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

def print_response(acc_number, user_id, coins_amount, counts, total):
    """Print the extracted data with colors and timestamps."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        f"{Fore.GREEN}[{current_time}] {Fore.BLUE} Acc: [{acc_number}]:{Style.RESET_ALL} "
        f"User ID: {Fore.CYAN}[{user_id}]{Style.RESET_ALL}, Coins: {Fore.YELLOW}[{coins_amount}]{Style.RESET_ALL}, "
        f"Count: {Fore.MAGENTA}[{counts}]{Style.RESET_ALL}, Total Counts: {Fore.RED}[{total}]{Style.RESET_ALL}"
    )

async def send_request(token, acc_number):
    """Send an asynchronous HTTP POST request for a specific token."""
    global token_counts  # استخدم القاموس لتتبع مجموع كل توكن
    random_user_agent = random.choice(EDGE_USERAGENTS)
    url = "https://api-gw.geagle.online/tap"
    headers = {
        'User-Agent': random_user_agent,
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'authorization': f"Bearer {token}",
        'origin': "https://telegram.geagle.online",
        'accept-language': "en,en-US;q=0.9",
    }

    # تعيين المجموع الأولي للتوكن إذا لم يكن موجودًا
    if acc_number not in token_counts:
        token_counts[acc_number] = 0

    async with aiohttp.ClientSession() as session:
        while True:
            # تحقق إذا تجاوز المجموع للتوكن الحالي الحد الأقصى
            if token_counts[acc_number] >= TOTAL_LIMIT:
                print(f"{Fore.RED}Acc {acc_number} reached {TOTAL_LIMIT} total counts. Pausing for {PAUSE_DURATION // 60} minutes...")
                await asyncio.sleep(PAUSE_DURATION)
                token_counts[acc_number] = 0  # إعادة تعيين المجموع للتوكن الحالي

            salt = str(uuid.uuid4())
            counts = secrets.randbelow(41) + 50
            payload = {
                "available_taps": count,
                "count": counts,
                "timestamp": get_current_timestamp(),
                "salt": f"{salt}",
                "unique_id": str(uuid.uuid4())  # معرف مميز لكل طلب
            }

            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        data = json.loads(response_text)
                        user_id = data.get("user_id")
                        coins_amount = data.get("coins_amount")

                        # تحديث المجموع الخاص بالتوكن الحالي وطباعة النتيجة
                        token_counts[acc_number] += counts
                        print_response(acc_number, user_id, coins_amount, counts, token_counts[acc_number])
                    else:
                        print(f"{Fore.RED}Error: Received status code {response.status} for token {token[:10]}")

            except aiohttp.ClientError as e:
                print(f"{Fore.RED}Network error for acc {acc_number}: {e}. Retrying...")
                await asyncio.sleep(5)
                continue
            except Exception as e:
                print(f"{Fore.RED}Unexpected error for acc {acc_number}: {e}. Retrying...")
                await asyncio.sleep(5)
                continue

            if token_counts[acc_number] % 10 == 0:  # غير الـ User-Agent بعد كل 10 طلبات
                random_user_agent = random.choice(EDGE_USERAGENTS)
                headers['User-Agent'] = random_user_agent

            if token_counts[acc_number] % 50 == 0:  # التوقف بعد كل 50 طلب
                print(f"{Fore.YELLOW}Taking a longer pause for token anti detect 👾👽{acc_number}...")
                await asyncio.sleep(PAUSE * 2)

            random_delay = secrets.randbelow(11) + 15  # رقم عشوائي بين 20 و 40
            #additional_delay = secrets.randbelow(1)  # تأخير إضافي عشوائي بين 0 و 5 ثوانٍ
            await asyncio.sleep(random_delay)

async def main():
    """Main function to handle sending requests for all tokens."""
    tokens = get_tokens_from_file("data.txt")

    if not tokens:
        print("No tokens found. Exiting...")
        return

    tasks = [send_request(token, idx + 1) for idx, token in enumerate(tokens)]
    await asyncio.gather(*tasks)

# Run the main asynchronous function
asyncio.run(main())
