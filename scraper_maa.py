import requests
import pandas as pd
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import time

def get_clean_maa_data():
    url = "https://chennaiinternationalairport.com/api/flightsroute/getflightfeed"
    
    current_time_ms = int(time.time() * 1000)
    start_time_ms = current_time_ms - (24 * 60 * 60 * 1000)
    
    response = requests.get(url, params={"appname": "maa", "starttime": str(start_time_ms), "endtime": str(current_time_ms)})
    if response.status_code != 200: return pd.DataFrame()
    
    raw_json = response.json()
    flight_list = raw_json.get("flights", [])
    clean_data = []
    
    ist_zone = ZoneInfo("Asia/Kolkata")
    now = datetime.now(ist_zone)
    
    for flight in flight_list:
        sched_str = flight.get("scheduleDate")
        est_str = flight.get("estimatedDate")
        
        if sched_str and est_str:
            sched_dt = datetime.strptime(sched_str, "%Y-%m-%dT%H:%M:%S.000Z").replace(tzinfo=timezone.utc).astimezone(ist_zone)
            est_dt = datetime.strptime(est_str, "%Y-%m-%dT%H:%M:%S.000Z").replace(tzinfo=timezone.utc).astimezone(ist_zone)
            
            # GATEKEEPER: Only include flights that have actually landed
            if est_dt < now:
                delta_minutes = int((est_dt - sched_dt).total_seconds() / 60)
                
                clean_data.append({
                    "date": sched_dt.strftime("%Y-%m-%d"),
                    "airport_code": "MAA",
                    "origin_city": flight.get("originmap"), # Kept this!
                    "flight_number": flight.get("flightName"),
                    "scheduled_time": sched_dt.strftime("%H:%M"),
                    "actual_time": est_dt.strftime("%H:%M"),
                    "delta_minutes": delta_minutes
                })
    return pd.DataFrame(clean_data)

def update_csv_master_file(new_df, filepath="data/flights_data_maa.csv"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if os.path.exists(filepath):
        existing_df = pd.read_csv(filepath)
        combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['date', 'flight_number'], keep='last')
    else:
        combined_df = new_df
    combined_df.to_csv(filepath, index=False)

if __name__ == "__main__":
    df = get_clean_maa_data()
    if not df.empty: update_csv_master_file(df)