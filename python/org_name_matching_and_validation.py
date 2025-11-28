#!/usr/bin/env python
# coding: utf-8

import math
from tqdm import tqdm
import nltk
from nltk.corpus import stopwords
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
nltk.download('stopwords')
from nltk.tokenize import word_tokenize
import pandas as pd
from datetime import datetime
import pickle
import re
from pyxdameraulevenshtein import damerau_levenshtein_distance
import apsw
import sys
import numpy as np
import corp_simplify_utils
import seaborn as sns
import matplotlib.pyplot as plt
import pyreadr
from collections import Counter

# nlp
import spacy
from spacy import displacy
from collections import Counter
# to install: $python3 -m spacy download en_core_web_lg
import en_core_web_lg

# analysis/regressions
import statsmodels.api as sm
from statsmodels.formula.api import glm
from statsmodels.genmod.families import Poisson
from scipy.stats import ks_2samp
from scipy.stats import mannwhitneyu
from scipy.stats import ttest_ind

# from statsmodels.graphics.gofplots import qqplot_2samples
from scipy import stats
from joypy import joyplot
from matplotlib import cm

from datetime import date
today_for_filenames = date.today()
curr_date = str(today_for_filenames.strftime("%Y%m%d"))


NUMBER_OF_MATCHES_TO_RECORD = 10
punc_remove_re = re.compile(r'\W+')
corp_re = re.compile('( (group|holding(s)?( co)?|inc(orporated)?|ltd|l ?l? ?[cp]|co(rp(oration)?|mpany)?|s[ae]|plc))+$')
and_re = re.compile(' & ')
punc1_re = re.compile(r'(?<=\S)[\'’´\.](?=\S)')
punc2_re = re.compile(r'[\s\.,:;/\'"`´‘’“”\(\)\[\]\{\}_—\-?$=!]+')

STOPWORDS = nltk.corpus.stopwords.words('english')
STOPWORDS.remove("am")
STOPWORDS.remove("up")
STOPWORDS.remove("in")
STOPWORDS.remove("on")
STOPWORDS.remove("all")
STOPWORDS.remove("any")
STOPWORDS.remove("most")
STOPWORDS.remove("no")
STOPWORDS.remove("nor")
STOPWORDS.remove("own")
STOPWORDS.remove("same")
STOPWORDS.remove("so")
STOPWORDS.remove("very")
STOPWORDS.remove("s")
STOPWORDS.remove("t")
STOPWORDS.remove("d")
STOPWORDS.remove("ll")
STOPWORDS.remove("m")
STOPWORDS.remove("o")
STOPWORDS.remove("re")
STOPWORDS.remove("ve")
STOPWORDS.remove("y")

#compile regex patterns to reuse
STOPWORD_RE = re.compile(r'\b(the|of|and|in|on)\b', re.IGNORECASE)
CORP_SUFFIX_RE = re.compile(r'\b(inc|corp|ltd|llc|plc|co|company|limited)\b', re.IGNORECASE)
PDF_PATTERN_RE = re.compile(r'\s[0-9]*\s[km]b\s*pdf', re.IGNORECASE)
PUNCT_RE = re.compile(r'[^\w\s-]')  # match punctuation
MULTISPACE_RE = re.compile(r'\s+')

stopword_re_str = r""
for word in STOPWORDS:
	stopword_re_str += r'\b' + word + r'\b|'
stopword_re = re.compile(stopword_re_str[:-1]) # The negative 1 is for the fencepost |

NON_FINANCIAL_ORG_TERMS = [
    'university', 'college', 'school', 'institute', 'academy', 
    'hospital', 'medical center', 'health system', 'center', 
    'commission', 'authority', 'association', 'society', 
    'foundation', 'transportation services', 'district', 
    'chamber', 'commerce', 'library', 'museum', 'public', 
    'city', 'county', 'town', 'government', 'state', 'federal',
    'ministry', 'department', 'office'
]

NON_FINANCIAL_RE = re.compile(r'\b(' + '|'.join(NON_FINANCIAL_ORG_TERMS) + r')\b', re.IGNORECASE)

BASE_DIR = "/Users/aawesomez/Documents/UROP/NLP-regextable/"
# BASE_DIR = "/Users/jameschen/Team Name Dropbox/James Chen/JLW-FINREG-PARTICIPATION/"
# BASE_DIR = "/Users/jameschen/Documents/Code/JLW-FINREG-PARTICIPATION/"
# DB_PATH = BASE_DIR + "data/master.sqlite"
DB_PATH = BASE_DIR + "Data/master.sqlite"
# LAST_SAVE_DATASET_DATE = "20210824"
LAST_SAVE_DATASET_DATE = "20220402" # Needs to be set to the last date the 'rebuild datasets' part of this code was run

# Function to calculate longest common substring, from https://www.geeksforgeeks.org/print-longest-common-substring/
# function to find and print 
# the longest common substring of
# X[0..m-1] and Y[0..n-1]
def get_longest_common_substring(X, Y, m, n):
 
    # Create a table to store lengths of
    # longest common suffixes of substrings.
    # Note that LCSuff[i][j] contains length
    # of longest common suffix of X[0..i-1] and
    # Y[0..j-1]. The first row and first
    # column entries have no logical meaning,
    # they are used only for simplicity of program
    LCSuff = [[0 for i in range(n + 1)]
                 for j in range(m + 1)]
 
    # To store length of the
    # longest common substring
    length = 0
 
    # To store the index of the cell
    # which contains the maximum value.
    # This cell's index helps in building
    # up the longest common substring
    # from right to left.
    row, col = 0, 0
 
    # Following steps build LCSuff[m+1][n+1]
    # in bottom up fashion.
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 or j == 0:
                LCSuff[i][j] = 0
            elif X[i - 1] == Y[j - 1]:
                LCSuff[i][j] = LCSuff[i - 1][j - 1] + 1
                if length < LCSuff[i][j]:
                    length = LCSuff[i][j]
                    row = i
                    col = j
            else:
                LCSuff[i][j] = 0
 
    # if true, then no common substring exists
    if length == 0:
        return ""
 
    # allocate space for the longest
    # common substring
    resultStr = ['0'] * length
 
    # traverse up diagonally form the
    # (row, col) cell until LCSuff[row][col] != 0
    while LCSuff[row][col] != 0:
        length -= 1
        resultStr[length] = X[row - 1] # or Y[col-1]
 
        # move diagonally up to previous cell
        row -= 1
        col -= 1
 
    # required longest common substring
    longest_common_substring = ''.join(resultStr)

    return longest_common_substring


# Function from Brad Hackinen's NAMA
def basicHash(s):
    '''
    A simple case and puctuation-insensitive hash
    '''
    s = s.lower()
    s = re.sub(and_re,' and ',s)
    s = re.sub(punc1_re,'',s)
    s = re.sub(punc2_re,' ',s)
    s = s.strip()

    return s

# Function from Brad Hackinen's NAMA
def corpHash(s):
    '''
    A hash function for corporate subsidiaries
    Insensitive to
        -case & punctation
        -'the' prefix
        -common corporation suffixes, including 'holding co'
    '''
    s = basicHash(s)
    if s.startswith('the '):
        s = s[4:]

    s = re.sub(corp_re,'',s,count=1)

    return s

# function to clean org names
def clean_fin_org_names(name: str) -> str:
    if name is None or not isinstance(name, str) or name == "NA":
        return ""
    
    # James strip metadata from name
    name = name.split(',')[0]
    #Remove patterns like "10 kb pdf"
    name = PDF_PATTERN_RE.sub("", name)

    #Unicode and punctuation cleanup
    name = corp_simplify_utils.normalize_unicode(name)
    name = PUNCT_RE.sub(" ", name)

    #Remove corporate suffixes and stopwords and non-financial entity
    name = CORP_SUFFIX_RE.sub("", name)
    name = NON_FINANCIAL_RE.sub("", name)
    name = STOPWORD_RE.sub("", name)

    #Normalize spacing and lowercase
    name = MULTISPACE_RE.sub(" ", name).strip().lower()

    return name


# Function for organizing the covariates available for each of the gathered datasets
def get_data_row(match_type, match_row_num, match_on_type):

    df = covariate_dfs[match_type]
    column_names = df.columns
    match_covariates = df.iloc[match_row_num]
    
    covariate_dict = {'row_id':match_row_num, 'row_type':match_type}
    for elem_idx, elem in enumerate(match_covariates):
        var_name = match_type + "-" + match_on_type + ":" + column_names[elem_idx]
        val = elem
        covariate_dict[var_name] = val

    return covariate_dict
    
# Function to clean numeric fields that may have text like K for thousand
def clean_financial_measure(x):
    if x is None or x is np.nan or pd.isnull(x) or x == "":
        return np.nan
    elif isinstance(x, str) and not x.isnumeric():
        unit_multiplier = 1
        if "B" in x:
            x = x[:-1]
            unit_multiplier = 1000000000
        if "M" in x:
            x = x[:-1]
            unit_multiplier = 1000000
        if "K" in x:
            x = x[:-1]
            unit_multiplier = 1000
        x = x.replace(",", "")
        try:
            x = float(x) * unit_multiplier
            return x
        except:
            return np.nan
    else:
        return float(x)
    
# 3.1: Read the gathered datasets in as one dataframe
def get_covariate_dfs():
    covariate_dfs = {}
    financial_datasets = [("data/merged_resources/", "FDIC_Institutions"), 
                    ("data/merged_resources/", "FFIECInstitutions"),
                    ("data/", "CreditUnions"),
                    ("data/merged_resources/", "compustat_resources"),
                    ("data/merged_resources/", "nonprofits_resources"),
                    ("data/merged_resources/", "SEC_Institutions")
    ]
    for financial_dataset_tuple in financial_datasets:
        df = pd.read_csv(BASE_DIR + financial_dataset_tuple[0] + financial_dataset_tuple[1] + ".csv")
        covariate_dfs[financial_dataset_tuple[1]] = df
        
    # Read in opensecrets dataseparately to deal with quotechar
    df = pd.read_csv(BASE_DIR + "data/merged_resources/opensecrets_resources_jwVersion.csv", quotechar='"')
    covariate_dfs['opensecrets_resources_jwVersion'] = df
        
    # Merge compustat data to cik data on cik
    cik_df = pd.read_csv(BASE_DIR + "data/merged_resources/CIK.csv", dtype={"CIK":str})
    compustat_df = pd.read_csv(BASE_DIR + "data/merged_resources/compustat_resources.csv", dtype={"cik":str})
    compustat_df.sort_values(by=['year2', 'year1'], ascending=True, inplace=True)
    compustat_df = compustat_df.drop_duplicates(subset='cik', keep='last', ignore_index=True)
    compustat_df = compustat_df[['cik', 'marketcap']]

    # James: dtype convert
    cik_df['cik']= cik_df['cik'].astype('Int64')
    compustat_df['cik']= compustat_df['cik'].astype('Int64')

    cik_merged_df = cik_df.merge(compustat_df, how='left', left_on='cik', right_on='cik')
    del cik_merged_df['cik']
    covariate_dfs['CIK'] = cik_merged_df

    return covariate_dfs
    

def clean_match_score(x):
    if x is None or x is np.nan or pd.isnull(x) or x == "":
        return np.nan
    elif isinstance(x, str) and not x.isnumeric():
        unit_multiplier = 1
        if "B" in x:
            x = x[:-1]
            unit_multiplier = 1000000000
        if "M" in x:
            x = x[:-1]
            unit_multiplier = 1000000
        if "K" in x:
            x = x[:-1]
            unit_multiplier = 1000
        x = x.replace(",", "")
        try:
            x = float(x) * unit_multiplier
            return x
        except:
            return np.nan
    else:
        return float(x)

def get_quantile_by_variable(df, ascending_sort_var, ascending_quantile_start, ascending_quantile_end, vars_to_describe):

    df.sort_values(ascending_sort_var, ascending=True, inplace=True)
    num_rows = df.shape[0]
    start_idx = int(ascending_quantile_start * num_rows)
    end_idx = int(ascending_quantile_end * num_rows)
    quantile_df = df.iloc[start_idx:end_idx, :]
    return quantile_df[vars_to_describe]

def get_match_candidate_score(frequency_dict, org_name, candidate_match_name):
    if not isinstance(org_name, str):
        org_name = ""
    if not isinstance(candidate_match_name, str):
        candidate_match_name = ""
    
    if not org_name or not candidate_match_name:
        return 0.0
    
    org_tokens = org_name.split(' ')
    
    # tokenize the candidate match
    candidate_match_tokens = set(candidate_match_name.split(" "))

    max_dist = 1

    # Calculate the match score
    total_inverse_frequency = 0
    total_matching_inverse_frequency = 0
    tokenized_name = org_tokens
    for token in tokenized_name:
        token_frequency = frequency_dict.get(token, 999999) # if token not found, give high frequency to ignore it
        token_inverse_frequency = 1.0/token_frequency
        total_inverse_frequency += token_inverse_frequency

        best_token_similarity = 0.0
        
        for candidate_token in candidate_match_tokens:
            if not token or not candidate_token:
                continue

            dist = damerau_levenshtein_distance(token, candidate_token)

            if dist <= max_dist:
                max_len = max(len(token), len(candidate_token))
                if max_len == 0: continue
                similarity = 1.0 - (dist / max_len)

                best_token_similarity = max(best_token_similarity, similarity)
        if best_token_similarity > 0.0:
            total_matching_inverse_frequency += token_inverse_frequency * best_token_similarity
    
    try:
        match_score = total_matching_inverse_frequency / total_inverse_frequency
    except ZeroDivisionError:
        match_score = 0.0

    #Multiplicative DL Penalty
    m = len(org_name)
    n = len(candidate_match_name)
    if m == 0 or n == 0: return 0.0

    dl_distance = damerau_levenshtein_distance(org_name, candidate_match_name)
    normalized_dl = dl_distance / max(m, n)

    final_score = match_score * (1 - normalized_dl)
    return max(0.0, final_score)


REBUILD_DATSETS = True
if REBUILD_DATSETS:

    ## PART 1: Match records from the gathered organization datasets (FDIC, FFEIC, Nonprofits, CIK, Compustat, etc.) to scraped comments

    # 1.1: Read and clean org names from gathered org datasets
    sources = ["FDIC_Institutions", "FFIECInstitutions", "CreditUnions", "CIK", "compustat_resources", "nonprofits_resources", "opensecrets_resources_jwVersion", "SEC_Institutions"]
    # sources = ["FFIECInstitutions", "CIK"]

    org_name_dict = {}
    if True:
        financial_datasets = []
        unique_ids = []
        all_org_names = []
        for financial_dataset in sources:
            intermediate_data_folder = "data/"
            col_name = ""
            read_from_file = False
            if financial_dataset == "FDIC_Institutions":
                intermediate_data_folder = "data/merged_resources/"
                col_name = "NAME"
                read_from_file = True
            elif financial_dataset == "FFIECInstitutions":
                intermediate_data_folder = "data/merged_resources/"
                col_name = "Financial Institution Name"
                read_from_file = True
            elif financial_dataset == "CreditUnions":
                col_name = "CU_NAME"
                read_from_file = True
            elif financial_dataset == "CIK":
                intermediate_data_folder = "data/merged_resources/"
                col_name = "company_name"#"COMPANYNAME"
                read_from_file = True
            elif financial_dataset == "compustat_resources":
                intermediate_data_folder = "data/merged_resources/"
                col_name = "conm"
                read_from_file = True
            elif financial_dataset == "nonprofits_resources":
                intermediate_data_folder = "data/merged_resources/"
                col_name = "name"
                read_from_file = True
            elif financial_dataset == "opensecrets_resources_jwVersion":
                intermediate_data_folder = "data/merged_resources/"
                col_name = "orgName"
                read_from_file = True
            elif financial_dataset == "SEC_Institutions":
                intermediate_data_folder = "data/merged_resources/"
                col_name = "Name"
                read_from_file = True

            print(financial_dataset)
            if financial_dataset == "opensecrets_resources_jwVersion":
                df = pd.read_csv(BASE_DIR + intermediate_data_folder + financial_dataset + ".csv", quotechar='"')
            else:
                df = pd.read_csv(BASE_DIR + intermediate_data_folder + financial_dataset + ".csv")
            df['unique_id'] = financial_dataset + "-" + df.index.astype(str)
            df['financial_dataset'] = financial_dataset
            financial_datasets = financial_datasets + list(df['unique_id'])
            unique_ids = unique_ids + list(df['unique_id'])
            all_org_names = all_org_names + list(df[col_name])

        data = list(zip(unique_ids, all_org_names, financial_datasets))
        org_name_df = pd.DataFrame(data, columns=['unique_id', 'org_name', 'financial_dataset'])
        # org_name_df_lst = []
        # for source in sources:
        #     org_name_df_lst.append(org_name_df[org_name_df['financial_dataset']==source]['org_name'].apply(clean_fin_org_names))
        org_name_df['original_org_name'] = org_name_df['org_name']
        org_name_df['org_name'] = org_name_df['org_name'].apply(clean_fin_org_names)


    rdata_path = BASE_DIR + "data/org_counts.RData"

    print(f"Loading organization counts from: {rdata_path}")


    try:
        rdata_results = pyreadr.read_r(rdata_path)
        df = rdata_results[list(rdata_results.keys())[0]].copy()
    except Exception as e:
        print(f"Error loading RData file: {e}. Ensure pyreadr is installed and the path is correct.")
        sys.exit(1)
# --- END: Load RData Block ---

# 1. Clean and standardize the DataFrame to match the format expected by the rest of the script.

# Check the columns in the RData file and rename them to match the script's expected columns:
try:
    if 'org_name' in df.columns:
        df.rename(columns={'org_name': 'organization'}, inplace=True)
    else:
        print("Error: RData file does not contain the expected 'org_name' column.")

    df['comment_url'] = ""
except Exception as e:
    print(f"Error loading RData file: {e}. Ensure pyreadr is installed and the path is correct.")
    sys.exit(1)

df['submitter_name'] = ""
df['agency_acronym'] = "RDATA" # Placeholder
df['docket_id'] = ""
df['comment_title'] = ""

# Select only the columns the script expects later
cols = ['comment_url', 'submitter_name', 'organization', 'agency_acronym', 'docket_id', 'comment_title']
df = df[cols]

df['original_organization_name'] = df['organization']

# The following cleaning lines should be kept to ensure consistency, 
# even if the RData data is already partially clean.
# FRS, FDIC, SEC cleaning blocks are skipped for the RData sample.

# Clean the names using your function
df['submitter_name'] = df['submitter_name'].map(clean_fin_org_names)
df['organization'] = df['organization'].map(clean_fin_org_names)

# replace none
df.loc[df['submitter_name'].isna(), "submitter_name"] = ''

key_names_list = df.iloc[:,:] # This DataFrame is now your list of organizations to match

print("Finished cleaning with RData source.")

    


    # Make a (slightly) educated guess as to the submitter_name and organization for the Fed
"""
    new_key_names_list = []
    for elem in key_names_list:
        submitter_name = elem[1]
        org_name = elem[2]
        agency_acronym = elem[3]
        # TODO: we may need to consider the names
        # if agency_acronym == "FRS":
        #     comment_title = elem[5]
        #     if "(" in comment_title:
        #         comment_title = comment_title[:comment_title.index("(")].strip()
        #     clauses = comment_title.split(",")
        #     if len(clauses) == 0:
        #         clauses = comment_title.split(";")
        #     if len(clauses) == 0:
        #         pass
        #     elif len(clauses) == 1:
        #         org_name = clean_fin_org_names(clauses[0])
        #         submitter_name = org_name
        #     else:
        #         org_name = clean_fin_org_names(clauses[0])
        #         submitter_name = clean_fin_org_names(clauses[1])
        #     print(submitter_name + " | " + org_name)
        new_key_names = (elem[0], submitter_name, org_name, agency_acronym, elem[4])
        new_key_names_list.append(new_key_names)

    key_names_list = new_key_names_list
    """
print("Finished cleaning")


    # 1.3: Create 2 dicts with frequency counts of every token in the org and submitter name fields of the scraped comments db
    # submitter_frequency_dict = {}
    # org_frequency_dict = {}
    # for _, key_name in key_names_list.iterrows():
    #     org_name = key_name[2]
    #     for token in org_name.split(" "):
    #         if token in org_frequency_dict:
    #             org_frequency_dict[token] += 1
    #         else:
    #             org_frequency_dict[token] = 1



from collections import Counter
from tqdm.auto import tqdm # Keep tqdm if you want a progress bar on the split operation
tqdm.pandas()
print('Preparing candidate frequency dictionary (Vectorized).')
# 1. Split every string in the Series into a list of tokens.
token_lists = org_name_df['org_name'].progress_apply(lambda x: x.split(" "))

# 2. Flatten the list of lists into a single list of all tokens.
all_tokens = [token for sublist in token_lists for token in sublist]

# 3. Use Counter for fast, efficient frequency counting.
candidate_frequency_dict = Counter(all_tokens)
# Create linking dataset
# 1.4: Create a dict mapping from tokens in the gathered org datasets to IDs and org_names that contain that token
candidate_match_dict = {}
print('Preparing candidate match dictionary.')
for row_idx in tqdm(range(len(org_name_df))):
    row = org_name_df.iloc[row_idx]
    unique_id = row['unique_id']
    org_name = row['org_name']
    original_org_name = row['original_org_name']
    for token in org_name.split(" "):
        if token in candidate_match_dict:
            candidate_match_dict[token].append((unique_id, org_name, original_org_name))
        else:
            candidate_match_dict[token] = [(unique_id, org_name, original_org_name)]
                

    # Apply linking dataset
    # 1.5.1: For each org and submitter name in the scraped comment dataset, get all of the names ('candidate matches') from among the gathered org datasets that have the most important word of the scraped db names in the org's name. Calculate a tf-idf weighted jaccard index match score to choose the best matches among the candidates.
    print('Generating match dictionary.')
    match_dict = {}
    print("Num scraped records: " + str(len(key_names_list)))
    for key_name_idx in tqdm(range(len(key_names_list))):
        key_name = key_names_list.iloc[key_name_idx]
        org_name = key_name['organization']

        if not org_name:
            match_dict[org_name] = pd.DataFrame()
            continue

        if org_name in match_dict:
            continue

        # Tokenize the submitter name and org name
        org_tokens = org_name.split(" ")
        
        # Get the frequencies (in the scraped comment db) of the tokens in the submitter name and org name
        # submitter_token_frequencies = sorted([(submitter_token, submitter_frequency_dict[submitter_token]) for submitter_token in submitter_tokens], key=lambda x: x[1])
        org_token_frequencies = [(org_token, candidate_frequency_dict.get(org_token)) for org_token in org_tokens]
        org_token_frequencies = list(filter(lambda item: item[1] is not None, org_token_frequencies))
        org_token_frequencies = sorted(org_token_frequencies, key=lambda x: x[1])
        

        candidate_matches = []
        # Iterate through the candidate matches to the most informative token
        for most_unique_org_token, _ in org_token_frequencies[:1]: # uses top 2 most unique tokens
            if most_unique_org_token in candidate_match_dict:
                for row in candidate_match_dict[most_unique_org_token]:
                    unique_id = row[0]
                    candidate_match_name = row[1]
                    original_candidate_match_name = row[2]
                    match_score = get_match_candidate_score(candidate_frequency_dict, org_name, candidate_match_name)
                    candidate_matches.append((match_score, candidate_match_name, original_candidate_match_name, unique_id))

        # Sort the candidate matches, first by the match score and then by the absolute value of the difference in the number of tokens between the submitter (or org) name and the candidate match org name
        candidate_matches.sort(key=lambda x:(-x[0], abs(len(x[1].split(" ")) - len(org_tokens))))
        candidate_matches = pd.DataFrame(candidate_matches, columns=['match_score','candidate_match_name', 'original_org_name', 'unique_id'])
        #TODO: remove submitters
        # candidate_matches_list.append([])
        # candidate_matches_list.append(candidate_matches)


        # Record the candidate matches corresponding to the current scraped comment record
        match_dict[org_name] = candidate_matches


    # 1.5.2: Save the candidate matches and get record counts
    # with open(BASE_DIR + "data/finreg_jaccard_match_" + curr_date + ".pkl", 'wb') as pkl_out:
    #     pickle.dump(match_dict, pkl_out)

    print("Num scraped records: " + str(len(key_names_list)))


    # 1.6: Extract the scraped records with at least one candidate match and take the top top_matches_num (or all if there are < top_matches_num) matches from the scored candidate matches
    # DONE: loop until we get top match from each dataset
    threshold = 0.95
    counter = 0
    match_counter = 0
    good_matches = {}
    for elem_idx, elem in tqdm(list(enumerate(match_dict))):

        # Org name
        good_org_matches = []
        collected_sources = set()
        matches = match_dict[elem]

        if len(matches) == 0:
            counter += 1   


        if len(collected_sources) == len(sources):
            break

        for match_candidate_idx in range(len(matches)):
            match_candidate = matches.iloc[match_candidate_idx]
            if len(collected_sources) == len(sources):
                break
            match_candidate_source = match_candidate['unique_id'].split('-')[0]
            if not match_candidate_source in collected_sources:
                good_org_matches.append(match_candidate)
                collected_sources.add(match_candidate_source)

        good_matches[elem] = good_org_matches
            
    print("Num records in match_dict: " + str(len(match_dict)))
    print("Num records without a match: " + str(counter))
    print("Share of records that weren't matchable: " + str(counter / len(match_dict)))


    ## PART 2: Attempt to estimate whether comment was submitted by a person or an organization
    nlp = en_core_web_lg.load()

    # 2.1: Among the matchable scraped comment records, use spacy's ner tagger to tag the tokens in the submitter name and org name of each record. 
    good_matches_org_tagged = {}
    num_likely_orgs = 0
    for elem_idx, elem in tqdm(list(key_names_list.iterrows())):
        # Consider an org name to likely be a person if the submitter's name isn't empty and if at least one of its tokens gets tagged as corresponding to a person
        tagged_org_name = []
        likely_org_check = 1
        if elem['organization'] is not None:
            tagged_org_name = nlp(elem['organization'])
            if "PERSON" in [tag.label_ for tag in tagged_org_name.ents]:
                likely_org_check = 0

        # Default to considering a record to have been submitted by an org
        likely_org = 1
        # BUT, consider the record to have been submitted by a person if the name fields aren't empty and at least one token of each name field was tagged as a person
        if elem['submitter_name'] is not None and elem['organization'] is not None and elem['submitter_name'] != "" and elem['organization'] != "" and likely_org_check == 0:
            likely_org = 0
        # Also consider the record to have been submitted by a person if only one of the name fields was empty and the other had at least one token of each name field was tagged as a person
        if (elem['submitter_name'] is None or elem['submitter_name'] == "") and (elem['organization'] is not None and elem['organization'] != "") and likely_org_check == 0:
            likely_org = 0
        # (Same as above case but switching which name was empty)
        if (elem['organization'] is None or elem['organization'] == "") and (elem['submitter_name'] is not None and elem['submitter_name'] != ""):
            likely_org = 0        
        # Also consider the record to have been submitted by a person if the submitter name field has "anonymous anonymous" in it and the org name field is empty
        if "anonymous anonymous" in elem['submitter_name'] and (elem['organization'] is None or elem['organization'] == ""):
            likely_org = 0
            
        num_likely_orgs += likely_org
        
        good_matches_org_tagged[tuple(elem.values)] = (good_matches[elem['organization']], (likely_org, [X.label_ for X in tagged_org_name.ents]))
        
        

    ## PART 3: Create a data from to explore commenter covariates
    covariate_dfs = get_covariate_dfs()

    # 3.2: Make a dataframe organizing the covariates of the gathered datasets
    covariate_dict = {}
    frs_counter = 0
    for elem_idx, elem in tqdm(list(key_names_list.iterrows())):
        elem = tuple(elem)
        url = elem[0]
        submitter_name = elem[1]
        org_name = elem[2]
        agency_acronym = elem[3]
        if agency_acronym == "FRS":
            frs_counter += 1
        docket_id = elem[4]
        comment_title = elem[5]
        original_org_name = elem[6]

        matches = good_matches_org_tagged[elem][0]
        tag_data = good_matches_org_tagged[elem][1]
        is_likely_org = tag_data[0]
        org_tags = tag_data

        
        org_match_covariate_dict = {}
        org_match_type = ""
        org_best_match_score = np.nan

        org_matches_collected = []
        org_types_collected = []
        if len(matches) > 0:
            for match in matches:
                org_best_match = match
                org_best_match_id = org_best_match['unique_id']
                org_match_type = org_best_match_id.split("-")[0]
                if not org_match_type in org_types_collected:
                    org_matches_collected.append(match)
                    org_types_collected.append(org_match_type)

            for org_match in org_matches_collected:
                org_best_match = org_match
                org_best_match_id = org_best_match['unique_id']
                org_best_match_name = org_best_match['candidate_match_name']
                original_best_match_name = org_best_match['original_org_name']
                org_best_match_score = clean_match_score(org_best_match['match_score'])
                if pd.isnull(org_best_match_score):
                    print("this shouldn't be null")
                org_match_type = org_best_match_id.split("-")[0]
                org_match_row_num = org_best_match_id.split("-")[1]
                org_match_covariate_dict.update(get_data_row(org_match_type, int(org_match_row_num), "orgMatch"))
                org_match_covariate_dict[org_match_type + '-orgMatch' + ":best_match_score"] = org_best_match_score
                org_match_covariate_dict[org_match_type + '-orgMatch' + ":best_match_name"] = org_best_match_name
                org_match_covariate_dict[org_match_type + '-orgMatch' + ":original_match_name"] = original_best_match_name

        
        covariate_dict[elem] = {**org_match_covariate_dict}
        covariate_dict[elem]['original_org_name'] = original_org_name
        covariate_dict[elem]['comment_url'] = url
        covariate_dict[elem]['comment_submitter_name'] = submitter_name
        covariate_dict[elem]['comment_org_name'] = org_name
        covariate_dict[elem]['comment_agency'] = agency_acronym
        covariate_dict[elem]['docket_id'] = docket_id
        covariate_dict[elem]['is_likely_org'] = is_likely_org
        covariate_dict[elem]['org_tags'] = str(org_tags)
        covariate_dict[elem]['org_match_type'] = org_match_type
        covariate_dict[elem]['org_best_match_score'] = org_best_match_score  

        covariate_dict[elem]['num_org_matches'] = len(org_matches_collected)


    print("FRS counter: " + str(frs_counter))
    print("Finished creating data dicts")

    variables = set()
    for elem_idx, elem in tqdm(enumerate(covariate_dict)):
        variables = variables.union(set(covariate_dict[elem].keys()))
    variables = list(variables)
    variables.sort()
    print("Finished establishing variables")

    data = []
    for elem_idx, elem in tqdm(enumerate(covariate_dict)):
        elem_data_dict = covariate_dict[elem]
        elem_data_row = [None]*len(variables)
        for var_idx, variable in enumerate(variables):
            if variable in elem_data_dict:
                elem_data_row[var_idx] = elem_data_dict[variable]
        data.append(elem_data_row)
        # if elem_idx % 10000 == 0:
        #     print(elem_idx)
    print("Finished creating items for df")

    covariate_df = pd.DataFrame(data, columns=variables)

    # 3.3: Save the dataframe of scraped records with attached covariates

    # filter columns
    common_tails = ['best_match_name',
                    'original_match_name', 
                    'best_match_score', 
                    'CIK', 
                    'CU_NUMBER', 
                    'RSSD', 
                    'CERT', 
                    'FED_RSSD',
                    'FDIC Certificate Number',
                    'IDRSSD',
                    'OCC Charter Number',
                    'SIC',
                    'Ticker',
                    'cik',
                    'cusip',
                    'gvkey',
                    'naics',
                    'sic',
                    'tic',
                    'ein',
                    'name',
                    'parentID'
                    ]
    important_cols = ['original_org_name',
                      'num_org_matches', 
                      'num_submitter_matches', 
                      'comment_agency',
                      'comment_org_name',
                      'comment_submitter_name',
                      'docket_id',
                      'comment_url',]
    important_cols = [x for x in covariate_df.columns if (x.split(':')[-1] in common_tails) or (x in important_cols)]
    covariate_df= covariate_df[important_cols]

    # reorder columns
    cols = covariate_df.columns
    cols = [x for x in cols if not ':' in x] + [x for x in cols if ':' in x]
    covariate_df= covariate_df[cols]

    # write df
    with open(BASE_DIR + "data/finreg_commenter_covariates_df_" + curr_date + ".pkl", 'wb') as pkl_out:
        pickle.dump(covariate_df, pkl_out)

    covariate_df.to_csv(BASE_DIR + "data/finreg_commenter_covariates_df_" + curr_date + ".csv")

    df = covariate_df
    df = df[list(filter(lambda x: not "submitter" in x,df.columns))]
    # df = df[df['comment_org_name']!='']
    df.to_csv(BASE_DIR + "data/match_data/match_all_covariates_df_" + curr_date + ".csv")

    df = pd.read_csv(BASE_DIR + "data/match_data/match_all_covariates_df_" + curr_date + ".csv")
    df = df.drop("Unnamed: 0", axis=1)

    #isolating low scores
    score_cols = [col for col in df.columns if "best_match_score" in col]
    df['max_match_score'] = df[score_cols].fillna(-100).max(axis = 1)
   
    LOWER_BOUND = 0.50
    UPPER_BOUND = 0.60
    
    # Filter for scores in the moderate range and ensures the score is positive
    filter_condition = (df['max_match_score'] > LOWER_BOUND) & \
                       (df['max_match_score'] < UPPER_BOUND) & \
                       (df['max_match_score'] > 0)
    
    df = df[filter_condition].copy()
    
    print(f"Filtered DataFrame down to {len(df)} records (0.80 < score < 0.90).")

    #Add Exact Match column
    name_cols = list(filter(lambda x: "best_match_name" in x,df.columns))
    exact_matches = pd.DataFrame()
    for name_col in name_cols:
        exact_matches[name_col] = df[name_col]==df['comment_org_name']

    new_col = (exact_matches.sum(axis=1)>0).astype(int)
    df['exact_match_present'] = new_col
    
    #Reorder columns (Adjusted to include 'max_match_score' in the front)
    cols = list(df.columns)
    front = [
        'comment_agency',
        'original_org_name',
        'comment_url',
        'docket_id',
        'comment_org_name',
        'num_org_matches',
        'exact_match_present',
        'max_match_score', 
        ]
    
    # Recreate the final column list by ensuring the front columns are first
    remaining_cols = [c for c in cols if c not in front]
    df = df[front + remaining_cols]


    final_filename = f"match_df_moderate_sample_{int(LOWER_BOUND*100)}_{int(UPPER_BOUND*100)}_" + curr_date + ".csv"
    df.to_csv(BASE_DIR + "data/match_data/" + final_filename, index=False)
    print(f"Saved moderate sample to: {final_filename}")