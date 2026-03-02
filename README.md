# Organization Name Standardization Process

## Overview
This Python project develops a process for **standardizing raw organizational names** to improve **entity matching** across multiple datasets. By using a combination of **string cleaning**, **regular expressions**, and **hashing functions**, the goal is to create a large **crosswalk table**

The work is implemented and tested within a **Jupyter notebook** for simplied use. The full script can also be run in a .py file. 
> Note: This python script is currently under version 1 of development. There could be errors around false matches, etc. 

---

## Objectives
* Clean and normalize raw organization names from various datasets.
* Eliminate common textual noise, legal suffixes, punctuation, and inconsistent capitalization
* Map variations of the same organization based on standardized names or other unique keys
* Create a crosswalk table that aligns entities across multiple datasets (canonical key, raw name / aliases, CIK ID, FED RSSD ID, sources,stock tickers, NAICS codes, matching type, fuzzy matching score)
  * CIK (Central Index Key) is one way we can automatically match entities. They are used on the Securities Exchange Commission's (SEC) computer systems to identify corporations and individual people who have filed disclosure with the SEC.
  * RSSD ID (Research, Statistics, Supervision, and Discount ID) is a unique number assigned by the Federal Reserve Board to financial institutions for identification in their data systems, acting as a distinct identifier for banks, holding companies, and other entities in the U.S. financial system. 

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
* Converted all files into pandas dataframes—cik_df, compustat_df, sec_df, and fdic_df. 
* Created an empty dataframe called final_crosswalk_df where merged entities will be stored. 
* Cleaned data within cik_df by merging entities together based on the same unique CIK ID. This reduced cik_df to 806225 entities after merging. Then this cleaned version is concated into final_crosswalk_df
* Merged sec_df and compustat_df into final_crosswalk_based on unique CIK IDs, leaving only 19 unmerged entities from compustat. 
  * These remaining entities are concated into final_crosswalk_df as well. 
* The last steps involve merging fdic_df into final_crosswalk_df. Before fuzzy matching, exact standardized name matching is used. 
  * Cleaned fdic_df by FED RSSD IDs which reduces the number of entities to 24,721. 
  * Important: Before standardized name matching, there must be a separation of entities in fdic that are qualified to be matched based on an exact standardized_name match. The same standardized names with different FED RSSD IDs in enriched fdic do not qualify to be matched into final_crosswalk_df based on this method, because it is ambiguous as to which one matches the entity in final_crosswalk_df. The same goes for entities in final_crosswalk_df that have the same standardized name, but are known to be different. 
* Now, fuzzy matching can be used for the qualified remaining entities that were not matched from fdic_df. 
* Fuzzy matching information:
  * Library: rapidfuzz 
  * Function: fuzz.token_set_ratio
  * score_cutoff = 90
* Final Crosswalk (cleaned with only columns ['aliases', 'cik', 'FED_RSSD', 'ticker', 'naics', 'sources']):
``` bash
                                             aliases  \
0  DEFINED ASSET FUNDS MUNICIPAL INVT TR FD NEW Y...   
1  CORPORATE INCOME FUND SEVENTY NINTH SHORT TERM...   
2  DEFINED ASSET FUNDS MUNICIPAL INVT TR FD MON P...   
3  DEFINED ASSET FUNDS MUNICIPAL INVT TR FD MON P...   
4  NUVEEN TAX EXEMPT UNIT TRUST SERIES 169 NATION...   

                                  standardized_names   cik  FED_RSSD ticker  \
0  defined asset funds municipal invt tr fd new y...   3.0       NaN    NaN   
1  corporate income fund seventy ninth short term...  13.0       NaN    NaN   
2  defined asset funds municipal invt tr fd mon p...  14.0       NaN    NaN   
3  defined asset funds municipal invt tr fd mon p...  17.0       NaN    NaN   
4  nuveen tax exempt unit trust series 169 nation...  18.0       NaN    NaN   

   naics sources matching_type fuzzy_matching_score  ineligible_name_matching  
0    NaN     cik           NaN                   []                     False  
1    NaN     cik           NaN                   []                     False  
2    NaN     cik           NaN                   []                     False  
3    NaN     cik           NaN                   []                     False  
4    NaN     cik           NaN                   []                     False  
```

## To-Do List
* [ ] **Testing and validation**  
  * Evaluate performance and accuracy of the cleaning + fuzzy matching using hand matching

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
