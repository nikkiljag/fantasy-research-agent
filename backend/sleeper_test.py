import requests

username = input("Enter your Sleeper username: ")

# Get Sleeper user
user_url = f"https://api.sleeper.app/v1/user/{username}"
user_response = requests.get(user_url)

if user_response.status_code != 200:
    print("Failed to retrieve Sleeper user.")
    raise SystemExit

user = user_response.json()

if user is None:
    print("Sleeper user not found.")
    raise SystemExit

user_id = user["user_id"]

print(f"\nFound user: {user['display_name']}")

# Get 2026 leagues
season = 2026
leagues_url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{season}"

leagues_response = requests.get(leagues_url)

if leagues_response.status_code != 200:
    print("Failed to retrieve leagues.")
    raise SystemExit

leagues = leagues_response.json()

print(f"\n2026 leagues found: {len(leagues)}")

for index, league in enumerate(leagues, start=1):
    print(f"\n{index}. {league['name']}")
    print(f"   League ID: {league['league_id']}")
    print(f"   Teams: {league['total_rosters']}")
    print(f"   Status: {league['status']}")