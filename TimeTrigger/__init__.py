import datetime
import logging

import azure.functions as func
from ..shared_code.impersonation_monitor import ImpersonationMonitor
import datetime

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()


    logging.info(f'TimerTrigger - Timer is Past Due - Beginning Account Search  - Start Time: {utc_timestamp}')

    im = ImpersonationMonitor()
    im.run()
    logging.info(f"TimerTrigger - Run Complete")
    

