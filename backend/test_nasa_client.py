
from data.nasa_client import fetch_power_data

# Winnipeg coordinates
result = fetch_power_data(
    latitude=49.8951,
    longitude=-97.1384,
    start_year=2023,
    end_year=2024,
    parameters=["T2M", "RH2M"],
    temporal_resolution="hourly",
    community="RE",
)

print("Source:", result["source"])
print("Parameters:", result["parameters"])
print("Location:", result["latitude"], result["longitude"])

for parameter, measurements in result["data"].items():
    print(f"\n{parameter}")
    print("First five measurements:")

    for measurement in measurements[:5]:
        print(measurement)

    print("Total measurements:", len(measurements))
