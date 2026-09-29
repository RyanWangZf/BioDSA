#!/bin/sh
mkdir -p /app/submission
cat > /app/submission/analysis.py <<'PY'
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
df=pd.read_csv('/app/inputs/data_clinical_patient.csv')
groups={'CR':'Group 1','CRi':'Group 1','PR':'Group 2','SD':'Group 2','PD':'Group 3','Not evaluable':'Group 3'}
df['Response Group']=df['MORPHOLOGIC_RESPONSE'].map(groups)
filtered=df.dropna(subset=['Response Group'])
sns.stripplot(data=filtered,x='Response Group',y='AGE_AT_DIAGNOSIS',jitter=True)
plt.tight_layout(); plt.savefig('/app/submission/response_age.png'); plt.close()
means=filtered.groupby('Response Group')['AGE_AT_DIAGNOSIS'].mean()
mean_age1=means['Group 1']; mean_age2=means['Group 2']; mean_age3=means['Group 3']
PY
