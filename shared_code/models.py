from pydantic import BaseModel
from datetime import datetime

class AccountStatusEnum(BaseModel):
    UNCLASSIFIED: str = "Unclassified"
    WHITELIST: str = "Whitelisted"
    IMPOSTER: str = "Imposter"
    UNRELATED: str = "Unrelated"
    DISABLED: str = "Disabled"


class LinkedInAccountIn(BaseModel):
    full_name: str
    username: str
    company: str = None
    job_title: str = None
    account_url: str
    keyword_id: int = 0

class TwitterAccountIn(BaseModel):
    twitter_account_id: str 
    full_name: str
    username: str
    account_url: str
    is_verified: bool
    created_at: datetime = None
    num_followers: int = None
    num_friends: int = None
    num_statuses: int = None
    keyword_id: int = 0

class TwitterAccount(TwitterAccountIn):
    account_id: int
    first_seen_at: datetime
    last_seen_at: datetime
    num_reports: int
    account_status: str


class LinkedInAccount(LinkedInAccountIn):
    account_id: int
    first_seen_at: datetime
    last_seen_at: datetime
    num_reports: int
    account_status: str

class Keyword(BaseModel):
    keyword_id: int
    keyword_string: str
    use_on_linkedin: bool
    use_on_twitter: bool
    first_searched_at: datetime
    last_searched_at: datetime

class ImpersonationAccountIn(BaseModel):
    source_account_id: int
    source_account_type: int
    full_name: str
    username: str
    num_reports: int
    account_url: str



class ImpersonationAccount(ImpersonationAccountIn):
    account_id: int
    created_at: datetime


class AccountTypes(BaseModel):
    linkedin: int = 1
    twitter: int = 2

class ErrorLog(BaseModel):
    module: str
    result: str
    errorType: str = None
    errorMessage: str = None
    data: str = None
    createdAt: datetime