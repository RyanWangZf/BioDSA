#!/bin/sh
mkdir -p /app/submission
cat > /app/submission/analysis.py <<'PY'
import pandas as pd
df_clinical=pd.read_csv('/app/inputs/data_clinical_patient.csv')
counts=df_clinical['MORPHOLOGIC_RESPONSE'].value_counts()
n_cr=counts['CR']; n_cri=counts['CRi']; n_or=n_cr+n_cri
PY
