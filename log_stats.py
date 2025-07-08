# generic stats

def get_att_presence(col, log):
    print('total:', len(log[col]))
    print('unique:', len(log[col].unique()))
    print('na:', len(log[log[col].isna()]))
    print('not na:', len(log[log[col].notna()]))
    
def get_relation_details(col1, col2, log, verbose=False):
    dir1 = get_dir_relation_details(col1, col2, log, verbose)
    dir2 = get_dir_relation_details(col2, col1, log, verbose)
    print(f"{dir1}-{dir2}")

def get_dir_relation_details(col_from, col_to, log, verbose=False):
    groups = log.groupby(col_from)[col_to].unique()
    nums = groups.apply(len)
    num_many = len(nums[nums > 1])
    if verbose:
        num_total = len(log[col_from].unique())
        print(f"{num_many} (out of {num_total}) {col_from} with many {col_to}")
    return 'many' if len(nums[nums > 1]) > 1 else 'one'


# stats for events

# count total number of occurrences of events (absolute & percentage)
def count_events(evt_col, case_col, log, plot=True):
    total_evts = len(log[evt_col])
    evt_counts = log.groupby(evt_col)[case_col].count().rename('cnt').to_frame()
    evt_counts['perc'] = 100 / total_evts * evt_counts['cnt']
    evt_counts = evt_counts.sort_values(by='perc', ascending=False)
    # for idx, row in evt_counts.items():
    #     print(idx, row[0], row[1])
    if plot:
        ax = evt_counts[['perc']].plot.bar()
        ax.xaxis.set_visible(False)
    return evt_counts

# per event, count number of cases that it occurs in (absolute & percentage)
def count_cases_per_event(evt_col, case_col, log, plot=True):
    total_cases = len(log[case_col].unique())
    evts_cases = log.groupby(evt_col)[case_col].unique().rename('cases').to_frame()
    evts_cases['cases'] = evts_cases['cases'].apply(len)
    evts_cases['perc'] = 100 / total_cases * evts_cases['cases']
    evt_cases = evts_cases.sort_values(by='perc', ascending=False)
    if plot:
        ax = evt_cases[['perc']].plot.bar()
        ax.xaxis.set_visible(False)
    return evt_cases

# filter log
def filter_events_on_counts(evt_col, leq_perc, counts, log):
    keep_evts = counts[counts['perc']>leq_perc].index.array
    return log[log[evt_col].isin(keep_evts)]


# stats for traces

def get_trace_lengths(evt_col, case_col, log, plot=True):
    trace_lens = log.groupby(case_col)[evt_col].count()
    trace_lens = trace_lens.sort_values(ascending=False)
    # for idx, cnt in trace_lens.items():
    #     print(idx, cnt)
    if plot:
        ax = trace_lens.plot.bar()
        ax.xaxis.set_visible(False)
    return trace_lens