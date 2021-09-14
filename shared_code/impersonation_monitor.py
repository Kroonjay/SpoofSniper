from .linkedin_helpers import LinkedInAgent
from .twitter_helpers import TwitterAgent
from .crud_helpers import connect_to_db, fetch_twitter_keywords, fetch_linkedin_keywords, upsert_linkedin_account, upsert_twitter_account, fetch_linkedin_impersonation_accounts, fetch_twitter_impersonation_accounts, create_impersonation_account, clear_impersonation_accounts_table, update_linkedin_account_status, update_twitter_account_status, fetch_linkedin_account_by_id, fetch_twitter_account_by_id
from .models import LinkedInAccount, TwitterAccount, AccountTypes, ImpersonationAccountIn, AccountStatusEnum
from .azure_helpers import post_alert
from pydantic import ValidationError
import os
import logging


def source_account_to_impersonation_account(source_account):
    account_types = AccountTypes()
    if isinstance(source_account, LinkedInAccount):
        account_type = account_types.linkedin
    elif isinstance(source_account, TwitterAccount):
        account_type = account_types.twitter
    else:
        logging.warning(f"Impersonation Monitor - Source Account to Impersonation Account - Failed - Source Account is Invalid Type - Type: {type(source_account)}")
        return None
    try:
        ia = ImpersonationAccountIn(source_account_id = source_account.account_id, source_account_type=account_type, **source_account.dict())
        return ia
    except ValidationError as ve:
        logging.warning(f"Impersonation Monitor - Source Account to Impersonation Account - Failed - Validation Error - Msg: {ve.json()}")
        return None
    


class ImpersonationMonitor:

    def __init__(self):
        cnxn_str = os.getenv("DATABASE_CONNECTION_STRING")
        if not cnxn_str:
            logging.critical(
                "Impersonation Monitor - Initialize - Failure - Unable to find Database Connection String")
            raise Exception(
                "Failed to Initialize Impersonation Monitor - No Connection STring")
        self.cnxn = connect_to_db(cnxn_str)
        if not self.cnxn:
            logging.critical(
                "Impersonation Monitor - Initialize - Failure - Unable to Connect to Database")
            raise Exception(
                "Failed to Initialize Impersonation Monitor - Couldn't Connect to DB")
        self.search_twitter = True
        self.search_linkedin = True
        self.twitter_keywords = fetch_twitter_keywords(self.cnxn)
        self.num_twitter_keywords = 0
        self.num_linkedin_keywords = 0
        if not self.twitter_keywords:
            logging.warning(
                "Impersonation Monitor - Initialize - Twitter Search Disabled - No Keywords to Search")
            self.search_twitter = False
        else:
            self.num_twitter_keywords = len(self.twitter_keywords)
        self.linkedin_keywords = fetch_linkedin_keywords(self.cnxn)
        if not self.linkedin_keywords:
            logging.warning(
                "Impersonation Monitor - Initialize - LinkedIn Search Disabled - No Keywords to Search")
            self.search_linkedin = False
        else:
            self.num_linkedin_keywords = len(self.linkedin_keywords)
            self.linkedin_keywords = iter(self.linkedin_keywords)
        if not self.twitter_keywords and not self.linkedin_keywords:
            logging.critical(
                "Impersonation Monitor - Initialize - Failure - Nothing to Search")
            raise Exception(
                "Failed to Initialize Impersonation Monitor - No Keywords")
        else:
            self.twitter_keywords = iter(self.twitter_keywords)
        self.linkedin_agent = LinkedInAgent()
        self.twitter_agent = TwitterAgent()
        self.num_linkedin_accounts = 0
        self.num_twitter_accounts = 0


    def scan(self):
        logging.info(
            f"Impersonation Monitor - Starting Scan - Searching {self.num_twitter_keywords} Twitter Keywords and {self.num_linkedin_keywords} LinkedIn Keywords")
        twitter_keyword = True
        linkedin_keyword = True
        while twitter_keyword or linkedin_keyword:
            twitter_keyword = next(self.twitter_keywords, None)
            if twitter_keyword:
                for account in self.twitter_agent.find_accounts_by_keyword(twitter_keyword.keyword_string):
                    account.keyword_id = twitter_keyword.keyword_id
                    post_alert(account.json(), 'TwitterAccounts')
                    #upsert_twitter_account(self.cnxn, account)
                    self.num_twitter_accounts += 1
            linkedin_keyword = next(self.linkedin_keywords, None)
            if linkedin_keyword:
                for account in self.linkedin_agent.find_accounts_by_keyword(linkedin_keyword.keyword_string):
                    account.keyword_id = linkedin_keyword.keyword_id
                    post_alert(account.json(), 'LinkedInAccounts')
                    #upsert_linkedin_account(self.cnxn, account)
                    self.num_linkedin_accounts += 1
        logging.info(
            f"Impersonation Monitor - Completed - Found {self.num_linkedin_accounts} LinkedIn Accounts and {self.num_twitter_accounts} Twitter Accounts")
        return self
    
    def update(self):
        logging.info(
            "Impersonation Monitor - Starting Update")
        cleared = clear_impersonation_accounts_table(self.cnxn)
        if not cleared:
            logging.critical(f"Impersonation Monitor - Update - Error - Failed to Clear Impersonation Accounts Table")
            return
        num_linkedin_accounts = 0
        num_twitter_accounts = 0
        for account in fetch_linkedin_impersonation_accounts(self.cnxn):
            ia = source_account_to_impersonation_account(account)
            if not ia:
                logging.warning(f"Impersonation Monitor - Update - Error - Failed to Convert LinkedIn Account to Impersonation Account")
                continue
            create_impersonation_account(self.cnxn, ia)
            num_linkedin_accounts +=1
        logging.info(f"Impersonation Monitor - Update - LinkedIn Accounts Added to Impersonations Table - Total Acconts: {num_linkedin_accounts}")
        for account in fetch_twitter_impersonation_accounts(self.cnxn):
            ia = source_account_to_impersonation_account(account)
            if not ia:
                logging.warning(f"Impersonation Monitor - Update - Error - Failed to Convert Twitter Account to Impersonation Account")
                continue
            create_impersonation_account(self.cnxn, ia)
            num_twitter_accounts += 1
        logging.info(f"Impersonation Monitor - Update - Twitter Accounts Added to Impersonations Table - Total Accounts: {num_twitter_accounts}")
        logging.info(f"Impersonation Monitor - Update - Complete - Total LinkedIn Accounts: {num_linkedin_accounts} - Total Twitter Accounts: {num_twitter_accounts}")
    
    def classify(self, account_id, account_type, new_status):
        if not isinstance(account_id, int):
            logging.warning("Impersonation Monitor - Classify - Failed - Accound ID must be Integer")
            return None
        if not new_status in [(v) for k, v in AccountStatusEnum().dict().items()]:
            logging.warning(f"Impersonation Monitor - Classify - Failed - New Status is Invalid - New Status: {new_status}")
            return None
        if account_type == AccountTypes().linkedin:
            account = fetch_linkedin_account_by_id(self.cnxn, account_id)
        elif account_type == AccountTypes().twitter:
            account = fetch_twitter_account_by_id(self.cnxn, account_id)
        else:
            logging.warning(f"Impersonation Monitor - Classify - Failed - Invalid Account Type - Account ID: {account_id}")
            return None
        if not account:
            logging.warning(f"Impersonation Monitor - Classify - Failed - Account Not Found in Database - Account ID: {account_id}")
            return None
        if account.account_status == AccountStatusEnum().WHITELIST:
            logging.warning(f"Impersonation Monitor - Classify - Failed - Can't Modify a Whitelisted Account - Account ID: {account.account_id}")
            return None
        if account.account_status == AccountStatusEnum().DISABLED:
            logging.warning(f"Impersonation Monitor - Classify - Failed - Can't Modify a Disabled Account - Account ID: {account.account_id}")
            return None
        if new_status == AccountStatusEnum().IMPOSTER:
            logging.debug(f"Impersonation Monitor - Classify - Imposter Account Reported - Account ID: {account.account_id}")
            account.num_reports += 1 
        if account_type == AccountTypes().linkedin:
            updated = update_linkedin_account_status(self.cnxn, account.account_id, new_status, account.num_reports)
            if not updated:
                logging.warning(f"Impersonation Monitor - Classify - Failed to Update LinkedIn Account - Account ID: {account.account_id}")
                return None
            return True
        elif account_type == AccountTypes().twitter:
            updated = update_twitter_account_status(self.cnxn, account_id, new_status, account.num_reports)
            if not updated:
                logging.warning(f"Impersonation Monitor - Classify - Failed to Update LinkedIn Account - Account ID: {account.account_id}")
                return None
            return True
        else:
            logging.warning(f"Impersonation Monitor - Classify - Failed to Update Account - Unknown Account Type - Account Type: {account_type}")
            return None

    def run(self):
        self.scan()
        self.update()