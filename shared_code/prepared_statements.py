

def read_linkedin_account_by_username_query(username: str):
    return f"SELECT * FROM LinkedInAccounts WHERE username='{username}';"

