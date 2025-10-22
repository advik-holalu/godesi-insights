import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

input_file = "Untitled spreadsheet.xlsx"
output_folder = "insightsgraphs"
os.makedirs(output_folder, exist_ok=True)

# Read sheets
excel_file = pd.ExcelFile(input_file)
sheets = [s for s in excel_file.sheet_names if "sweet" in s.lower() or "mint" in s.lower() or "confection" in s.lower()]
df = pd.concat([pd.read_excel(input_file, sheet_name=s) for s in sheets], ignore_index=True)
df.columns = df.columns.str.strip().str.lower()

# Find column
col = [c for c in df.columns if "what is desi popz" in c][0]
df[col] = df[col].astype(str).str.lower().str.strip()

# Map categories
def categorize(x):
    if any(k in x for k in ["candy", "lollipop", "both"]):
        return "Candy / Lollipop"
    elif any(k in x for k in ["churan", "fresh", "digestive"]):
        return "Digestive / Mouth Freshener"
    elif any(k in x for k in ["tamarind", "popz", "unique"]):
        return "Novelty / Tamarind Pop"
    elif "not" in x or "no" in x or x in ["nan", "none", ""]:
        return "Unclear / Not Mentioned"
    else:
        return "Other"

df["Perceived_Category"] = df[col].apply(categorize)

# Count
counts = df["Perceived_Category"].value_counts()

# --- Donut Chart ---
colors = ["#F57C00", "#FFA726", "#FFE0B2", "#E0E0E0"]
fig, ax = plt.subplots(figsize=(5,5))
wedges, texts, autotexts = ax.pie(
    counts.values,
    labels=counts.index,
    autopct='%1.1f%%',
    startangle=90,
    colors=colors,
    textprops={'color':'#333333', 'fontsize':10}
)
centre_circle = plt.Circle((0,0),0.70,fc='white')
fig.gca().add_artist(centre_circle)
ax.set_title("What Do Consumers Think Desi Popz Is?", pad=15, weight="bold", color="#333333")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "perception_donut.png"), dpi=300)
plt.close()

print("✅ perception_donut.png saved in", output_folder)
