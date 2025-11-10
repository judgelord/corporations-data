# Organization Name Standardization Process

## Overview
This Python project develops a process for **standardizing raw organizational names** to improve **entity matching** across multiple datasets. By using a combination of **string cleaning**, **regular expressions**, and **hashing functions**, the goal is to create a large **crosswalk table**

The work is currently implemented and tested within a **Jupyter notebook** for simplied use
> Note: This notebook is still under development. Several functions and matching methods need refinement and expansion

---

## Objectives
- Clean and normalize raw organization names from various datasets.
- Eliminate common textual noise, legal suffixes, punctuation, and inconsistent capitalization
- Map variations of the same organization to a single standardized key
- Create a crosswalk table that aligns entities across multiple datasets (canonical key, raw name, column for each of the source data sets)

## To-Do List

- [ ] **Implement fuzzy matching**  
  - Use libraries such as `fuzzywuzzy` or `rapidfuzz` to handle near-duplicate names 

- [ ] **Check for duplicates**  
  - Identify and remove duplicate standardized names after cleaning

- [ ] **Testing and validation**  
  - Create test cases for all cleaning functions (`basicHash`, `corpHash`, `clean_fin_org_names`)
  - Verify edge cases of names with special characters, multiple suffixes, etc
  - Evaluate performance and accuracy of the cleaning + fuzzy matching

## requirements.txt

The requirements.txt file contains a list of all Python packages required for this project. 
To install all dependencies, run: \
`pip install -r requirements.txt` \
Or use the automated installation script: \ 
`./install_dependencies.sh` \
