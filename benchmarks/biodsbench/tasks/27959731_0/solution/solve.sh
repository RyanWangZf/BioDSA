#!/bin/sh
mkdir -p /app/submission
cat > /app/submission/analysis.py <<'PY'
import pandas as pd
df_clinical=pd.read_csv('/app/inputs/data_clinical_patient.csv')
output_df=df_clinical.groupby('SOURCE')['DISEASE'].value_counts().reset_index()
PY
