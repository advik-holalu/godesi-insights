import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# === Setup ===
input_file = "Untitled spreadsheet.xlsx"
output_folder = "insightsgraphs"
os.makedirs(output_folder, exist_ok=True)

# === Read and combine sheets ===
excel_file = pd.ExcelFile(input_file)
sheets = [s for s in excel_file.sheet_names if "sweet" in s.lower() or "mint" in s.lower() or "confection" in s.lower()]
df = pd.concat([pd.read_excel(input_file, sheet_name=s) for s in sheets], ignore_index=True)

# === Clean columns ===
df.columns = df.columns.str.strip().str.lower()

# === Identify relevant columns ===
age_col = [c for c in df.columns if "age" in c][0]
discovery_col = [c for c in df.columns if "hear" in c and "popz" in c][0]

# === Clean data ===
df[age_col] = df[age_col].astype(str).str.strip()
df[discovery_col] = df[discovery_col].astype(str).str.strip()

# === Create pivot for heatmap ===
pivot = pd.crosstab(df[age_col], df[discovery_col])

# === Plot ===
plt.figure(figsize=(10,5))
sns.heatmap(pivot, annot=True, fmt="g", cmap="YlGnBu")
plt.title("Age Group vs Discovery Channel of Desi Popz")
plt.xlabel("Discovery Channel")
plt.ylabel("Age Group")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

# === Save ===
plt.savefig(os.path.join(output_folder, "age_vs_discovery_heatmap.png"), dpi=300)
plt.close()

print("✅ age_vs_discovery_heatmap.png saved in", output_folder)

