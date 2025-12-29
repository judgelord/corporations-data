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
* Create a crosswalk table that aligns entities across multiple datasets (canonical key, raw name / aliases, CIK ID, FED RSSD ID, sources,matching type, fuzzy matching score)
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
* Converted all files into pandas dataframes—cik_df, compustat_df, and fdic_df. 
  * SEC_Institutions.csv no longer needs to be matched because it is a subset of CIK.csv
* Created an empty dataframe called final_crosswalk_df where merged entities will be stored. 
* Cleaned data within cik_df by merging entities together based on the same unique CIK ID. This reduced cik_df to 806225 entities after merging. Then this cleaned version is concated into final_crosswalk_df
* Merged compustat_df into final_crosswalk_based on unique CIK IDs, leaving only 19 unmerged entities from compustat. 
  * These remaining entities are concated into final_crosswalk_df as well. 
* 

```bash
                                    standardized_names  \
9                                                  aar   
11                                 abbott laboratories   
19               abrams industries|servidyne|servidyne   
23  academic computer systems|worlds com|worlds|worlds   
28                                               aceto   

                                                                                aliases  \
9                                                                              AAR CORP   
11                                                                  ABBOTT LABORATORIES   
19                                  ABRAMS INDUSTRIES INC|SERVIDYNE, INC.|SERVIDYNE INC   
23  ACADEMIC COMPUTER SYSTEMS INC|WORLDS COM INC|WORLDS INC|WORLDS.COM, INC.|WORLDS INC   
28                                                                           ACETO CORP   

     cik FED_RSSD        sources matching_type fuzzy_matching_score  
9   1750      NaN  cik,compustat  cik_id_match                  NaN  
11  1800      NaN  cik,compustat  cik_id_match                  NaN  
19  1923      NaN  cik,compustat  cik_id_match                  NaN  
23  1961      NaN  cik,compustat  cik_id_match                  NaN  
28  2034      NaN  cik,compustat  cik_id_match                  NaN  
```
* The last steps involve merging fdic_df into final_crosswalk_df. Before fuzzy matching, exact standardized name matching is used. 
  * Cleaned fdic_df by FED RSSD IDs which reduces the number of entities to 24,721. 
  * Important: Before standardized name matching, there must be a separation of entities in fdic that are qualified to be matched based on an exact standardized_name match. The same standardized names with different FED RSSD IDs in enriched fdic do not qualify to be matched into final_crosswalk_df based on this method, because it is ambiguous as to which one matches the entity in final_crosswalk_df. The same goes for entities in final_crosswalk_df that have the same standardized name, but are known to be different. 
  * After standardized name matching: 
```bash
            standardized_names  \
749           bb t financial   
3278  united california bank   
3517             mellon bank   
4769          rockland trust   
5593        trust new jersey   

                                                                                   aliases  \
749                                     BB&T FINANCIAL CORP|BB&T FUNDS|BB&T Financial, FSB   
3278  BANK OF THE WEST|SANWA BANK CALIFORNIA|UNITED CALIFORNIA BANK|UNITED CALIFORNIA BANK   
3517                            MELLON BANK CORP|MELLON FINANCIAL CORP|Mellon Bank, F.S.B.   
4769                                              ROCKLAND TRUST CO|Rockland Trust Company   
5593                                TRUST CO OF NEW JERSEY|The Trust Company of New Jersey   

        cik   FED_RSSD   sources                            matching_type  \
749   13839  [2689463]  cik,fdic  cik_id_match,standardized_name_matching   
3278  59951   [438368]  cik,fdic  cik_id_match,standardized_name_matching   
3517  64782   [825904]  cik,fdic  cik_id_match,standardized_name_matching   
4769  84616   [613008]  cik,fdic               standardized_name_matching   
5593  99982    [31303]  cik,fdic               standardized_name_matching   

     fuzzy_matching_score  
749                   NaN  
3278                  NaN  
3517                  NaN  
4769                  NaN  
5593                  NaN  
```
* Now, fuzzy matching can be used for the qualified remaining entities that were not matched from fdic_df. 
* Fuzzy matching information:
  * Library: rapidfuzz 
  * Function: fuzz.token_set_ratio
  * score_cutoff = 90


## To-Do List

* [ ] **Duplicates Issue**  
  * The workflow currently has a slight logic and type errors within the code that lead to some duplicated in IDs and there is missing FDIC data that needs to be adressed. 

* [ ] **Check for duplicates**  
  * Identify and remove duplicate standardized names and IDs after matching

* [ ] **Testing and validation**  
  * Verify edge cases of names with special characters, multiple suffixes, etc
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
