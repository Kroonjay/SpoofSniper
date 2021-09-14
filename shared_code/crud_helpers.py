import pyodbc
import datetime
import logging
import time
from .queries import create_linkedin_account_stmt, read_linkedin_account_by_id_stmt, read_twitter_account_by_id_stmt, update_linkedin_account_stmt, update_twitter_account_stmt, create_twitter_account_stmt, read_linkedin_keywords_stmt, read_twitter_keywords_stmt, upsert_linkedin_account_stmt, upsert_twitter_account_stmt, read_linkedin_impersonation_accounts_stmt, read_twitter_impersonation_accounts_stmt, create_impersonation_account_stmt, clear_impersonation_accounts_table_stmt
from .stored_procedures import create_linkedin_account_procedure, update_linkedin_account_last_seen_at_procedure, create_twitter_account_procedure, update_twitter_account_last_seen_at_procedure
from .models import LinkedInAccountIn, LinkedInAccount, TwitterAccountIn, TwitterAccount, Keyword, ImpersonationAccountIn, AccountStatusEnum


def to_linkedin_account(row):
    return LinkedInAccount(account_id=row[0], full_name=row[1], username=row[2], company=row[3], job_title=row[4], account_status=row[5], account_url=row[6], first_seen_at=row[7], last_seen_at=row[8], num_reports=row[9], keyword_id=row[10])


def to_twitter_account(row):
    return TwitterAccount(account_id=row[0], full_name=row[1], username=row[2], twitter_account_id=row[3], is_verified=row[4], created_at=row[5], num_followers=row[6], num_friends=row[7], num_statuses=row[8], account_status=row[9], account_url=row[10], first_seen_at=row[11], last_seen_at=row[12], num_reports=row[13], keyword_id=row[14])

def to_keyword(row):
    return Keyword(keyword_id=row[0], keyword_string=row[1], use_on_linkedin=row[2], use_on_twitter=row[3], first_searched_at=row[4], last_searched_at=row[5])

    

def convert_to_params(pydantic_object):
    return tuple(v for k, v in pydantic_object.dict().items())

def connect_to_db(cnxn_str, max_attempts=10):
    attempts = 1

    if not cnxn_str:
        logging.critical(
            "Crud Helpers - Connect to Database - Failed - Connection String Not Provided")
        return None
    while attempts <= max_attempts:
        try:  # PyODBC will usually timeout on the first attempt to connect to the DB, retrying connecting fixes the issue
            cnxn = pyodbc.connect(cnxn_str)
            logging.info(
                f"Crud Helpers  - Connect to Database - Success - Took {str(attempts)} Attempt(s)")
            return cnxn
        except (pyodbc.ProgrammingError, pyodbc.OperationalError) as e:
            if e.args[0] == '42000':  # IP Whitelisting Error, won't resolve
                logging.error(
                    f"Crud Helpers - Connect to Database - Failed - IP not Whitelisted in Database")
                return None
            logging.error(
                f"Crud Helpers - Connect to Database - Programming or Operational Error - Msg: {e.args[1]}")
            time.sleep(2)
            attempts += 1
    return None


def fetch_linkedin_account_by_id(cnxn, account_id):
    if not isinstance(account_id, int):
        logging.warning(f"Crud Helpers - Fetch LinkedIn Account by ID - Failed - Account ID must be an Integer")
        return None
    query = read_linkedin_account_by_id_stmt
    cursor = cnxn.cursor()
    cursor.execute(query, account_id)
    row = cursor.fetchone()
    if row:
        account = to_linkedin_account(row)
        logging.debug(
            f"Crud Helpers - Fetch LinkedIn Account by Username - Complete - Account ID: {account_id}")
        return account
    else:
        logging.warning(
            f"Crud Helpers - Fetch LinkedIn Account by Username - Failed - No Account for Username: {account_id}")
        return None
    return account

def fetch_linkedin_impersonation_accounts(cnxn):
    query = read_linkedin_impersonation_accounts_stmt
    cursor = cnxn.cursor()
    cursor.execute(query)
    accounts = []
    for row in cursor.fetchall():
        account = to_linkedin_account(row)
        accounts.append(account)
    logging.debug(f"Crud Helpers - Fetch LinkedIn Impersonation Accounts - Complete - Total Accounts: {len(accounts)}")
    return accounts

def fetch_twitter_impersonation_accounts(cnxn):
    query = read_twitter_impersonation_accounts_stmt
    cursor = cnxn.cursor()
    cursor.execute(query)
    accounts = []
    for row in cursor.fetchall():
        account = to_twitter_account(row)
        accounts.append(account)
    logging.debug(f"Crud Helpers - Fetch Twitter Impersonation Accounts - Complete - Total Accounts: {len(accounts)}")
    return accounts

def fetch_twitter_account_by_id(cnxn, account_id):
    if not isinstance(account_id, int):
        logging.warning(f"Crud Helpers - Fetch LinkedIn Account by ID - Failed - Account ID must be an Integer")
        return None
    query = read_twitter_account_by_id_stmt
    cursor = cnxn.cursor()
    cursor.execute(query, account_id)
    account = None
    row = cursor.fetchone()
    if row:
        account = to_twitter_account(row)
        logging.debug(
            f"Crud Helpers - Fetch Twitter Account by Twitter Account ID - Complete - Twitter Account ID: {account_id}")
    else:
        logging.warning(
            f"Crud Helpers - Fetch Twitter Account by Twitter Account ID - Failed - No Account for Twitter Account ID: {account_id}")
    return account



def upsert_linkedin_account(cnxn, account_in):
    if not isinstance(account_in, LinkedInAccountIn):
        logging.warning(
            f"Crud Helpers - Upsert LinkedIn Account - Input is not LinkedInAccountIn Object - Type: {type(account_in)}")
        return None
    cursor = cnxn.cursor()
    params = convert_to_params(account_in)
    query = upsert_linkedin_account_stmt
    try:
        cursor.execute(query, params)
        cnxn.commit()
        logging.debug(
            f"Crud Helpers - Upsert LinkedIn Account - Success - Username: {account_in.username.capitalize()}")
        return True
    except Exception as e:
        logging.warning(
            f"Crud Helpers - Upsert LinkedIn Account - Failed - Username: {account_in.username.capitalize()} - Msg: {e.args}")
        return None

def upsert_twitter_account(cnxn, account_in):
    if not isinstance(account_in, TwitterAccountIn):
        logging.warning(
            f"Crud Helpers - Upsert Twitter Account - Input is not TwitterAccountIn Object - Type: {type(account_in)}")
        return None
    cursor = cnxn.cursor()
    params = convert_to_params(account_in)
    query = upsert_twitter_account_stmt
    try:
        cursor.execute(query, params)
        cnxn.commit()
        logging.debug(
            f"Crud Helpers - Upsert Twitter Account - Success - Twitter Account ID: {account_in.twitter_account_id}")
        return True
    except Exception as e:
        logging.warning(
            f"Crud Helpers - Upsert Twitter Account - Twitter Account ID: {account_in.twitter_account_id} - Msg: {e.args}")
        return None

def create_impersonation_account(cnxn, account_in):
    if not isinstance(account_in, ImpersonationAccountIn):
        logging.warning(f"Crud Helpers - Create Impersonation Account - Input is not ImpersonationAccountIn Object - Type: {type(account_in)}")
        return None
    cursor = cnxn.cursor()
    params = convert_to_params(account_in)
    query = create_impersonation_account_stmt
    try:
        cursor.execute(query, params)
        cnxn.commit()
        logging.debug(
            f"Crud Helpers - Create Impersonation Account - Success - Username: {account_in.username}"
        )
        return True
    except Exception as e:
        logging.warning(
            f"Crud Helpers - Create Impersonation Account - Failed - Username: {account_in.username} - Msg: {e.args}"
        )
        return None

def clear_impersonation_accounts_table(cnxn):
    cursor = cnxn.cursor()
    query = clear_impersonation_accounts_table_stmt
    try:
        cursor.execute(query)
        cnxn.commit()
        logging.info(
            f"Crud Helpers - Clear Impersonation Accounts Table - Success"
        )
        return True
    except Exception as e:
        logging.warning(
            f"Crud Helpers - Clear Impersonation Accounts Table - Failed - Msg: {e.args}"
        )
        return None


def fetch_linkedin_keywords(cnxn):
    keywords = []
    cursor = cnxn.cursor()
    query = read_linkedin_keywords_stmt
    for row in cursor.execute(query).fetchall():
        keyword = to_keyword(row)
        keywords.append(keyword)
    logging.debug(f"Crud Helpers - Fetch LinkedIn Keywords - Complete - Total Keywords: {len(keywords)}")
    return keywords


def fetch_twitter_keywords(cnxn):
    keywords = []
    cursor = cnxn.cursor()
    query = read_twitter_keywords_stmt
    for row in cursor.execute(query).fetchall():
        keyword = to_keyword(row)
        keywords.append(keyword)
    logging.debug(f"Crud Helpers - Fetch Twitter Keywords - Complete - Total Keywords: {len(keywords)}")
    return keywords

def update_linkedin_account_status(cnxn, account_id, new_status, num_reports):
    
    cursor = cnxn.cursor()
    query = update_linkedin_account_stmt
    params = tuple([account_id, new_status, num_reports])
    try:
        cursor.execute(query, params)
        cnxn.commit()
        logging.debug(
            f"Crud Helpers - Update LinkedIn Account Status - Success - Account ID: {account_id}"
        )
        return True
    except Exception as e:
        logging.warning(
            f"Crud Helpers - Update LinkedIn Account Status - Failed - Account ID: {account_id} - Msg: {e.args}"
        )
        return None

def update_twitter_account_status(cnxn, account_id, new_status, num_reports):
    
    cursor = cnxn.cursor()
    query = update_twitter_account_stmt
    params = tuple([account_id, new_status, num_reports])
    try:
        cursor.execute(query, params)
        cnxn.commit()
        logging.debug(
            f"Crud Helpers - Update Twitter Account Status - Success - Account ID: {account_id}"
        )
        return True
    except Exception as e:
        logging.warning(
            f"Crud Helpers - Update Twitter Account Status - Failed - Account ID: {account_id} - Msg: {e.args}"
        )
        return None