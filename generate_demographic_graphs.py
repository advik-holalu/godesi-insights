import pandas as pd
import matplotlib.pyplot as plt
import os

# === Setup ===
input_file = "Untitled spreadsheet.xlsx"
output_folder = "insightsgraphs"
os.makedirs(output_folder, exist_ok=True)

# === Read available sheet names ===
excel_file = pd.ExcelFile(input_file)
print("Available sheets:", excel_file.sheet_names)

# Try to identify the sheets automatically
popz_sheet = None
sweets_sheet = None

for sheet in excel_file.sheet_names:
    name_lower = sheet.lower()
    if "confection" in name_lower or "mint" in name_lower or "pop" in name_lower:
        popz_sheet = sheet
    elif "sweet" in name_lower:
        sweets_sheet = sheet

if not popz_sheet or not sweets_sheet:
    raise ValueError("Couldn't auto-detect Popz or Sweets sheet names. Please rename sheets clearly.")

print(f"Detected sheets → Popz: {popz_sheet} | Sweets: {sweets_sheet}")

# === Read the sheets ===
popz_df = pd.read_excel(input_file, sheet_name=popz_sheet)
sweets_df = pd.read_excel(input_file, sheet_name=sweets_sheet)

# Combine data
combined_df = pd.concat([popz_df, sweets_df], ignore_index=True)

# === Clean Columns ===
combined_df.columns = combined_df.columns.str.strip().str.lower()

# Identify column names dynamically
age_col = [c for c in combined_df.columns if "age" in c][0]
gender_col = [c for c in combined_df.columns if "gender" in c][0]
category_col = [c for c in combined_df.columns if "product" in c or "category" in c][0]

# === Plot 1: Age Distribution ===
age_counts = combined_df[age_col].value_counts(dropna=False).sort_index()
plt.figure(figsize=(6, 6))
age_counts.plot(kind="pie", autopct="%1.0f%%", startangle=90)
plt.title("Age Distribution of Respondents")
plt.ylabel("")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "age_distribution.png"), dpi=300)
plt.close()

# === Plot 2: Gender Split ===
gender_counts = combined_df[gender_col].value_counts(dropna=False)
plt.figure(figsize=(5, 5))
gender_counts.plot(kind="pie", autopct="%1.0f%%", startangle=90, colors=["#f9a825", "#81d4fa", "#cfd8dc"])
plt.title("Gender Split")
plt.ylabel("")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "gender_split.png"), dpi=300)
plt.close()

# === Plot 3: Product Category Split ===
category_counts = combined_df[category_col].value_counts(dropna=False)
plt.figure(figsize=(6, 4))
category_counts.plot(kind="bar", color="#f57c00")
plt.title("Product Category Split")
plt.xlabel("Product Category")
plt.ylabel("Number of Respondents")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "product_category_split.png"), dpi=300)
plt.close()

print("\n✅ Graphs generated successfully in:", output_folder)
