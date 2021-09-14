

read_linkedin_account_by_id_stmt = "SELECT * FROM LinkedInAccounts WHERE account_id=?;"
read_twitter_account_by_id_stmt = 'SELECT * FROM TwitterAccounts WHERE account_id=?'
read_linkedin_keywords_stmt = 'SELECT * FROM Keywords WHERE use_on_linkedin=1'
read_twitter_keywords_stmt = 'SELECT * FROM Keywords WHERE use_on_twitter=1'

update_twitter_account_stmt = 'EXEC UpdateTwitterAccountStatus @account_id=?, @account_status=?, @num_reports=?'
update_linkedin_account_stmt = 'EXEC UpdateLinkedInAccountStatus @account_id=?, @account_status=?, @num_reports=?'

create_linkedin_account_stmt = 'EXEC [dbo].[CreateLinkedInAccount] @full_name=?, @username=?, @company=?, @job_title=?, @account_url=?'
create_twitter_account_stmt = 'EXEC [dbo].[CreateTwitterAccount] @twitter_account_id=?, @full_name=?, @username=?, @account_url=?, @is_verified=?, @created_at=?, @num_followers=?, @num_friends=?, @num_statuses=?'
create_impersonation_account_stmt = 'EXEC CreateImpersonationAccount @source_account_id=?, @source_account_type=?, @full_name=?, @username=?, @num_reports=?, @account_url=?'
upsert_linkedin_account_stmt = 'EXEC [dbo].[UpsertLinkedInAccount] @full_name=?, @username=?, @company=?, @job_title=?, @account_url=?, @keyword_id=?'
upsert_twitter_account_stmt = 'EXEC [dbo].[UpsertTwitterAccount] @twitter_account_id=?, @full_name=?, @username=?, @account_url=?, @is_verified=?, @created_at=?, @num_followers=?, @num_friends=?, @num_statuses=?, @keyword_id=?'

read_linkedin_impersonation_accounts_stmt = "SELECT * FROM [dbo].[LinkedInAccounts] WHERE account_status in ('Unclassified', 'Imposter')"
read_twitter_impersonation_accounts_stmt = "SELECT * FROM [dbo].[TwitterAccounts] WHERE account_status in ('Unclassified', 'Imposter')"

clear_impersonation_accounts_table_stmt = 'DELETE FROM [dbo].[ImpersonationAccounts] WHERE 1=1'