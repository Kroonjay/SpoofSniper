import os
from shared_code import crud_helpers
from shared_code.models import LinkedInAccountIn
from shared_code.linkedin_helpers import grab_username_from_url
cnxn_str = ""

cnxn = crud_helpers.connect_to_db(cnxn_str)

account_in = LinkedInAccountIn(first_name="Test", last_name="User", username="TestUser01", company="TestCompany", job_title="Boss", account_url="https://www.linkedin.com/in/bigboss/")

#account = crud_helpers.linkedin_account_create_new_or_update_existing(cnxn, account_in)

url = grab_username_from_url(account_in.account_url)

print(url)