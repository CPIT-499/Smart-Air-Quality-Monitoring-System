import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

def run_test():
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": 21.4901,
        "longitude": 39.1862,
        "hourly": ["pm10", "pm2_5", "carbon_monoxide", "carbon_dioxide"]
    }
    response = openmeteo.weather_api(url, params=params)[0]

    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    hourly = response.Hourly()
    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "pm10": hourly.Variables(0).ValuesAsNumpy(),
        "pm2_5": hourly.Variables(1).ValuesAsNumpy(),
        "carbon_monoxide": hourly.Variables(2).ValuesAsNumpy(),
        "carbon_dioxide": hourly.Variables(3).ValuesAsNumpy()
    }

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    print(hourly_dataframe)

if __name__ == "__main__":
    run_test()
