from helper_functions import *
from rapidfuzz import process, fuzz
import os
from pathlib import Path
import pandas as pd

current_dir = Path(__file__).resolve().parent.parent
data_dir = current_dir / 'data'

try:
    compustat_df = pd.read_csv(data_dir / 'CompustatNames.csv')
    cik_df = pd.read_csv(data_dir / 'CIK.csv')
    fdic_df = pd.read_csv(data_dir / 'FDIC_clean.csv') # Using your 'FDIC_clean.csv'
    sec_df = pd.read_csv(data_dir / 'SEC_Institutions.csv')
except FileNotFoundError as e:
    print(f"Error loading file: {e}")
    print(f"Please make sure your CSV files are in the directory: {data_dir}")
    exit()
print("Finished Reading Files...")

# -----------------------------------------------------------------
# NAME CLEANING
# -----------------------------------------------------------------
print("Cleaning file names for standardized name matching...")
# cleaning and standardizing organization names
compustat_df['std_name'] = compustat_df['conm'].apply(to_standardized_name)
fdic_df['std_name'] = fdic_df['NAME'].apply(to_standardized_name)
cik_df['std_name'] = cik_df['company_name'].apply(to_standardized_name)
sec_df['std_name'] = sec_df['Name'].apply(to_standardized_name)
print("Done creating standardized names")

print("Cleaning file names for R package regular expression matching...")
# cleaning and standardizing organization names
compustat_df['clean_alias'] = compustat_df['conm'].apply(clean_org_alias)
fdic_df['clean_alias'] = fdic_df['NAME'].apply(clean_org_alias)
cik_df['clean_alias'] = cik_df['company_name'].apply(clean_org_alias)
print("Done creating cleaned alias names")


duplicates_cik_id = cik_df['cik'].duplicated(keep = False)
duplicates_cik = cik_df[duplicates_cik_id]

# This is the final dataframe crosswalk where we will be merging entities into. 
cols = ['aliases', 'standardized_names', 'clean_alias', 'cik', 'FED_RSSD', 'ticker', 'naics', 'sources', 
        'matching_type', 'fuzzy_matching_score']
final_crosswalk_df = pd.DataFrame(columns = cols)

# -----------------------------------------------------------------
# CIK MATCHING
# -----------------------------------------------------------------
# Merging entities in cik_df based on the unique cik id value. 
print("Now merging entities in cik_df based on the unique cik id value.")
grouped_by_cik_id = cik_df.groupby('cik')
confident_matches = []
# count = 0
for cik_value, group in grouped_by_cik_id:
    # count += 1
    # if count % 1000 == 0:
    #   print(count)
    
    if len(group) > 1:
        # Aggregate the data based on cik
        new_match_keys = {
            'cik': group['cik'].dropna().unique().tolist(),
            # Now aggregate the std_name and clean_alias to see all variations found for cik
            'standardized_names': '|'.join(group['std_name'].dropna().unique()),
            'clean_alias': '|'.join(group['clean_alias'].dropna().unique()),
            # Aggregate other fields as before
            'aliases': '|'.join(group['company_name'].dropna().unique()),
            'sources': 'cik',
            'matching_type': 'cik_id_match'
        }
        confident_matches.append(new_match_keys)
    else: 
        unmatched_keys = {
            'cik': group['cik'].dropna().unique().tolist(),
            'standardized_names': group['std_name'].iloc[0],
            'clean_alias': group['clean_alias'].iloc[0],
            'aliases': group['company_name'].iloc[0],
            'sources': 'cik'
        }
        confident_matches.append(unmatched_keys)
         
pd.set_option('display.max_colwidth', None)
enriched_cik_df = pd.DataFrame(confident_matches)
print(f"cik_df reduced to {len(enriched_cik_df)} entities after merging.")

final_crosswalk_df = pd.concat([final_crosswalk_df, enriched_cik_df])
print("Added enriched cik_df to the final_crosswalk_df")

temp_compustat_df = compustat_df[compustat_df['cik'].notna()].copy()

# Apply the cleaning function to both dataframes
temp_compustat_df['cik'] = temp_compustat_df['cik'].astype('string')
temp_compustat_df.loc[:, 'cik'] = temp_compustat_df['cik'].apply(clean_cik)
final_crosswalk_df.loc[:, 'cik'] = final_crosswalk_df['cik'].apply(clean_cik)

# Merge compustat_df into final_crosswalk_df based on cik id. 
final_crosswalk_df = final_crosswalk_df.merge(temp_compustat_df, on = 'cik', how = 'left', 
                                              suffixes=('','_other'), indicator=True)
print("Successfully merged compustat into final_crosswalk_df based on cik id")

# Clean up final_crosswalk_df
CIK_merge_cleaup(final_crosswalk_df, "conm", "compustat", "tic", naics_column_name = "naics")
# Cleaning up final_crosswalk_df columns
final_crosswalk_df = final_crosswalk_df.drop(columns=['Unnamed: 0','gvkey', 'conm', 'cusip', 'sic', 'tic',\
                                                      'gsubind', 'gind', 'year1', 'year2', 'std_name', 
                                                      '_merge', 'clean_alias_other', 'naics_other'])

# Merge sec_df into final_crosswalk_df based on cik id. 
sec_df = sec_df.rename(columns = {'CIK': 'cik'})
sec_df.loc[:, 'cik'] = sec_df['cik'].apply(clean_cik)
final_crosswalk_df = final_crosswalk_df.merge(sec_df, on = 'cik', how = 'left', suffixes=('','_other'), indicator=True)
CIK_merge_cleaup(final_crosswalk_df, "Name", "sec", "Ticker")

final_crosswalk_df = final_crosswalk_df.drop(columns=['Ticker', 'index', 'Name', 'Exchange', 'SIC', 
                                                      'Business', 'Incorporated', 'IRS', '_merge', 'std_name'])

# TODO: fix below logic based on the changes made here


# Create a dataframe of entities that were not merged called remaining_compustat_df 
rejected_compustat_df = temp_compustat_df[~temp_compustat_df['cik'].isin(final_crosswalk_df['cik'])].reset_index(drop=True)
print(f"The number of compustat entities that didn't match anything: {len(rejected_compustat_df)}")
rejected_compustat_df = rejected_compustat_df.drop(columns = ['Unnamed: 0', 'gvkey', 'tic', 'cusip', 'sic', 
                                                              'naics', 'gsubind', 'gind', 'year1', 'year2', ])
rejected_compustat_df = rejected_compustat_df.rename(columns={'std_name': 'standardized_names', 'conm': 'aliases'})
rejected_compustat_df['sources'] = 'compustat'

print("Adding remaining of compustat into final_crosswalk_df ")
final_crosswalk_df = pd.concat([final_crosswalk_df, rejected_compustat_df], axis = 0, ignore_index=True)

# -----------------------------------------------------------------
# FED_RSSD MATCHING
# -----------------------------------------------------------------
# Merge entities in fdic based on FED_RSSD values with itself to remove duplicates. 
# New df called enriched_fdic_df
print("Merging entities in fdic based on FED_RSSD values with itself to remove duplicates...")
print(f"original length of fdic: {len(fdic_df)}")
grouped_by_FED_RSSD = fdic_df.groupby('FED_RSSD')
confident_matches = []
# count = 0
for FED_RSSD_value, group in grouped_by_FED_RSSD:
    # count += 1
    # if count % 1000 == 0:
    #   print(count)
    
    if len(group) > 1:
        # Aggregate the data based on cik
        new_match_keys = {
            'FED_RSSD': group['FED_RSSD'].dropna().unique().tolist(),
            # Now aggregate the std_name to see all variations found for FED_RSSD
            'standardized_names': '|'.join(group['std_name'].dropna().unique()),
            'clean_alias': '|'.join(group['clean_alias'].dropna().unique()),
            # Aggregate other fields as before
            'aliases': '|'.join(group['NAME'].dropna().unique()),
            'sources': 'fdic',
            'matching_type': 'FED_RSSD_match'
        }
        confident_matches.append(new_match_keys)
    else: 
        unmatched_keys = {
            'FED_RSSD': group['FED_RSSD'].dropna().unique().tolist(),
            'standardized_names': group['std_name'].iloc[0],
            'clean_alias': group['clean_alias'].iloc[0],
            'aliases': group['NAME'].iloc[0],
            'sources': 'fdic'
        }
        confident_matches.append(unmatched_keys)
         
enriched_fdic_df = pd.DataFrame(confident_matches)
print(f"fdic_df reduced to {len(enriched_fdic_df)} entities after merging.")

# -----------------------------------------------------------------
# EXACT STANDARDIZED_NAMES MATCHING
# -----------------------------------------------------------------
# Checking to see which entities in fdic are qualified to be matched 
# based on an exact standardized_name match. Standardized names with more than 
# one appearence in enriched fdic do not qualify to be matched into final_crosswalk_df 
# based on this method, because it is ambiguous as to whether which one matches the entity 
# in final_crosswalk_df when we know they are different because they have different 
# FED_RSSD ids. This goes the same for final_crosswalk_df if there are multiple standardized
# names for one entity. 
print("Identifying entities qualified for exact standardized name matching...")
final_crosswalk_df_exploded = (
    final_crosswalk_df.assign(standardized_names = final_crosswalk_df['standardized_names'].str.split('|'))
    .explode('standardized_names')  
)

final_crosswalk_df_exploded['standardized_names'] = (
    final_crosswalk_df_exploded['standardized_names'].str.strip()
)

enriched_fdic_df_exploded = (
    enriched_fdic_df.assign(standardized_names = enriched_fdic_df['standardized_names'].str.split('|'))
    .explode('standardized_names')  
)

enriched_fdic_df_exploded['standardized_names'] = (
    enriched_fdic_df_exploded['standardized_names'].str.strip()
)

# Find duplicated rows for each column separately
unqualified_for_standardized_names_matching_fdic = enriched_fdic_df_exploded['standardized_names'].duplicated(keep=False)
qualified_for_standardized_names_matching__fdic_exploded = enriched_fdic_df_exploded[~unqualified_for_standardized_names_matching_fdic]

duplicated_cik_final = final_crosswalk_df_exploded["cik"].duplicated(keep=False)
duplicated_names_final = final_crosswalk_df_exploded["standardized_names"].duplicated(keep=False)

# Keep only rows where neither cik nor standardized_names are duplicated
qualified_for_standardized_names_matching_final_exploded = final_crosswalk_df_exploded[~(duplicated_cik_final | duplicated_names_final)]

# Unqualified = rows where either cik or standardized_names is duplicated
# Keeping unqualified entities to be merged later
unqualified_for_standardized_names_matching_final_exploded = final_crosswalk_df_exploded[duplicated_cik_final | duplicated_names_final]
grouped_by_cik_id = unqualified_for_standardized_names_matching_final_exploded.groupby('cik')
confident_matches = []
# Grouping the entities that can't be matched based on name back together on cik id. 
for cik_value, group in grouped_by_cik_id:
    if len(group) > 1:
        # Aggregate the data based on cik
        new_match_keys = {
            'cik': group['cik'].dropna().iloc[0],
            # Now aggregate the std_name to see all variations found for cik
            'standardized_names': '|'.join(group['standardized_names'].dropna().unique()),
            'clean_alias': '|'.join(group['clean_alias'].dropna().unique()),
            # Aggregate other fields as before
            'aliases': '|'.join(group['aliases'].dropna().unique()),
            'sources': ','.join(group['sources'].dropna().unique()),
            'matching_type': ','.join(group['matching_type'].dropna().unique())
        }
        confident_matches.append(new_match_keys)
    else: 
        unmatched_keys = {
            'cik': group['cik'].dropna().iloc[0],
            'standardized_names': group['standardized_names'].iloc[0],
            'aliases': group['aliases'].iloc[0],
            'clean_alias': group['clean_alias'].iloc[0],
            'sources': group['sources'].iloc[0]
        }
        confident_matches.append(unmatched_keys)
         
pd.set_option('display.max_colwidth', None)
unqualified_for_standardized_names_matching_final_df = pd.DataFrame(confident_matches)

# This dataframe will be just later concated to the final data frame becasue they cannot be matched on names
# add column for reason
unqualified_for_standardized_names_matching_final_df['ineligible_name_matching'] = True

overlap = final_crosswalk_df.columns.intersection(qualified_for_standardized_names_matching__fdic_exploded.columns)

qualified_for_standardized_names_matching__fdic_exploded = qualified_for_standardized_names_matching__fdic_exploded.rename(
    columns={
        c: f'df2_{c}'
        for c in overlap
        if c != 'standardized_names'
    }
)

# Merging...
print("Merging into final_crosswalk_df...")
merged = qualified_for_standardized_names_matching_final_exploded.merge(
    qualified_for_standardized_names_matching__fdic_exploded,
    on='standardized_names',
    how='left',
    suffixes=('', '_df2'),
    indicator=True
)

# Clean up merged before turning back into final_crosswalk_df

mask = merged['_merge'] == 'both'

# add new alias
aliases = merged['aliases'].astype('string')
new_alias = merged['df2_aliases'].astype('string')

# add clean_alias
clean_aliases = merged['clean_alias'].astype('string')
new_clean_alias = merged['df2_clean_alias'].astype('string')

merged['aliases'] = aliases.where(
    new_alias.isna() | (aliases == new_alias),
    aliases + '|' + new_alias
).fillna(new_alias)

# add clean_alias
merged['clean_alias'] = clean_aliases.where(
    new_clean_alias.isna() | (clean_aliases == new_clean_alias),
    clean_aliases + '|' + new_clean_alias
).fillna(new_clean_alias)

# add the source fdic
merged.loc[mask, 'sources'] = (
    merged.loc[mask, 'sources']
    .fillna('')
    .where(
        merged.loc[mask, 'sources'] == '',
        merged.loc[mask, 'sources'] + ','
    )
    + 'fdic'
)

merged.loc[mask, 'FED_RSSD'] = (
    merged.loc[mask, 'df2_FED_RSSD']
)

# add the entity is matched by standardized_name_matching
merged.loc[mask, 'matching_type'] = (
    merged.loc[mask, 'matching_type']
    .fillna('')
    .where(
        merged.loc[mask, 'matching_type'] == '',
        merged.loc[mask, 'matching_type'] + ','
    )
    + merged.loc[mask, 'df2_matching_type'].fillna('') + ',' + 'standardized_name_matching'
)

merged = merged.drop(columns=['df2_FED_RSSD','df2_aliases', 'df2_clean_alias', 'df2_sources', 'df2_matching_type', '_merge'])
print("Sucessfully merged based on exact standardized names")

# -----------------------------------------------------------------
# FUZZING MATCHING
# -----------------------------------------------------------------
# Identify the remaining entities from fdic that were not merged to be fuzzy matched
print("Identifying the remaining qualified entities from fdic that were not merged to be fuzzy matched")
qualified_for_fuzzy_matching = qualified_for_standardized_names_matching__fdic_exploded[\
    ~qualified_for_standardized_names_matching__fdic_exploded['standardized_names']\
    .isin(merged['standardized_names'])].reset_index(drop = True) 


# Create a testing mode to sample data for faster fuzzy matching
TESTING_MODE = True
SAMPLE_FRAC = 0.01 # choose percent of data to sample in testing mode

if TESTING_MODE:
    print(f"--- RUNNING FUZZY MATCHING IN TESTING MODE (Sample: {SAMPLE_FRAC*100}%) ---")
    
    # Take a random sample of your 'unmatched_for_fuzzy' DataFrame
    qualified_for_fuzzy_matching = qualified_for_fuzzy_matching.sample(frac=SAMPLE_FRAC, random_state=42)
    
    print(f"  'qualified_for_fuzzy_matching' sampled to: {len(qualified_for_fuzzy_matching)} rows")
    print("-------------------------------------------------")
    
else:
    print(f"--- RUNNING FUZZY MATCHING IN FULL PRODUCTION MODE ---")
    print(f"  'qualified_for_fuzzy_matching' full size: {len(qualified_for_fuzzy_matching)} rows")
    print("-------------------------------------------------")
    

# Merge qualified_for_fuzzy_matching into merged based on fuzzy matching. 
# 1. Go through each entity in remaining qualified_for_fuzzy_matching and go through the final_crosswalk_df entities
# 2. If the score is higher than the desired threshold, append the values to the existing Series. 

# Prepare list of all names from merged, flattened for multiple names per row
crosswalk_alias_list = []
crosswalk_idx_list = []
merged['FED_RSSD'] = merged['FED_RSSD'].apply(normalize_to_list)
merged['fuzzy_matching_score'] = [[] for _ in range(len(merged))]

print('Beginning string splitting')
# count = 0
for idx, row in merged.iterrows():
    # count += 1 
    # if count % 1000 == 0:
    #     print(count)
    names = row['aliases'].split('|')
    for name in names:
        crosswalk_alias_list.append(name)
        crosswalk_idx_list.append(idx)

# Now go through qualified_for_fuzzy_matching
count = 0
print('Beginning fuzzy matching')
for i, new_row in qualified_for_fuzzy_matching.iterrows():
    count += 1 
    if count % 50 == 0:
        print(count)
    
    new_alias = new_row['df2_aliases']
    # Find best matches with threshold 90
    matches = process.extract(
        new_alias,
        crosswalk_alias_list,
        scorer=fuzz.token_set_ratio,
        score_cutoff=90
    )
    
    for match_name, score, match_pos in matches:
        idx = crosswalk_idx_list[match_pos]
        
        # Skip merge if 'fdic' already in sources
        existing_sources = merged.at[idx, 'sources']
        if existing_sources and 'fdic' in existing_sources.split(','):
            continue

        # Update merged row
        merged.at[idx, 'aliases'] = (
            merged.at[idx, 'aliases'] + '|' + new_alias
        )
        
        mask = qualified_for_fuzzy_matching['df2_aliases'] == new_alias
        alias_val = qualified_for_fuzzy_matching.loc[mask, 'standardized_names'].iloc[0]
        merged.at[idx, 'standardized_names'] = (
            merged.at[idx, 'standardized_names'] + '|' + alias_val
        )
        
        # Check if the cell is empty/NaN first to avoid string errors
        current_new_alias = merged.at[idx, 'new_alias']
        if pd.isna(current_new_alias) or current_new_alias == '':
            merged.at[idx, 'new_alias'] = new_alias
        else:
            merged.at[idx, 'new_alias'] = f"{current_new_alias}|{new_alias}"
        
        rssd_val = qualified_for_fuzzy_matching.loc[mask, 'df2_FED_RSSD'].iloc[0]
        # If rssd_val is a list, get the first element
        if isinstance(rssd_val, list) and len(rssd_val) > 0:
            rssd_val = rssd_val[0]
        merged.at[idx, 'FED_RSSD'].append(int(rssd_val))

        val_source = merged.at[idx, 'sources']
        merged.at[idx, 'sources'] = (
            ("" if pd.isna(val_source) or val_source == '' else val_source + ',') + 'fdic'
        )

        val_matching_type = merged.at[idx, 'matching_type']
        merged.at[idx, 'matching_type'] = (
            ("" if pd.isna(val_matching_type) or val_matching_type == '' else val_matching_type + ',') + 'fuzzy_matching'
        )
        # Append fuzzy score to the column
        merged.at[idx, 'fuzzy_matching_score'].append(score)
print("Finished fuzzy matching")
        
merged['FED_RSSD'] = (
    merged['FED_RSSD']
    .str[0]
    .astype('Int64') 
)

enriched_fdic_df['FED_RSSD'] = (
    enriched_fdic_df['FED_RSSD']
    .str[0]
    .astype('Int64')   
)

print("Adding entities that were not matched from fdic into final_crosswalk_df and entites from final_crosswalk_df that were\
      removed because they were not qualified for exact standardized name matching")
remaining_fdic_df = enriched_fdic_df[~enriched_fdic_df['FED_RSSD'].isin(merged['FED_RSSD'])]

final_crosswalk_df = pd.concat(
    [
        merged,
        remaining_fdic_df,
        unqualified_for_standardized_names_matching_final_df
    ],
    ignore_index=True
)

# Fill the NaNs and immediately cast to boolean
final_crosswalk_df['ineligible_name_matching'] = (
    final_crosswalk_df['ineligible_name_matching']
    .fillna(False)
    .astype(bool)
)
 
print("Exporting final_crosswalk_df into a csv file")
if TESTING_MODE:
    final_crosswalk_df.to_csv(data_dir / 'final_crosswalk_test.csv', index=False)
else:
    final_crosswalk_df.to_csv(data_dir / 'final_crosswalk.csv', index=False)
print("CROSSWALK CREATION COMPLETE")