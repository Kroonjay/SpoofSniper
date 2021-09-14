import twitter
import os
from .models import TwitterAccountIn
#import utils, models
import logging
from datetime import datetime
import pytz

#Finds what seems to be the only DateTime format that both SQL Server and Twitter can Agree on...
def parse_datetime(datetime_in):
    date_format = '%a %b %d %H:%M:%S'
    try:
        t = datetime.strptime(datetime_in, date_format).replace(tzinfo=pytz.UTC)
    except ValueError as v:
        if len(v.args) > 0 and v.args[0].startswith('unconverted data remains: '):
            datetime_in = datetime_in[:-(len(v.args[0]) - 26)]
            t = datetime.strptime(datetime_in, date_format)
        else:
            raise
    return t


class TwitterAgent:
    def __init__(self):
        consumer_key=os.getenv("TWITTER_CONSUMER_KEY")
        consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
        access_token_key = os.getenv("TWITTER_ACCESS_TOKEN_KEY")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.api = twitter.Api(consumer_key=consumer_key,
                        consumer_secret=consumer_secret,
                        access_token_key=access_token_key,
                        access_token_secret=access_token_secret)
        self.matched_accounts = []
        self.account_base_url = 'https://twitter.com/'
        self.num_pages = 20 

    def get_account_url(self, username):
        return f"{self.account_base_url}{username.lower()}"


    #Use Twitter API to search for accounts where screen_name contains user full_name
    def find_accounts_by_keyword(self, keyword):
        matched_accounts = []
        if not isinstance(keyword, str):
            logging.critical(f"TwitterAgent - Failed to Initialize - Keyword is not String - Type: {type(keyword)} - Keyword: {keyword}")
            return
        page = 0
        while page < self.num_pages:
            twtr_accounts = self.api.GetUsersSearch(term=keyword, page=page, count=50)
            for twtr_account in twtr_accounts:
                account_url = self.get_account_url(twtr_account.screen_name)
                matched = TwitterAccountIn(twitter_account_id= twtr_account.id_str, full_name= twtr_account.name, username=twtr_account.screen_name, account_url=account_url, is_verified=twtr_account.verified, created_at=parse_datetime(twtr_account.created_at), num_followers=twtr_account.followers_count, num_friends=twtr_account.friends_count, num_statuses=twtr_account.statuses_count)
                logging.debug(f"Twitter Agent - Match - Matched New Account - Details: {matched.json()}")
                matched_accounts.append(matched)    
            page +=1
        return matched_accounts

def main():
    pass
    

if __name__ == "__main__":
    main()