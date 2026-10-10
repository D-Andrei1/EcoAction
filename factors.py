""" factors.py - emissions factor sets. The numbers the whole app is built on. PROVIDED COMPLETE - type it in exactly and do not change it.
How a saving is worked out:
    kg CO2e saved = quantity x (baseline factor - alternative factor)
e.g. cycling 8 km instead of driving = 8 x (0.16272 - 0) = 1.30176 -> 1.30 kg
NEVER edit a factor set that is already in use. To change numbers, add a NEW version and make it ACTIVE_VERSION. Old actions keep the version they were calculated with. """

ACTIVE_VERSION = "uk-2025.1" 

CATEGORIES = [("transport", "Transport"), ("energy", "Energy"), ("waste", "Waste"), ("food", "Food")] 

CAR_KM = 0.16272   # DESNZ 2025: average car, unknown fuel, kg CO2e per km

FACTOR_SETS = {
    "uk-2025.1": {
        "source": ("UK Government GHG Conversion Factors for Company Reporting (DESNZ): "
                   "2025 edition for transport, electricity and gas; 2024 edition for waste disposal."),
        "types": {
            # ----- transport: kg CO2e per km, compared with driving an average car -----
            "walking": {"category": "transport", "label": "Walked instead of driving", "unit": "km",
                        "baseline": CAR_KM, "alternative": 0.0, "typical_max": 30},
            "cycling": {"category": "transport", "label": "Cycled instead of driving", "unit": "km",
                        "baseline": CAR_KM, "alternative": 0.0, "typical_max": 100},             "bus": {"category": "transport", "label": "Took the bus instead of driving", "unit": "km",
                    "baseline": CAR_KM, "alternative": 0.10385, "typical_max": 150},             "coach": {"category": "transport", "label": "Took a coach instead of driving", "unit": "km",
                      "baseline": CAR_KM, "alternative": 0.02776, "typical_max": 500},
            "train": {"category": "transport", "label": "Took the train instead of driving", "unit": "km",
                      "baseline": CAR_KM, "alternative": 0.03546, "typical_max": 800},
            "tram": {"category": "transport", "label": "Took the tram instead of driving", "unit": "km",
                     "baseline": CAR_KM, "alternative": 0.02860, "typical_max": 60},
            "underground": {"category": "transport", "label": "Took the Underground instead of driving",
                            "unit": "km", "baseline": CAR_KM, "alternative": 0.02780, "typical_max": 60},
            # ----- energy: kg CO2e per kWh not used -----
            "electricity_saved": {"category": "energy", "label": "Used less electricity", "unit": "kWh",
                                    "baseline": 0.177, "alternative": 0.0, "typical_max": 100},
                "gas_saved": {"category": "energy", "label": "Used less gas (heating or cooking)", "unit": "kWh",
                              "baseline": 0.18296, "alternative": 0.0, "typical_max": 300},
            # ----- waste: kg CO2e per kg kept out of landfill -----
            "paper_recycled": {"category": "waste", "label": "Recycled paper or card", "unit": "kg",
                               "baseline": 1.164, "alternative": 0.0, "typical_max": 25},
            "plastic_recycled": {"category": "waste", "label": "Recycled plastic", "unit": "kg",
                                 "baseline": 0.009, "alternative": 0.0, "typical_max": 25},
            "cans_recycled": {"category": "waste", "label": "Recycled cans", "unit": "kg",
                              "baseline": 0.009, "alternative": 0.0, "typical_max": 25},
            "general_waste_cut": {"category": "waste", "label": "Put less in the general waste bin",
                                  "unit": "kg", "baseline": 0.497, "alternative": 0.0, "typical_max": 25},
            # ----- food: kg CO2e per kg of food not thrown away -----
            "food_not_wasted": {"category": "food", "label": "Ate or shared food instead of binning it",
            "unit": "kg", "baseline": 0.497, "alternative": 0.0, "typical_max": 10},
        },
    },
    # Illustrative set used ONLY by the worked examples and tests in the documentation.
    "v1.2": {
        "source": "Illustrative numbers for examples and tests only - not for real users.",
        "types": {
        "cycling": {"category": "transport", "label": "Cycled instead of driving", "unit": "km",
                    "baseline": 0.2, "alternative": 0.0, "typical_max": 100},
        "walking": {"category": "transport", "label": "Walked instead of driving", "unit": "km",
                    "baseline": 0.2, "alternative": 0.0, "typical_max": 30},
        },
    },
}

def get_type(action_type, version=None):
    """The factor details for one action type, or None if it doesn't exist in that version."""
    factor_set = FACTOR_SETS.get(version or ACTIVE_VERSION)
    if factor_set is None:
        return None
    return factor_set["types"].get(action_type)

def factor(details):
    """kg CO2e saved per unit (baseline minus alternative)."""
    return round(details["baseline"] - details["alternative"], 5)

def types_in(category, version=None):
    """[(action_type, details), ...] for one category, in the order listed above."""
    factor_set = FACTOR_SETS[version or ACTIVE_VERSION]
    return [(key, d) for key, d in factor_set["types"].items() if d["category"] == category]