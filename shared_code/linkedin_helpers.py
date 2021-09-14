import logging
import os
from urllib.parse import urlparse
from .models import LinkedInAccountIn
from pydantic import ValidationError
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time

def build_profile_url(username: str):
    return f"https://www.linkedin.com/in/{username}/"

def grab_username_and_safe_url(account_url: str):
    base_url = "linkedin.com"
    base_profile_path = "/in/"
    parse_result = urlparse(account_url)
    if not account_url:
        logging.warning(f"LinkedIn Helpers - Grab Username From URL - Failed - Account URL is None")
        return None
    if not base_url in parse_result.netloc:
        logging.warning(f"LinkedIn Helpers - Grab Username From URL - Failed - Account URL not Valid for LinkedIn - Account URL: {account_url}")
        return None
    
    if base_profile_path not in parse_result.path:
        logging.warning(f"LinkedIn Helpers - Grab Username From URL - Failed - '/in/' Not Found in Account URL Path - Path: {parse_result.path}")
        return None
    try:
        profile_base_stripped = parse_result.path.split(base_profile_path)[1] #Strip /in/ from Path
        if "/" in profile_base_stripped:
            profile_base_stripped = profile_base_stripped.split("/")[0]
    except:
        logging.warning("LinkedIn Helpers - Grab Username From URL - Failed - Unable to Split Profile Section of URL")
        return None
    safe_url = parse_result._replace(params='', query='', fragment='', path=f"/in/{profile_base_stripped}").geturl()
    return {"username" : ''.join(e for e in profile_base_stripped if e.isalnum()), "url": safe_url}

def grab_details_from_title(title: str):
    if not title:
        logging.warning(f"LinkedIn Helpers - Grab Details from Title - Failed - Title is None")
        return None
    sections = title.split(" - ")
    company_name = os.getenv("COMPANY_NAME")
    company_name_modifier = os.getenv("COMPANY_NAME_MODIFIER")
    full_name = None
    job_title = None
    company_in = ""
    if not sections:
        logging.warning(f"LinkedIn Helpers - Grab Details from Title - Failed - Failed to Split Title into Sections - Title: {title}")
        return None
    full_name = sections[0]
    if not len(sections) >= 2:
        logging.warning(f"LinkedIn Helpers - Grab Details from Title - Erorr - Too Few Sections in Title - Title: {title}")
        return None  
    if company_name in sections[1]:
        company_in = sections[1] #format is [COMPANY_NAME] ...
    else:
        job_title = sections[1]
        if company_name in sections[-1]:
            company_in = sections[-1] #format is [COMPANY_NAME] | LinkedIn
    if company_name in company_in.lower().strip() and company_name_modifier in company_in.lower().strip():
        company = f"{company_name} {company_name_modifier}".title()
    elif company_name in company_in.lower().strip():
        company = company_name.title()
    else:
        company = "Unknown"
        logging.warning(f"LinkedIn Helpers - Grab Details from Title - Error - Company not Recognized - Company Name: {company_in}")
    logging.debug(f"LinkedIn Helpers - Grab Details from Title - Completed - Full Name: {full_name} - Job Title: {job_title} - Company: {company}")
    return {"full_name" : full_name, "job_title": job_title, "company": company}

def parse_title(title: str):
    full_name = None
    job_title = None
    company = None
    if not title:
        logging.warning(f"LinkedIn Helpers - Grab Details from Title - Failed - Title is None")
        return None
    if "|" in title:
        title = title.split("|")[0]
    if "..." in title:
        title = title.split("...")[0]
    if "–" in title:
        sections = title.split(" – ")
    else:
        sections = title.split(" - ")
    if not sections:
        logging.warning(f"LinkedIn Helpers - Grab Details from Title - Failed - Failed to Split Title into Sections - Title: {title}")
        return None
    if len(sections) == 1:
        logging.warning(f"LinkedIn Helpers - Grab Details from Title - Failed - Only 1 Section in Title - Title: {title}")
        return None
    elif len(sections) == 2:
        #format is Full Name - City, State | Professional Profile
        full_name = sections[0]
    elif len(sections) == 3:
        full_name = sections[0]
        job_title = sections[1]
        company = sections[2]
    else:
        logging.warning(f"LinkedIn Helpers - Grab Details from Title - Error - Found TItle with 4 Sections - Title: {title}")
        return None
    return {"full_name" : full_name, "job_title": job_title, "company": company}
    


def parse_account_data_to_account(account_data):
    profile_url = account_data.get_attribute('href')
    account = None
    url_details = grab_username_and_safe_url(profile_url)
    if not url_details:
        logging.warning(f"LinkedIn Helpers - Parse Account Data to Account - Failed - Unable to Retrieve Username")
        return account

    profile_title = account_data.find_element_by_tag_name("h3").text
    title_details = parse_title(profile_title)
    if not title_details:
        logging.warning(f"LinkedIn Helpers - Parse Account Data to Account - Failed - Unable to Retrieve Title Details")
        return account
    try:
        account = LinkedInAccountIn(username=url_details['username'], account_url = url_details['url'], **title_details)
    except ValidationError as ve:
        logging.warning(f"LinkedIn Helpers - Parse Account Data to Account - Failed - Msg: {ve.json()}")
    return account


class LinkedInAgent:

    def __init__(self):
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options = chrome_options
        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver", chrome_options=chrome_options)
        self.matched_accounts = []



    
    def find_accounts_by_keyword(self, keyword):
        if not isinstance(keyword, str):
            logging.critical(f"LinkedInAgent - Failed to Initialize - Keyword is not String - Type: {type(keyword)} - Keyword: {keyword}")
            return
        
        self.driver.get('https://www.google.com/')
        time.sleep(2)
        search_input = self.driver.find_element_by_name('q')
        # let google find any linkedin user with keyword
        search_string =  f'site:linkedin.com/in/ AND "{keyword}"'
        logging.debug(f"LinkedIn Agent - Search String - {search_string}")
        search_input.send_keys(search_string)
        time.sleep(3)
        search_input.send_keys(Keys.RETURN)
        
        num_profiles = 0
        num_pages = 0
        matched_accounts = []
        # grab all linkedin profiles from first page at Google
        profile_data = self.driver.find_elements_by_xpath('//*[@class="r"]/a[1]')
        for profile in profile_data:
            account_in = parse_account_data_to_account(profile)
            if not account_in:
                logging.debug(f"LinkedIn Agent - Parsing Profiles - Failed to Parse")
                continue
            matched_accounts.append(account_in)
            logging.debug(f"LinkedIn Agent - Created Profile - Username: {account_in.username}")
        num_profiles += len(profile_data)
        next_page_button = None
        try:
            next_page_button = self.driver.find_element_by_xpath("//span[text()='Next']")
            next_page_button.click()
            num_pages +=1
        except NoSuchElementException as nsee:
            logging.info(f"LinkedIn Agent - Google Search for LinkedIn Accounts Complete - Searched {num_pages} Total Pages - Msg: {nsee.msg}")

        while next_page_button:
            profile_data = self.driver.find_elements_by_xpath('//*[@class="r"]/a[1]')
            for profile in profile_data:
                account_in = parse_account_data_to_account(profile)
                if not account_in:
                    logging.warning(f"LinkedIn Agent - Parsing Profiles - Failed to Parse")
                    continue
                logging.debug(f"LinkedIn Agent - Parsing Profiles - Successfully Parsed - Data: {account_in.json()}")
                matched_accounts.append(account_in)
                logging.debug(f"LinkedIn Agent - Created Profile - Success - Username: {account_in.username}")
            num_profiles += len(profile_data)
            try:
                next_page_button = self.driver.find_element_by_xpath("//span[text()='Next']")
                next_page_button.click()
                num_pages +=1
            except NoSuchElementException as nsee:
                logging.debug(f"LinkedIn Agent - Google Search for Linkedin Accounts Complete - Searched {num_pages} Total Pages")
                next_page_button = None
            logging.info(f"LinkedIn Agent - Moving on to Next Page - Total Accounts: {len(matched_accounts)} - Total Pages: {num_pages}")
        logging.info(f"LinkedIn Agent - Account Search Complete - Total Accounts: {len(matched_accounts)} - Total Pages: {num_pages}")
        return matched_accounts
            
