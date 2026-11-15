"""Shared constants for the NYC 311 data-quality layer."""
import numpy as np

COLS = ["unique_key", "created_date", "closed_date", "agency", "complaint_type", "descriptor", "incident_zip", "incident_address",
        "borough", "city", "status", "resolution_description", "latitude", "longitude"]
NUMERIC_COLS = {"unique_key": "i", "latitude": "f", "longitude": "f"}
REQUIRED = ["unique_key", "created_date", "agency", "complaint_type", "borough"]
ISO_RE = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$"
ISO_FMT = "%Y-%m-%dT%H:%M:%S.000"
ALT_FMT = "%m/%d/%Y %I:%M:%S %p"
ZIP3_BORO = {"100": "MANHATTAN", "101": "MANHATTAN", "102": "MANHATTAN", "103": "STATEN ISLAND", "104": "BRONX", "112": "BROOKLYN",
             "110": "QUEENS", "111": "QUEENS", "113": "QUEENS", "114": "QUEENS", "116": "QUEENS"}
BBOX = (40.45, 40.95, -74.30, -73.65)     # lat_min, lat_max, lon_min, lon_max (NYC)
BORO_ZIPS = {"MANHATTAN": ["10001", "10002", "10003", "10011", "10025", "10027", "10029", "10036"],
             "BRONX": ["10451", "10452", "10456", "10458", "10467", "10468"],
             "BROOKLYN": ["11201", "11206", "11211", "11221", "11226", "11234", "11215"],
             "QUEENS": ["11101", "11354", "11368", "11373", "11375", "11432", "11385"],
             "STATEN ISLAND": ["10301", "10304", "10306", "10312"]}
BORO_BOX = {"MANHATTAN": (40.70, 40.88, -74.02, -73.93), "BRONX": (40.80, 40.91, -73.93, -73.78), "BROOKLYN": (40.57, 40.70, -74.04, -73.86),
            "QUEENS": (40.55, 40.79, -73.96, -73.70), "STATEN ISLAND": (40.50, 40.64, -74.25, -74.05)}
AGENCY_COMPLAINTS = {
    "NYPD": {"Noise - Residential": ["Loud Music/Party", "Banging/Pounding", "Loud Talking"], "Illegal Parking": ["Blocked Hydrant", "Double Parked Vehicle", "Posted Parking Sign Violation"],
             "Blocked Driveway": ["No Access", "Partial Access"]},
    "HPD": {"HEAT/HOT WATER": ["ENTIRE BUILDING", "APARTMENT ONLY"], "PLUMBING": ["WATER LEAK", "TOILET", "BATHTUB/SHOWER"],
            "PAINT/PLASTER": ["CEILING", "WALLS"], "UNSANITARY CONDITION": ["PESTS", "MOLD"]},
    "DOT": {"Street Condition": ["Pothole", "Cave-in"], "Traffic Signal Condition": ["Controller", "Defective Hardware"], "Street Light Condition": ["Street Light Out", "Lamp Missing"]},
    "DSNY": {"Missed Collection": ["Missed Recycling", "Missed Garbage"], "Dirty Condition": ["Dirty Sidewalk", "Litter Basket Full"]},
    "DEP": {"Water System": ["Leak", "Low Pressure"], "Sewer": ["Catch Basin Clogged", "Backup"]},
    "DOHMH": {"Rodent": ["Rat Sighting", "Mouse Sighting"], "Food Establishment": ["Unsanitary", "Illness"]},
    "DPR": {"Damaged Tree": ["Branch Cracked", "Tree Down"], "Overgrown Tree/Branches": ["Branches Hitting Building", "Obstructing Sign"]},
    "DOB": {"General Construction/Plumbing": ["Work Without Permit", "Failure To Maintain"], "Building/Use": ["Illegal Conversion", "Certificate Of Occupancy"]},
    "TLC": {"For Hire Vehicle Complaint": ["Driver Complaint", "Vehicle Condition"]},
}
AGENCY_W = {"NYPD": .30, "HPD": .25, "DOT": .10, "DSNY": .10, "DEP": .07, "DOHMH": .05, "DPR": .05, "DOB": .05, "TLC": .03}
CLOSED_RES = ["The {a} responded to the complaint and took action to fix the condition.", "The {a} inspected the location and the complaint was closed.",
              "The {a} reviewed the complaint and found no violation."]
OPEN_RES = ["The {a} has been notified and will review your complaint.", "Your request has been assigned to the {a} and is pending."]
CLOSED_WORDS = ("responded to", "was closed", "found no violation", "took action", "has been resolved", "completed")
OPEN_WORDS = ("will review", "is pending", "has been assigned", "has been notified", "will be")
