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
cols = [c for c in df.columns if any(k in c for k in [
    "top", "which other", "prefer"
])]

# Combine all brand mentions
brands = pd.concat([df[c].astype(str).str.lower() for c in cols])
brands = brands[~brands.str.contains("not|none|no idea|nan|disconnected", na=False)]

# Normalize brand names
def simplify(b):
    if any(k in b for k in ["haldiram", "haldiram’s"]):
        return "Haldiram"
    elif any(k in b for k in ["bikan", "bhikha"]):
        return "Bikaner / Bhikharam"
    elif "godesi" in b:
        return "GO DESi"
    elif any(k in b for k in ["local", "homemade", "store"]):
        return "Local / Homemade"
    elif any(k in b for k in ["amul", "anand", "rajpurohit", "astha", "kanthi", "nandhini", "gulab"]):
        return "Other Branded"
    else:
        return "Misc / Unknown"

brands = brands.apply(simplify)

# Count frequency safely
brand_counts = brands.value_counts().reset_index()
brand_counts.columns = ["Brand", "Mentions"]

# --- Bar Chart ---
plt.figure(figsize=(7,4))
bars = plt.barh(brand_counts["Brand"].iloc[:10], brand_counts["Mentions"].iloc[:10], color="#6A1B9A", height=0.55)
plt.bar_label(bars, fmt='%d', padding=4, fontsize=10, color="#fff", label_type="center")
plt.title("Packaged Sweet Brand Mentions", pad=15, weight="bold", color="#333")
plt.xlabel("Number of Mentions")
plt.ylabel("")
sns.despine(left=True, bottom=True)
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "sweets_brand_mentions.png"), dpi=300)
plt.close()

# --- Brand Split Chart ---
split_data = {
    "GO DESi": (brands == "GO DESi").sum(),
    "Haldiram": (brands == "Haldiram").sum(),
    "Bikaner / Bhikharam": (brands == "Bikaner / Bhikharam").sum(),
    "Local / Homemade": (brands == "Local / Homemade").sum(),
    "Others": len(brands) - (
        (brands == "GO DESi").sum() +
        (brands == "Haldiram").sum() +
        (brands == "Bikaner / Bhikharam").sum() +
        (brands == "Local / Homemade").sum()
    )
}
split_df = pd.DataFrame(list(split_data.items()), columns=["Category", "Mentions"])

plt.figure(figsize=(6,4))
sns.barplot(x="Category", y="Mentions", data=split_df, palette="plasma")
plt.title("Brand Preference Split", pad=15, weight="bold", color="#333")
plt.xticks(rotation=25, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "sweets_brand_split.png"), dpi=300)
plt.close()

print("✅ Saved: sweets_brand_mentions.png & sweets_brand_split.png")
