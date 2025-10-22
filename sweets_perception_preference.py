import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

input_file = "Untitled spreadsheet.xlsx"
output_folder = "insightsgraphs"
os.makedirs(output_folder, exist_ok=True)

# Read Sweets sheet
df = pd.read_excel(input_file, sheet_name="Sweets")
df.columns = df.columns.str.strip().str.lower()

# Identify relevant columns
brand_pref_col = [c for c in df.columns if "prefer" in c][0]
freq_col = [c for c in df.columns if "how often" in c][0]
occasion_col = [c for c in df.columns if "occasion" in c][0]
age_col = [c for c in df.columns if "age" in c][0]

# --- Normalize brand preference ---
df[brand_pref_col] = df[brand_pref_col].astype(str).str.lower()
def simplify_brand(b):
    if "haldiram" in b:
        return "Haldiram"
    elif "bikan" in b or "bhikha" in b:
        return "Bikaner / Bhikharam"
    elif "godesi" in b:
        return "GO DESi"
    elif "local" in b or "store" in b or "homemade" in b:
        return "Local / Homemade"
    elif "amul" in b or "anand" in b or "rajpurohit" in b or "kanthi" in b or "nandhini" in b:
        return "Other Branded"
    else:
        return "Misc / Unknown"

df["brand_category"] = df[brand_pref_col].apply(simplify_brand)

# --- Donut Chart: Brand Preference ---
brand_counts = df["brand_category"].value_counts()
plt.figure(figsize=(5,5))
colors = sns.color_palette("Set2", len(brand_counts))
plt.pie(brand_counts, labels=brand_counts.index, colors=colors, autopct="%1.0f%%", startangle=90, wedgeprops=dict(width=0.45))
plt.title("Packaged Sweets Brand Preference", pad=20, weight="bold", color="#333")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "sweets_brand_preference_donut.png"), dpi=300)
plt.close()

# --- Occasion × Frequency ---
df[occasion_col] = df[occasion_col].astype(str).str.lower().str.strip()
df[freq_col] = df[freq_col].astype(str).str.lower().str.strip()

# Clean major buckets
def simplify_occasion(o):
    if "festive" in o:
        return "Festive Time"
    elif "dessert" in o or "meal" in o:
        return "After Meals / Dessert"
    elif "craving" in o:
        return "Craving / Snack"
    elif "gift" in o:
        return "Gifting"
    else:
        return "Other / Not Mentioned"

def simplify_freq(f):
    if "daily" in f:
        return "Daily"
    elif "week" in f:
        return "Weekly"
    elif "occasion" in f or "rare" in f:
        return "Occasionally"
    elif "never" in f:
        return "Never"
    else:
        return "Other"

df["occasion_group"] = df[occasion_col].apply(simplify_occasion)
df["frequency_group"] = df[freq_col].apply(simplify_freq)

# Pivot
pivot = pd.crosstab(df["occasion_group"], df["frequency_group"])

plt.figure(figsize=(8,5))
sns.heatmap(pivot, annot=True, fmt="g", cmap="YlGnBu", linewidths=0.4)
plt.title("Occasion × Frequency of Sweet Consumption", pad=15, weight="bold", color="#333")
plt.xlabel("Consumption Frequency")
plt.ylabel("Occasion")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "sweets_occasion_frequency_heatmap.png"), dpi=300)
plt.close()

print("✅ Saved: sweets_brand_preference_donut.png & sweets_occasion_frequency_heatmap.png")

