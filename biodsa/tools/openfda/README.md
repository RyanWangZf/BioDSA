# OpenFDA API Client

Comprehensive Python client for accessing the FDA's openFDA drug databases, including drug approval information and product labeling data.

## Overview

This module provides two main APIs:

1. **Drug Approval API** (`drug.py`) - Search FDA-approved drug products from Drugs@FDA
2. **Drug Labeling API** (`product_labeling.py`) - Search structured product labeling (SPL) content

## Installation

The OpenFDA tools are part of the BioDSA package. Required dependencies:
- `requests` - HTTP client
- `pandas` - Data manipulation
- `pydantic` - Data validation

## Quick Start

```python
from biodsa.tools.openfda import (
    search_openfda_drugs,
    search_drug_labels,
    search_labels_by_drug_interaction,
)

# Search for discontinued drugs
df, summary = search_openfda_drugs(marketing_status="Discontinued", limit=10)

# Search for drug interactions with caffeine
df, summary = search_labels_by_drug_interaction("caffeine", limit=5)

# Search for diabetes treatments
df, summary = search_drug_labels(indications_and_usage="type 2 diabetes", limit=10)
```

## Drug Approval API

### Available Functions

#### `search_openfda_drugs()`
Search for FDA-approved drug products.

**Parameters:**
- `search_term` - General search term across all fields
- `application_number` - NDA, ANDA, or BLA number
- `brand_name` - Brand or trade name
- `generic_name` - Generic name(s)
- `manufacturer_name` - Manufacturer name
- `marketing_status` - Status (e.g., "Prescription", "Discontinued", "OTC")
- `product_number` - Product number
- `route` - Route of administration (e.g., "ORAL", "INTRAVENOUS")
- `substance_name` - Active ingredient name
- `limit` - Max results (1-1000, default: 100)
- `skip` - Pagination offset
- `save_path` - Optional CSV save path

**Returns:** `(DataFrame, summary_string)`

**Example:**
```python
# Find oral formulations of aspirin
df, summary = search_openfda_drugs(
    substance_name="ASPIRIN",
    route="ORAL",
    limit=20
)
```

#### `fetch_openfda_drug_by_application()`
Fetch drug details by application number.

**Parameters:**
- `application_number` - The NDA/ANDA/BLA number
- `save_path` - Optional CSV save path

**Example:**
```python
df, summary = fetch_openfda_drug_by_application("NDA021462")
```

#### Convenience Functions

- `search_drugs_by_status(marketing_status, limit, skip, save_path)`
- `search_drugs_by_ingredient(substance_name, limit, skip, save_path)`
- `search_drugs_by_route(route, limit, skip, save_path)`

## Drug Labeling API

### Available Functions

#### `search_drug_labels()`
Search structured product labeling content.

**Parameters:**

*Label Content Fields:*
- `indications_and_usage` - Search indications section
- `dosage_and_administration` - Search dosage section
- `contraindications` - Search contraindications
- `warnings` - Search warnings section
- `adverse_reactions` - Search adverse reactions
- `drug_interactions` - Search drug interactions
- `boxed_warning` - Search black box warnings
- `mechanism_of_action` - Search mechanism section
- `pharmacokinetics` - Search PK section
- `pharmacodynamics` - Search PD section
- `clinical_pharmacology` - Search clinical pharm section
- `clinical_studies` - Search clinical studies
- `overdosage` - Search overdosage section
- `description` - Search description section

*OpenFDA Standardized Fields:*
- `brand_name` - Brand name
- `generic_name` - Generic name
- `substance_name` - Active ingredient
- `manufacturer_name` - Manufacturer
- `product_type` - Product type
- `route` - Route of administration
- `application_number` - NDA/ANDA/BLA number

*Other:*
- `search_term` - General search across all fields
- `limit` - Max results (1-1000, default: 100)
- `skip` - Pagination offset
- `save_path` - Optional JSON save path

**Returns:** `(DataFrame, summary_string)`

**Example:**
```python
# Find PDE4 inhibitors for COPD
df, summary = search_drug_labels(
    mechanism_of_action="PDE4",
    indications_and_usage="COPD",
    limit=10
)
```

#### `fetch_drug_label_by_id()`
Fetch complete label by set ID.

**Parameters:**
- `set_id` - The label set ID (UUID)
- `save_path` - Optional JSON save path

**Returns:** `(label_dict, summary_string)`

#### Convenience Functions

- `search_labels_by_drug_interaction(interaction_term, limit, skip, save_path)`
- `search_labels_by_adverse_reaction(reaction_term, limit, skip, save_path)`
- `search_labels_by_indication(indication_term, limit, skip, save_path)`
- `search_labels_by_mechanism(mechanism_term, limit, skip, save_path)`
- `search_labels_with_boxed_warning(warning_term, limit, skip, save_path)`

## Usage Examples

### Example 1: Research Drug Interactions

```python
from biodsa.tools.openfda import search_labels_by_drug_interaction

# Find all drugs that interact with warfarin
df, summary = search_labels_by_drug_interaction("warfarin", limit=20)

# Examine the interactions
for idx, row in df.iterrows():
    if row['brand_name']:
        print(f"{row['brand_name']}: {row['drug_interactions'][:200]}...")
```

### Example 2: Find Drugs with Safety Warnings

```python
from biodsa.tools.openfda import search_labels_with_boxed_warning

# Find drugs with black box warnings about suicide risk
df, summary = search_labels_with_boxed_warning("suicide", limit=10)

for idx, row in df.iterrows():
    print(f"{row['brand_name']} - WARNING: {row['boxed_warning'][:150]}...")
```

### Example 3: Research Specific Drug Class

```python
from biodsa.tools.openfda import search_drug_labels, search_openfda_drugs

# Step 1: Find PDE4 inhibitors in labels
label_df, _ = search_drug_labels(
    mechanism_of_action="PDE4 inhibitor",
    indications_and_usage="COPD",
    limit=5
)

# Step 2: Get approval details
for substance in label_df['substance_name'].dropna().unique():
    drug_df, _ = search_openfda_drugs(substance_name=substance, limit=1)
    if not drug_df.empty:
        print(f"Drug: {drug_df.iloc[0]['brand_name']}")
        print(f"Application: {drug_df.iloc[0]['application_number']}")
        print(f"Status: {drug_df.iloc[0]['marketing_status']}")
```

### Example 4: Comprehensive Drug Profile

```python
from biodsa.tools.openfda import search_openfda_drugs, search_drug_labels

drug_name = "Lipitor"

# Get approval information
approval_df, _ = search_openfda_drugs(brand_name=drug_name, limit=1)

# Get labeling information
label_df, _ = search_drug_labels(brand_name=drug_name, limit=1)

if not approval_df.empty and not label_df.empty:
    approval = approval_df.iloc[0]
    label = label_df.iloc[0]
    
    print(f"Drug: {approval['brand_name']}")
    print(f"Generic: {approval['generic_name']}")
    print(f"Application: {approval['application_number']}")
    print(f"Status: {approval['marketing_status']}")
    print(f"\nIndications: {label['indications_and_usage'][:300]}...")
    print(f"\nWarnings: {label['warnings'][:300]}...")
```

### Example 5: Save Results for Analysis

```python
from biodsa.tools.openfda import search_drug_labels

# Search and save comprehensive diabetes drug data
df, summary = search_drug_labels(
    indications_and_usage="type 2 diabetes",
    limit=100,
    save_path="/tmp/diabetes_drugs.json"
)

print(f"Saved {len(df)} drug labels to /tmp/diabetes_drugs.json")
```

## Data Structure

### Drug Approval Data (DataFrame columns)

- `application_number` - NDA/ANDA/BLA number
- `application_type` - NDA, ANDA, or BLA
- `sponsor_name` - Sponsor/applicant name
- `brand_name` - Brand name(s)
- `generic_name` - Generic name(s)
- `manufacturer_name` - Manufacturer(s)
- `substance_name` - Active ingredient(s)
- `marketing_status` - Marketing status
- `dosage_form` - Dosage form
- `route` - Administration route(s)
- `product_number` - Product number(s)

### Drug Labeling Data (DataFrame columns)

- `id` - Document ID
- `set_id` - Set ID (stable across versions)
- `effective_time` - Label effective date
- `brand_name` - Brand name(s)
- `generic_name` - Generic name(s)
- `substance_name` - Active ingredient(s)
- `manufacturer_name` - Manufacturer(s)
- `route` - Administration route(s)
- `application_number` - NDA/ANDA/BLA number(s)
- `indications_and_usage` - Indications text
- `dosage_and_administration` - Dosage text
- `contraindications` - Contraindications text
- `warnings` - Warnings text
- `adverse_reactions` - Adverse reactions text
- `drug_interactions` - Drug interactions text
- `boxed_warning` - Black box warning text

## API Limits

- Maximum results per query: 1000
- No API key required
- Rate limits apply (be respectful with requests)
- Use pagination (`skip` parameter) for large result sets

## Error Handling

All functions return a tuple of `(DataFrame, summary_string)`. If an error occurs:
- DataFrame will be empty
- Summary string will contain error message

```python
df, summary = search_openfda_drugs(brand_name="NonexistentDrug")
if df.empty:
    print(f"Error or no results: {summary}")
```

## Advanced Search Syntax

The OpenFDA API supports advanced query syntax:

```python
# AND operator (default)
search_drug_labels(
    drug_interactions="warfarin",
    warnings="bleeding"
)

# Search for existence of field
search_drug_labels(search_term="_exists_:boxed_warning")

# Exact match
search_openfda_drugs(brand_name="Lipitor")  # Uses exact match internally
```

## Resources

- **OpenFDA Documentation**: https://open.fda.gov/apis/
- **Drugs@FDA API**: https://open.fda.gov/apis/drug/drugsfda/
- **Drug Labeling API**: https://open.fda.gov/apis/drug/label/
- **Query Syntax**: https://open.fda.gov/apis/query-syntax/

## Notes

- Label content may be very long. DataFrame truncates to 500 characters for display.
- Save as JSON (not CSV) for complete label content.
- Some drugs may have multiple labels for different formulations.
- Historical data is available for discontinued drugs.

## Support

For issues or questions:
1. Check the OpenFDA documentation
2. Review the examples in `examples_openfda_usage.py`
3. Consult the API reference at https://open.fda.gov/

## License

This client is part of the BioDSA project. OpenFDA data is provided by the FDA and is in the public domain.

