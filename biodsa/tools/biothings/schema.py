"""Schemas for BioThings APIs data structures."""

from typing import Any
from pydantic import BaseModel, Field


class GeneInfo(BaseModel):
    """Gene information from MyGene.info."""

    gene_id: str = Field(alias="_id")
    symbol: str | None = None
    name: str | None = None
    summary: str | None = None
    alias: list[str] | None = Field(default_factory=list)
    entrezgene: int | str | None = None
    ensembl: dict[str, Any] | None = None
    refseq: dict[str, Any] | None = None
    type_of_gene: str | None = None
    taxid: int | None = None


class DiseaseInfo(BaseModel):
    """Disease information from MyDisease.info."""

    disease_id: str = Field(alias="_id")
    name: str | None = None
    mondo: dict[str, Any] | None = None
    definition: str | None = None
    synonyms: list[str] | None = Field(default_factory=list)
    xrefs: dict[str, Any] | None = None
    phenotypes: list[dict[str, Any]] | None = None


class DrugInfo(BaseModel):
    """Drug/chemical information from MyChem.info."""

    drug_id: str = Field(alias="_id")
    name: str | None = None
    tradename: list[str] | None = Field(default_factory=list)
    drugbank_id: str | None = None
    chebi_id: str | None = None
    chembl_id: str | None = None
    pubchem_cid: str | None = None
    unii: str | dict[str, Any] | None = None
    inchikey: str | None = None
    formula: str | None = None
    description: str | None = None
    indication: str | None = None
    pharmacology: dict[str, Any] | None = None
    mechanism_of_action: str | None = None


class GeneItem(BaseModel):
    """Individual gene item for search results."""
    gene_id: str = Field(description="Gene ID")
    symbol: str | None = Field(default=None, description="Gene symbol")
    name: str | None = Field(default=None, description="Gene name")
    summary: str | None = Field(default=None, description="Gene summary")
    alias: list[str] | None = Field(default_factory=list, description="Gene aliases")
    entrezgene: int | str | None = Field(default=None, description="Entrez gene ID")
    type_of_gene: str | None = Field(default=None, description="Type of gene")
    taxid: int | None = Field(default=None, description="Taxonomy ID")


class DiseaseItem(BaseModel):
    """Individual disease item for search results."""
    disease_id: str = Field(description="Disease ID")
    name: str | None = Field(default=None, description="Disease name")
    definition: str | None = Field(default=None, description="Disease definition")
    synonyms: list[str] | None = Field(default_factory=list, description="Disease synonyms")
    mondo_id: str | None = Field(default=None, description="MONDO ID")
    doid: str | None = Field(default=None, description="Disease Ontology ID")


class DrugItem(BaseModel):
    """Individual drug item for search results."""
    drug_id: str = Field(description="Drug ID")
    name: str | None = Field(default=None, description="Drug name")
    tradename: list[str] | None = Field(default_factory=list, description="Trade names")
    drugbank_id: str | None = Field(default=None, description="DrugBank ID")
    chebi_id: str | None = Field(default=None, description="ChEBI ID")
    chembl_id: str | None = Field(default=None, description="ChEMBL ID")
    pubchem_cid: str | None = Field(default=None, description="PubChem CID")
    inchikey: str | None = Field(default=None, description="InChI Key")
    formula: str | None = Field(default=None, description="Chemical formula")
    description: str | None = Field(default=None, description="Drug description")


class VariantInfo(BaseModel):
    """Variant information from MyVariant.info."""

    variant_id: str = Field(alias="_id")
    chrom: str | None = None
    pos: int | None = None
    ref: str | None = None
    alt: str | None = None
    rsid: str | None = None
    gene: dict[str, Any] | None = None
    clinvar: dict[str, Any] | None = None
    dbsnp: dict[str, Any] | None = None
    cadd: dict[str, Any] | None = None
    dbnsfp: dict[str, Any] | None = None
    cosmic: dict[str, Any] | None = None
    vcf: dict[str, Any] | None = None


class VariantItem(BaseModel):
    """Individual variant item for search results."""
    variant_id: str = Field(description="Variant ID (HGVS notation)")
    chrom: str | None = Field(default=None, description="Chromosome")
    pos: int | None = Field(default=None, description="Position")
    ref: str | None = Field(default=None, description="Reference allele")
    alt: str | None = Field(default=None, description="Alternate allele")
    rsid: str | None = Field(default=None, description="dbSNP rsID")
    gene_symbol: str | None = Field(default=None, description="Gene symbol")
    variant_type: str | None = Field(default=None, description="Type of variant")
    clinical_significance: str | None = Field(default=None, description="Clinical significance")