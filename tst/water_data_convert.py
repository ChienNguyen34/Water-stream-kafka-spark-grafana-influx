import pandas as pd
import json

# Đọc file BATADAL
df_water = pd.read_csv("dataset\BATADAL_dataset03.csv", nrows=100)

# Vì cột DATETIME có khoảng trắng thừa, ta nên strip() nó đi
df_water.columns = df_water.columns.str.strip()

# Lấy thử dòng đầu tiên chuyển thành JSON
sample_row = df_water.iloc[0].to_dict()
print("Sample Water JSON:", json.dumps(sample_row, indent=2))