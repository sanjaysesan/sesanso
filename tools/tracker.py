import argparse
import json
import os
import sys
import datetime
import gspread
from dotenv import load_dotenv

load_dotenv()

def log_application(company, role, status, notes):
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
    sheet_name = os.environ.get("GOOGLE_SHEET_NAME", "Job Applications Tracker")
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Missing Google service account credentials at '{creds_path}'")
        
    gc = gspread.service_account(filename=creds_path)
    sh = gc.open(sheet_name)
    worksheet = sh.get_worksheet(0)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    worksheet.append_row([timestamp, company, role, status, notes])
    return {"status": "success", "logged": [timestamp, company, role, status]}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Log job application to Google Sheets")
    p.add_argument("--company", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--status", default="Applied")
    p.add_argument("--notes", default="")
    args = p.parse_args()
    
    try:
        res = log_application(args.company, args.role, args.status, args.notes)
        print(json.dumps(res, indent=2))
    except Exception as e:
        err_msg = str(e)
        # If it's just the gspread HTTP 200 response notice, treat it as a success
        if "<Response [200]>" in err_msg:
            print(json.dumps({"status": "success", "message": "Logged successfully to Google Sheet!"}, indent=2))
        else:
            print(json.dumps({"error": err_msg}, indent=2))
            sys.exit(1)