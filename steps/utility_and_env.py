import random

def _word():
    return random.choice([
        "N/A",
        "Not applicable",
        "No issue",
        "Standard operation",
        "Handled by contractor",
        "According to plan",
        "See attached document",
        "Controlled and monitored",
        "Comply with regulations",
        "On-site management",
    ])

def field_override(code):
    if code == "transport_mode":
        return random.choice([
            "Truck",
            "Container truck",
            "Pickup",
            "Van",
            "Motorbike",
        ])

    if code == "dump_location":
        return random.choice([
            "Designated municipal landfill",
            "Approved disposal site",
            "On-site temporary storage (approved)",
        ])

    if code == "noise_source":
        return random.choice([
            "Machinery operation",
            "Generators",
            "Vehicle movement",
            "Construction activities",
        ])

    if code == "clearing_land":
        return random.choice([
            "No land clearing required",
            "Minor clearing within site boundary",
            "Clearing done with approval",
        ])

    if code in {
        "staff_accom_health_and_safety",
        "staff_accom_sanitation",
        "staff_accom_solids_waste_management",
    }:
        return _word()

    return None
