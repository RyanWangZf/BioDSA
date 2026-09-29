#!/bin/sh
mkdir -p /app/submission
cat > /app/submission/analysis.py <<'PY'
import pandas as pd
df_mutation=pd.read_csv('/app/inputs/data_mutations.csv')
df_sample=pd.read_csv('/app/inputs/data_clinical_sample.csv')
sample_ids=df_mutation[df_mutation['Hugo_Symbol']=='TP53']['Tumor_Sample_Barcode']
n=df_sample.set_index('SAMPLE_ID').loc[sample_ids]['PATIENT_ID'].nunique()
PY
