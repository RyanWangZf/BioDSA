"""OpenFDA API functions for drug information retrieval.

This module provides functions to search and retrieve drug information from the
OpenFDA Drugs@FDA database and drug product labeling information.
"""

__all__ = [
    # Drug approval functions
    "search_openfda_drugs",
    "fetch_openfda_drug_by_application",
    "search_drugs_by_status",
    "search_drugs_by_ingredient",
    "search_drugs_by_route",
    # Drug labeling functions
    "search_drug_labels",
    "fetch_drug_label_by_id",
    "search_labels_by_drug_interaction",
    "search_labels_by_adverse_reaction",
    "search_labels_by_indication",
    "search_labels_by_mechanism",
    "search_labels_with_boxed_warning",
]

from .drug import (
    search_openfda_drugs,
    fetch_openfda_drug_by_application,
    search_drugs_by_status,
    search_drugs_by_ingredient,
    search_drugs_by_route,
)

from .product_labeling import (
    search_drug_labels,
    fetch_drug_label_by_id,
    search_labels_by_drug_interaction,
    search_labels_by_adverse_reaction,
    search_labels_by_indication,
    search_labels_by_mechanism,
    search_labels_with_boxed_warning,
)

