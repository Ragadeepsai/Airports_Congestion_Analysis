import requests
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_all_bom_arrivals():
    url = "https://csmia-mumbai.adaniairports.com/api/sitecore/FlightStatus/Search"
    today_str = datetime.now().strftime("%Y-%m-%dT00:00:00")
    
    headers = {
        "User-Agent": "AAI-StudentPortfolioProject/1.0",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Referer": "https://csmia-mumbai.adaniairports.com/en/flight-status"
    }
    
    clean_data = []
    page_number = 1
    
    print("Starting Mumbai (BOM) extraction loop...")
    
    # 1. The Pagination Loop
    while True:
        payload = {
            "Terminal": "0",
            "Date": today_str,
            "SearchText": "",
            "PageNumber": str(page_number),
            "IsLoadMore": True, 
            "DataSourceId": "{A2727810-F569-400C-A80A-91967CCC6366}",
            "ServiceType": "Passenger",
            "TabName": "A",
            "timeslot": ""
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"Failed to fetch page {page_number}. Breaking loop.")
            break
            
        raw_html = response.json().get("FlightHtml", "")
        soup = BeautifulSoup(raw_html, 'html.parser')
        flight_rows = soup.find_all("div", class_="flightListRow")
        
        if len(flight_rows) == 0:
            print(f"Page {page_number} is empty. Finished scraping!")
            break
            
        print(f"Scraping page {page_number} ({len(flight_rows)} flights found)...")
        
        for row in flight_rows:
            columns = row.find_all("div", class_="flightListCol")
            if len(columns) >= 6:
                
                # 2. The Time Split Logic
                time_text = columns[0].text.split()
                if len(time_text) >= 2:
                    scheduled_time = time_text[0]
                    actual_time = time_text[1]
                elif len(time_text) == 1:
                    scheduled_time = time_text[0]
                    actual_time = time_text[0]
                else:
                    continue
                
                airline_tag = columns[1].find("label")
                airline = airline_tag.text.strip() if airline_tag else "Unknown"
                
                h6_tag = columns[1].find("h6")
                origin_city = h6_tag.text.replace(airline, "").strip() if (h6_tag and airline_tag) else "Unknown"
                
                flight_number = " ".join(columns[2].text.split()).replace("Flight No", "").strip()
                status = " ".join(columns[5].text.split())
                
                if "Arrived" in status or "On Time" in status:
                    sched_dt = datetime.strptime(scheduled_time, "%H:%M")
                    act_dt = datetime.strptime(actual_time, "%H:%M")
                    
                    delta_minutes = int((act_dt - sched_dt).total_seconds() / 60)
                    
                    if delta_minutes > 1000: delta_minutes -= 1440
                    elif delta_minutes < -1000: delta_minutes += 1440
                    
                    if delta_minutes <= -10: classification = "Early"
                    elif delta_minutes >= 15: classification = "Late"
                    else: classification = "On-Time"
                    
                    clean_data.append({
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "airport_code": "BOM",
                        "origin_city": origin_city,
                        "airline": airline,
                        "flight_number": flight_number,
                        "scheduled_time": scheduled_time,
                        "actual_time": actual_time,
                        "delta_minutes": delta_minutes,
                        "classification": classification,
                        "arrival_status": status
                    })
        page_number += 1

    return pd.DataFrame(clean_data)

def update_csv_master_file(new_df, filepath="data/flights_data_bom.csv"):
    print(f"Saving data to {filepath}...")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    if os.path.exists(filepath):
        existing_df = pd.read_csv(filepath)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        # Deduplication ensures we keep only the most recent status per flight per day
        combined_df = combined_df.drop_duplicates(subset=["date", "flight_number"], keep="last")
    else:
        combined_df = new_df
        
    combined_df.to_csv(filepath, index=False)
    print(f"Master file updated! Total records: {len(combined_df)}")

if __name__ == "__main__":
    df = scrape_all_bom_arrivals()
    if not df.empty:
        update_csv_master_file(df)