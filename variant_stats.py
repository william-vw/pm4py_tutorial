import pandas as pd
import pm4py
from collections import Counter
from collections_extended import frozenbag
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.obj import EventLog

# from pm4py.algo.filtering.log.variants.variants_filter import filter_log_variants_percentage
# from pm4py.objects.conversion.log.variants import to_data_frame

def get_variants(log, unordered=False, verbose=False):
    if verbose:
        print("# total:", len(log['case:concept:name'].unique()))
    
    variants = log.groupby('case:concept:name')['concept:name'].agg(tuple).to_dict()
    variants = Counter(variants.values())
    
    if verbose:
        print("# unique variants:", len(list(variants.keys())))
    if unordered:
        unvariants = { frozenbag(variant): 0 for variant in variants.keys() }
        for variant_series, cov_amt in variants.items():
            unvariants[frozenbag(variant_series)] += cov_amt
        if verbose:
            print("# unique unordered variants:", len(unvariants))
        return unvariants
    else:
        return variants

def get_variant_ratio(log, vars_stats):
    num_traces = len(log['case:concept:name'].unique())
    num_vars = vars_stats.shape[0]
    var_ratio = round((num_vars / num_traces) * 100, 2)
    return f"# traces = {num_traces}, # vars = {num_vars}, ratio = {var_ratio}"

def get_variants_stats(log, plot=True):
    variants = get_variants(log, unordered=False)
    variants = pd.DataFrame(variants.items())
    num_seq = len(log['case:concept:name'].unique())
    num_var = variants.shape[0]
    
    variants.columns = ['sequence', 'cov_amt']

    variants_sorted = variants.sort_values(by = 'cov_amt', ascending=False)
    variants_sorted = variants_sorted.reset_index(drop=True)
    variants_sorted['cov_perc'] = variants_sorted.apply(lambda row: 100 / num_seq * row['cov_amt'], axis=1)

    cumul_cov_perc = []
    cur_cov_perc = 0
    for _, row in variants_sorted.iterrows(): # yeah, yeah ...
        cur_cov_perc += row['cov_perc']
        cumul_cov_perc.append(cur_cov_perc)
    variants_sorted['cov_perc_cumul'] = cumul_cov_perc

    var_perc = 100 / num_var
    variants_sorted['var_perc_cumul'] = variants_sorted.apply(lambda row: (row.name + 1) * var_perc, axis=1)

    if plot:
        ax = variants_sorted[['cov_perc']].plot.bar()
        ax.xaxis.set_visible(False)

    return variants_sorted

def print_variants_stats(vars_stats):
    for idx, row in vars_stats.iterrows():
        print(f"coverage: amt = {row['cov_amt']}, perc = {row['cov_perc']}, cumul = {row['cov_perc_cumul']}")
        print(f"variant: cnt = {row.name}, perc = {row['var_perc_cumul']}")
        print(row['sequence'])


# how many cases (percentage) do var_perc of variants (sorted desc by coverage) cover?
def get_case_coverage(var_perc, vars_stats):
    return get_x_coverage(var_perc, 'var_perc_cumul', 'cov_perc_cumul', vars_stats)


# how many variants (percentage) are needed (sorted desc by coverage) to cover case_perc of cases?
def get_variant_coverage(case_perc, vars_stats):
    return get_x_coverage(case_perc, 'cov_perc_cumul', 'var_perc_cumul', vars_stats)


# get all variants that are needed (sorted desc by coverage) to cover case_perc of cases
def get_covering_variants(case_perc, vars_stats):
    first_k = vars_stats.loc[vars_stats['cov_perc_cumul'] <= case_perc]
    return first_k


def get_x_coverage(perc, cmp_col, ret_col, vars_stats):
    first_k = vars_stats.loc[vars_stats[cmp_col] <= perc]
    return first_k.iloc[-1][ret_col]
    
    
def filter_traces_on_variants(log, variants):
    traces = log.groupby('case:concept:name')['concept:name'].apply(tuple).rename('sequence').reset_index()
    # add case's sequence to all events of that case
    merged_log = log.merge(traces) # will merge on case:concept:name
    
    # filter all events with a sequence found in variants
    filtered_log = merged_log[merged_log['sequence'].isin(variants['sequence'])]
    filtered_log = filtered_log[['case:concept:name', 'concept:name', 'time:timestamp']]
    
    return filtered_log