#
#
#   This script removes (soft deletion) expired users who has 'lastActiveTime' && 'lastActiveCodeHostIntegrationTime' = 'never'  
#
#

import requests
import logging
from datetime import datetime, timedelta

# Vars
SOURCEGRAPH_URL = "YYY"
TOKEN = "XXX"
EXCLUDE_USERS = {"ZZZ"}  # users who will never be deleted
LOG_FILE = "/var/log/sourcegraph-delete-expired-users.log"
headers = {"Authorization": f"token {TOKEN}", "Content-Type": "application/json"}

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Write to file
        logging.StreamHandler()  # Stdout
    ]
)

#  Request list of current users
query_all_users = """query {
  users {
    nodes {
      id
      username
      usageStatistics {
        lastActiveTime
        lastActiveCodeHostIntegrationTime
      }
    }
  }
}"""

request_response = requests.post(
    f"{SOURCEGRAPH_URL}/.api/graphql",
    json={"query": query_all_users},
    headers=headers)

users = request_response.json().get("data", {}).get("users", {}).get("nodes", [])

# Looking for expired users
inactive_users = [
    user for user in users
    if user["usageStatistics"]["lastActiveTime"] is None
       and user["usageStatistics"]["lastActiveCodeHostIntegrationTime"] is None
       and user["username"] not in EXCLUDE_USERS
]

# Try to logging
if inactive_users:
    logging.info(
        f"Found out {len(inactive_users)} expired users to be deleted: {[user['username'] for user in inactive_users]}")
else:
    logging.info("No inactive users found out, terminating...")
    exit(0)

# Delete expired users
for user in inactive_users:
    user_id = user["id"]
    variables = {"user": user_id, "hard": False}

    delete_query = """
    mutation DeleteUser($user: ID!, $hard: Boolean) {
      deleteUser(user: $user, hard: $hard) {
        alwaysNil
      }
    }
    """

    delete_response = requests.post(
        f"{SOURCEGRAPH_URL}/.api/graphql",
        json={"query": delete_query, "variables": variables},
        headers=headers
    )

    if delete_response.status_code == 200:
        logging.info(f"User {user['username']} has been deleted")
    else:
        logging.error(f"Error occurred during deletion {user['username']}: {delete_response.text}")

logging.info("Job is done.")
