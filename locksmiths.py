"""locksmiths.py

Locksmiths push bot for the hourly report of locksmiths jobs
The script preloads the txt files with each query. 
It uses the functions of the src.utils_bot module to modify the result of the queries. 
With the information, it generates the report and sends it to Telegram using the src.bot module.


The script needs the installation of the following packages:
* os: For path management and directory creation
* pandas: Return a DataFrame object
* dotenv: Load environment variables
* logging: Log management

This script uses the following custom modules:
* src: Adapt the format of the data to be printed on Telegram

"""
import os
import pandas as pd
import src.db as db
import src.bot as bot
import src.utils_bot as utils_bot
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
# Define project main path
MAIN_FOLDER = os.getenv('MAIN_PATH')

# LOG File save
log_file = os.path.join(MAIN_FOLDER, 'logs/locksmiths_batch.log')
logger = logging.getLogger(__name__)
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Define chat id
GROUP_ID = os.getenv('LOCKSMITHS_GROUP')

# For TEST
# GROUP_ID = os.getenv('TEST_GROUP')

LOCKSMITHS_REPORT_IMAGE = os.getenv('LOCKSMITHS_REPORT_IMAGE')

################################## Query Load #####################################

query_path = os.path.join(MAIN_FOLDER, 'queries/locksmiths')

LS_total_pending_jobs_by_locksmith_day = open(os.path.join(query_path,
                    'LS_total_pending_jobs_by_locksmith_day.sql'), 'r').read()

LS_total_pending_jobs_day = open(os.path.join(query_path,
                    'LS_total_pending_jobs_day.sql'), 'r').read()

LS_total_completed_jobs_day = open(os.path.join(query_path,
                    'LS_total_completed_jobs_day.sql'), 'r').read()

LS_total_revenue_day = open(os.path.join(query_path,
                    'LS_total_revenue_day.sql'), 'r').read()

LS_selected_vs_invoice_locksmiths = open(os.path.join(query_path,
                    'LS_selected_vs_invoice_locksmiths.sql'), 'r').read()


def main():
    """Main function, it is in charge of:
    * Query the database
    * Transform dataframes to strings
    * Assemble report
    * Send report to Telegram
    """    
    date =  pd.Timestamp.now().strftime('%A, %d %B %H:%M')
    # Today's Pending Jobs
    locksmiths_jobs_pending = utils_bot.df_locksmith_to_str( db.sql_to_df(LS_total_pending_jobs_by_locksmith_day))
    total_jobs_pending = utils_bot.trans_one_row(db.sql_to_df(LS_total_pending_jobs_day))

    # Today's Completed Jobs
    total_revenue = utils_bot.trans_one_row(db.sql_to_df(LS_total_revenue_day), money=True)
    total_jobs_completed = utils_bot.trans_one_row(db.sql_to_df(LS_total_completed_jobs_day))
    
    # Not maching locksmiths
    selected_vs_invoice_locksmiths = utils_bot.selected_vs_invoice_locksmiths(db.sql_to_df(LS_selected_vs_invoice_locksmiths))
    
    message = f"""{date}\n
*TODAY'S PENDING JOBS:*\n
{locksmiths_jobs_pending}\n
{total_jobs_pending}\n
*TODAY'S COMPLETED JOBS:*\n
{total_revenue}
{total_jobs_completed}\n
"""
    if selected_vs_invoice_locksmiths:
        message = message + f"""*DISCREPANCY FOUND:*\n
{selected_vs_invoice_locksmiths}"""
    logger.info(message)
    bot.send_message(GROUP_ID, message)
    
    if os.path.exists(LOCKSMITHS_REPORT_IMAGE):
        bot.send_photo(GROUP_ID, LOCKSMITHS_REPORT_IMAGE, 'Completed jobs summary')

if __name__ == '__main__':
    try:
        NOW = pd.Timestamp.now()
        hour = NOW.hour
        logger.info('Bot online')
        # Time validation to check if the hour is between 6 and 21
        if hour >= 6 and hour <= 21:
            main()
            logger.info('Process Successful')
        else:
            logger.info('Execution after hours')
        if os.path.exists(LOCKSMITHS_REPORT_IMAGE):
            os.remove(LOCKSMITHS_REPORT_IMAGE)
            logger.info('Locksmiths report image deleted')
    except Exception as e:
        logger.exception(e)