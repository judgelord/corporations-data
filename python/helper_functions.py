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


# function to clean org names for exact standardized name matching
def to_standardized_name(name: str) -> str:
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


# Function to clean aliases by removing corporation suffixes 
# and other symbols for more accurate regular expression matching
def clean_org_alias(name: str) -> str:
    # if name is None or not isinstance(name, str) or name == "NA":
    #     return ""
    
    # # Unicode & PDF cleanup
    # name = PDF_PATTERN_RE.sub("", name)
    # name = corp_simplify_utils.normalize_unicode(name)

    # # Remove corporate suffixes
    # name = CORP_SUFFIX_RE.sub("", name)

    # # Remove punctuations
    # name = PUNCT_RE.sub(" ", name)
    
    # # Final cleanup of spaces
    # name = MULTISPACE_RE.sub(" ", name).strip().lower()

    # return name
    
    if name is None or not isinstance(name, str) or name == "NA":
        return ""

    # Unicode & PDF cleanup
    name = corp_simplify_utils.normalize_unicode(name)
    name = PDF_PATTERN_RE.sub("", name)

    # normalizing to lowercase
    name = name.lower()

    # Remove corporate suffixes
    name = CORP_SUFFIX_RE.sub("", name)

    # Remove punctuation & symbol noise
    # punc2_re already handles:
    # () [] {} quotes, dashes, slashes, punctuation, unicode quotes
    name = punc2_re.sub(" ", name)

    # Normalize commas 
    name = re.sub(r"\s*(?:,\s*)+", ", ", name)

    # Final cleanup of spaces
    name = MULTISPACE_RE.sub(" ", name).strip()

    return name

    
    
def normalize_to_list(x):
    if pd.isna(x):
        return []
    if isinstance(x, list):
        return [int(i) for i in x]  # convert to int
    return [int(x)]


# This function is used to clean the cik values into a string,
# so that the merge function can be properly called. 
def clean_cik(value):
    # If it's a list, take the first element
    if isinstance(value, list):
        if len(value) > 0:
            value = value[0]
        else:
            return ""
    
    # If it's null, return an empty string
    if pd.isna(value) or value == "":
        return ""
    
    # Convert the value to float, then int, then string to remove the '.0'
    try:
        return str(int(float(value)))
    except (ValueError, TypeError):
        return str(value)
