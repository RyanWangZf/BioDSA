# Set the CRAN repository (optional, but recommended for better performance)
options(repos = c(CRAN = "https://cloud.r-project.org/"))

# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
  install.packages("BiocManager")

# Install Bioconductor packages
BiocManager::install(c("org.Hs.eg.db", "pathview", "clusterProfiler", "biomaRt", "annotate"), ask = FALSE, force = TRUE)

# List of CRAN packages to install (excluding the ones installed by BiocManager)
packages <- c("readr", "jsonlite", "dplyr", "ggplot2", "survival", "survminer", 
              "factoextra", "tidyr", "cluster", "ggrepel", "pheatmap", "cowplot", 
              "png", "grid", "gridExtra", "AnnotationDbi", "enrichplot", 
              "lubridate", "stringr", "logger", "logging", "log4r", 
              "tibble", "NbClust", "DOSE", "data.table", 
              "RColorBrewer", "broom", "futile.logger", "logr")

# "tidyverse" keeps failed due to the system requirement not met 
# ggforestplot

# Install packages if not already installed
for (pkg in packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg)
  }
}

# Load all installed packages
lapply(packages, library, character.only = TRUE)

# Load Bioconductor packages installed via BiocManager
library(org.Hs.eg.db)
library(clusterProfiler)
library(pathview)

# error: clusterProfiler: bitr, enrichGO,
# org.Hs.eg.db

# Print a message to confirm the packages are installed and loaded
cat("The following packages are installed and loaded:\n")
cat(paste("- ", packages, "\n"))


