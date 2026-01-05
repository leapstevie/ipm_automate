# steps/invt_info.py

import os
import random
from datetime import datetime, timedelta

from api.upload import upload_temp_attachment


# ======================================================
# HELPERS
# ======================================================

def random_file(folder="picture_automate"):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abs_folder = os.path.abspath(os.path.join(base_dir, folder))
    if not os.path.isdir(abs_folder):
        raise Exception(f"Folder not found: {abs_folder}")

    files = [
        f for f in os.listdir(abs_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    if not files:
        raise Exception(f"No images found in {abs_folder}/")

    return os.path.join(abs_folder, random.choice(files))


def generate_timeline(context):
    
    if context.get("_timeline_ready"):
        return


    start = datetime.now().date() + timedelta(days=7)
 
    end = start + timedelta(days=random.randint(30, 120))
  
    eq = end + timedelta(days=random.randint(7, 45))
   
    prod = eq + timedelta(days=random.randint(7, 45))

    context["construction_start_datetime"] = start.isoformat()
    context["construction_end_datetime"] = end.isoformat()
    context["equipping_start_datetime"] = eq.isoformat()
    context["production_start_datetime"] = prod.isoformat()
    context["_timeline_ready"] = True


# ======================================================
# FIELD OVERRIDE LOGIC FOR invt_info
# ======================================================

def field_override(code, context=None):
    if context is None:
        context = {}

    # 1) Company name (Khmer / English)
    if code == "investment_target_km":
        return random.choice([
            "ក្រុមហ៊ុន ខេមបូឌា ឧស្សាហកម្ម",
            "ក្រុមហ៊ុន អភិវឌ្ឍន៍ ឧស្សាហកម្ម",
            "ក្រុមហ៊ុន សេដ្ឋកិច្ច កម្ពុជា",
            "ក្រុមហ៊ុន វិនិយោគ ឧស្សាហកម្ម",
            "ក្រុមហ៊ុន ផលិតកម្ម កម្ពុជា",
            "ក្រុមហ៊ុន បច្ចេកវិទ្យា ឧស្សាហកម្ម",
            "ក្រុមហ៊ុន ស្ថាបត្យកម្ម កម្ពុជា",
            "ក្រុមហ៊ុន អភិវឌ្ឍន៍ សេដ្ឋកិច្ច",
            "ក្រុមហ៊ុន ផលិតផល កម្ពុជា",
            "ក្រុមហ៊ុន វិស័យ ឧស្សាហកម្ម"
        ])

    if code == "investment_target_en":
        return random.choice([
            "Cambodia Industrial Corporation",
            "Cambodia Development Industries",
            "Khmer Economic Ventures",
            "Cambodia Manufacturing Group",
            "Indo-Khmer Industrial Co.",
            "Cambodia Tech Industries",
            "Mekong Industrial Holdings",
            "Cambodia Growth Corporation",
            "Khmer Production Enterprises",
            "Cambodia Sector Industries"
        ])
    
    if code == "investment_output_market":
        return random.choice([
           "United States", "Canada", "Germany", "France", "Australia",
           "Vietnam", "Thailand", "Japan", "South Korea", "China",
        ])
    
    if code == "total_investment_capital":
        total = (
            float(context.get("construction_cost", 0) or 0) +
            float(context.get("building_cost", 0) or 0) +
            float(context.get("equipment_production_cost", 0) or 0) +
            float(context.get("equipment_stationery_cost", 0) or 0) +
            float(context.get("equipment_other_cost", 0) or 0)
        )
    
        return round(total, 2)

    if code == "invt_info_incentive_label":
        return None
    
    if code in {
        "construction_start_datetime",
        "construction_end_datetime",
        "equipping_start_datetime",
        "production_start_datetime",
    }:
        generate_timeline(context)
        return context.get(code)

    if code == "sez_and_industrial_park_code":
        return "Vattanak I Industrial Park"

    if code in {
        "location_document_info_attachment_id",
        "building_plan_info_attachment_id",
    }:
        return upload_temp_attachment(random_file())

    return None
