# Organization Name Standardization Process

## Overview
This Python project develops a process for **standardizing raw organizational names** to improve **entity matching** across multiple datasets. By using a combination of **string cleaning**, **regular expressions**, and **hashing functions**, the goal is to create a large **crosswalk table**

The work is currently implemented and tested within a **Jupyter notebook** for simplied use
> Note: This notebook is still under development. Several functions and matching methods need refinement and expansion

---

## Objectives
* Clean and normalize raw organization names from various datasets.
* Eliminate common textual noise, legal suffixes, punctuation, and inconsistent capitalization
* Map variations of the same organization based on standardized names or other unique keys
* Create a crosswalk table that aligns entities across multiple datasets (canonical key, raw name / aliases, sources, CIK ID, match type)
  * CIK (Central Index Key) is one way we can automatically match entities. They are used on the Securities Exchange Commission's (SEC) computer systems to identify corporations and individual people who have filed disclosure with the SEC.

## Information About the Datasets
* CIK.csv
  * 870051 entities
  * Columns: "company_name", "cik"
* SEC_Institutions.csv
  * 13737 entities
  * Columns: "CIK", "Ticker", "Name", "Exchange", "SIC", "Business", "Incorporated", "IRS"
  * It has been tested that all the entities in SEC are already in CIK, so further matching wiht SEC can be stopped. 
* compustat_clean.csv
  * 19581 entities
  * Columns: "gvkey", "conm", "tic", "cusip", "cik", "sic", "naics", "gsubind", "gind", "year1", "year2"
* FDIC_clean.csv
  * 25670 entities
  * Columns: "NAME", "NAMEHCR", "STALP", "STNAME", "BKCLASS", "ASSET", "CERT", "FED_RSSD", "org_name", "commented", "Commented", "mean_ASSET", "median_ASSET", "mean_ASSET_type", "median_ASSET_type"

## Current Progress
* Created a dataframe of all the datasets merged together into all_names_df.
  * 915289 entities
  * Columns: "std_name" (this is the cleaned name), "raw_name", "cik", "source"
* A crosswalk can be produced using the immediate matches from CIK IDs across the datasets. There are 133395 entities that match based on CIK IDs which ends up merging into 56760 rows in the dataframe. This leaves 781894 remaining rows to process
* The next step is to separate the remaining rows and use exact matches based on the cleaned std_name. This creates 14708 clusters based on std_name name. Then these exact matches begin merging with the CIK clusters. 
  * 759 existing clusters in the CIK crosswalk have the same std_name as the std_name cluster. 
  * Merging these gives up a crosswalk based on cleaned standardized names and CIK ids with 70709 rows/clusters. 

```bash
| cik      | standardized_names       | aliases                                                                      | sources       | match_type   |
|:---------|:-------------------------|:-----------------------------------------------------------------------------|:--------------|:-------------|
| [1750.0] | aar                      | AAR CORP                                                                     | compustat,cik | cik_cluster  |
| [1800.0] | abbott laboratories      | ABBOTT LABORATORIES                                                          | compustat,cik | cik_cluster  |
| [1841.0] | abel noser bd|abel noser | ABEL NOSER CORP                                         /BD|ABEL/NOSER CORP. | cik           | cik_cluster  |
```
* The last steps involve separating the remaining unprocessed rows to a new dataframe that need to be matched through a scoring-based algorithm. 
  * There are 728657 remaining entities that need to go through this
  * Matching algorithms to choose from:
    * get_match_candidate_score from the regextable-python repository
    * RapidFuzz algorithms including JaoWinkler.similarity or fuzz.token_set_ratio
* The workflow for matching has been implemented which uses a union-find object to create sets of high match scoring entities and then retrieving the information of entities through their indices in the dataframe of unproccesed entities. 


## To-Do List

* [ ] **Run the full program including fuzzy-matching**  
  * There is currently a running time issue, as matching thousands of entities can take longer than a typical laptop can handle, so there needs to be improvements to time complexity or implement a logic for running the program in batches. 

* [ ] **Check for duplicates**  
  * Identify and remove duplicate standardized names after cleaning

* [ ] **Testing and validation**  
  * Create test cases for all cleaning functions (`basicHash`, `corpHash`, `clean_fin_org_names`)
  * Verify edge cases of names with special characters, multiple suffixes, etc
  * Evaluate performance and accuracy of the cleaning + fuzzy matching

## requirements.txt

The **`requirements.txt`** file contains a list of all Python packages required for this project.

### Installation Options

To install all dependencies, you can choose one of the following methods:

* **Using pip:** Run the following command directly:
    ```bash
    pip install -r requirements.txt
    ```

* **Using the Installation Script:** Run the automated installation script:
    ```bash
    ./install_dependencies.sh
    ```
