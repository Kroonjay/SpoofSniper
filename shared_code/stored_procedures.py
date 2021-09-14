from .models import LinkedInAccountIn, TwitterAccountIn
import logging

def create_linkedin_account_procedure(account_in: LinkedInAccountIn):
    return f'EXEC [dbo].[CreateLinkedInAccount] @full_name="{account_in.full_name}", @username="{account_in.username}", @company="{account_in.company}", @job_title="{account_in.job_title}", @account_url="{account_in.account_url}";'

def update_linkedin_account_last_seen_at_procedure(username: str):
    stripped_username = ''.join(e for e in username if e.isalnum())
    return f'EXEC [dbo].[UpdateLinkedInLastSeenAt] @username="{stripped_username}"'
    

def create_twitter_account_procedure(account_in: TwitterAccountIn):
    return f'EXEC [dbo].[CreateTwitterAccount] @twitter_account_id="{account_in.twitter_account_id}", @full_name="{account_in.full_name}", @username="{account_in.username}", @account_url="{account_in.account_url}", @is_verified={account_in.is_verified}, @created_at=\'{account_in.created_at}\', @num_followers={account_in.num_followers}, @num_friends={account_in.num_friends}, @num_statuses={account_in.num_statuses}'

def update_twitter_account_last_seen_at_procedure(twitter_account_id: int):
    return f"EXEC [dbo].[UpdateTwitterLastSeenAt] @twitter_account_id='{twitter_account_id}'"

