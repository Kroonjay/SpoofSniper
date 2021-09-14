import logging

import azure.functions as func
from ..shared_code.impersonation_monitor import ImpersonationMonitor
from datetime import datetime
import os

def main(req: func.HttpRequest) -> func.HttpResponse:

    if not req.params.get("accountId"):
        logging.warning(f"UpdateAccountClassification Trigger - Invalid Request Received - accountId Param not Present")
        return func.HttpResponse(status_code = 400, body = "Invalid Request - Required Parameter accountId is Missing!")
    else:
        
        try:
            account_id = int(req.params.get("accountId"))
        except:
            logging.warning(f"UpdateAccountClassification Trigger - Invalid Request Received - accountId Param not Integer")
            return func.HttpResponse(status_code = 400, body = "Invalid Request - Required Parameter accountId Must be an Integer")
    
    if not req.params.get("accountType"):
        logging.warning(f"UpdateAccountClassification Trigger - Invalid Request Received - accountType Param not Present")
        return func.HttpResponse(status_code = 400, body = "Invalid Request - Required Parameter accountType is Missing!")
    else:
        try:
            account_type = int(req.params.get("accountType"))
        except:
            logging.warning(f"UpdateAccountClassification Trigger - Invalid Request Received - accountType Param not Integer")
            return func.HttpResponse(status_code = 400, body = "Invalid Request - Required Parameter accountId Must be an Integer")
    
    if not req.params.get("newStatus"):
        logging.warning(f"UpdateAccountClassification Trigger - Invalid Request Received - newStatus Param not Present")
        return func.HttpResponse(status_code = 400, body = "Invalid Request - Required Parameter newStatus is Missing")
    else:
        try:
            new_status = str(req.params.get("newStatus"))
        except:
            logging.warning(f"UpdateAccountClassification Trigger - Invalid Request Received - newStatus Param not String")
            return func.HttpResponse(status_code = 400, body = "Invalid Request - Required Parameter newStatus Must be a String!")

    im = ImpersonationMonitor()
    logging.info(f"UpdateAccountClassification Trigger - Request Received - Account ID: {account_id} - New Status: {new_status}")
    success = im.classify(account_id, account_type, new_status)
    if not success:
        return func.HttpResponse(status_code = 400, body = "Invalid Request - Failed to Update Account - Unknown Reason")

    return func.HttpResponse(status_code = 200, body = "Account Classification Updated Successfully")