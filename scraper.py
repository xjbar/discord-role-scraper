import aiohttp
import asyncio
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="Discord API token")
    parser.add_argument("--role", required=True, help="Discord Role id")
    parser.add_argument("--server", required=True, help="Discord Server id")
    parser.add_argument("--output", help="Output directory")
    return parser.parse_args()

async def scrape(session, before=None):
    params = {"limit": 1000}
    if before:
        params["before"] = before
    # API endpoint to get all members of a server
    url = f"https://discord.com/api/guilds/{SERVER_ID}/members"
    async with session.get(url, headers={
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }, params=params) as resp:
        if resp.status == 200:
            reset_time = int(resp.headers.get("X-Ratelimit-Reset"))
            now = int(time.time())
            wait_time = reset_time - now
            await asyncio.sleep(wait_time)
            data = await resp.json()
            return data
        elif resp.status == 429:
            reset_time = int(resp.headers.get("X-Ratelimit-Reset"))
            now = int(time.time())
            wait_time = reset_time - now
            print(f"Rate limit exceeded. Waiting {wait_time} seconds before retrying.")
            await asyncio.sleep(wait_time)
            return await scrape(session, before)
        else:
            raise ValueError(f"Failed to fetch members from server with id: {SERVER_ID}. Error code: {resp.status}")

if __name__ == "__main__":
    args = parse_args()
    TOKEN = args.token
    ROLE_ID = args.role
    SERVER_ID = args.server
    output_dir = args.output
    usernames = set()
    async with aiohttp.ClientSession() as session:
        has_more = True
        while has_more:
            try:
                data = await scrape(session)
                has_more = data["has_more"]
                for member in data["members"]:
                    if ROLE_ID in member["roles"]:
                        usernames.add(member["user"]["username"])
            except ValueError as e:
                print(e)
                continue
            except Exception as e:
                print(f"An error occurred while scraping: {e}")
                break

    if usernames:
        if output_dir:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            with open(os.path.join(output_dir, "usernames.txt"), "w") as file:
                for username in usernames:
                    file.write(username + "\n")
            print(f"Usernames were saved to {output_dir}/usernames.txt")
        else:
            with open("usernames.txt", "w") as file:
                for username in usernames:
                    file.write(username + "\n")
            print("Usernames were saved to the current directory.")
    else:
        print("No usernames found.")

