"""
Partial-equilibrium elasticity-based Behavioral-Responses results
returned as expected by TaxBrain.
"""
# CODING-STYLE CHECKS:
# pycodestyle tbi.py
# pylint --disable=locally-disabled tbi.py

import numpy as np
import taxcalc as tc
from behresp.behavior import response


def run_nth_year_behresp_model(year_n, start_year,
                               use_puf_not_cps,
                               use_full_sample,
                               user_mods,
                               elasticities,
                               return_dict=True):
    """
    Implements TaxBrain "Partial Equilibrium Simulation" dynamic analysis
    returning behavioral-response results as expected by TaxBrain.

    The first five and the last function arguments are the same as for the
      run_nth_year_taxcalc_model function in the Tax-Calculator repository.
    The run_nth_year_behresp_model function assumes elasticities is a
      dictionary (containing the assumed values of the behavioral-response
      elasticities) that can be passed to the Behavioral-Responses.response
      function.
    """
    # pylint: disable=too-many-arguments,too-many-statements
    # pylint: disable=too-many-locals,too-many-branches
    assert isinstance(user_mods, dict)
    assert isinstance(elasticities, dict)

    # create calc1 and calc2 for year_n
    tc.tbi.check_years(year_n, start_year, use_puf_not_cps)
    calc1, calc2 = tc.tbi.calculators(year_n, start_year,
                                      use_puf_not_cps, use_full_sample,
                                      user_mods)

    # extractf unfuzzed raw results from calc1 and calc2-with-response
    dv1, dv2 = response(calc1, calc2, elasticities)

    # delete calc1 and calc2 now that raw results have been extracted
    del calc1
    del calc2

    # construct TaxBrain summary results from raw results
    sres = dict()
    fuzzing = use_puf_not_cps
    if fuzzing:
        # seed random number generator with a seed value based on user_mods
        # (reform-specific seed is used to choose whose results are fuzzed)
        seed = tc.tbi.random_seed(user_mods)
        print('fuzzing_seed={}'.format(seed))
        np.random.seed(seed)
        # make bool array marking which filing units are affected by the reform
        # pylint: disable=assignment-from-no-return
        reform_affected = np.logical_not(
            np.isclose(dv1['combined'], dv2['combined'], atol=0.01, rtol=0.0)
        )
        agg1, agg2 = tc.tbi.fuzzed(dv1, dv2, reform_affected, 'aggr')
        sres = tc.tbi.summary_aggregate(sres, agg1, agg2)
        del agg1
        del agg2
        dv1b, dv2b = tc.tbi.fuzzed(dv1, dv2, reform_affected, 'xbin')
        sres = tc.tbi.summary_dist_xbin(sres, dv1b, dv2b)
        sres = tc.tbi.summary_diff_xbin(sres, dv1b, dv2b)
        del dv1b
        del dv2b
        dv1d, dv2d = tc.tbi.fuzzed(dv1, dv2, reform_affected, 'xdec')
        sres = tc.tbi.summary_dist_xdec(sres, dv1d, dv2d)
        sres = tc.tbi.summary_diff_xdec(sres, dv1d, dv2d)
        del dv1d
        del dv2d
        del reform_affected
    else:
        sres = tc.tbi.summary_aggregate(sres, dv1, dv2)
        sres = tc.tbi.summary_dist_xbin(sres, dv1, dv2)
        sres = tc.tbi.summary_diff_xbin(sres, dv1, dv2)
        sres = tc.tbi.summary_dist_xdec(sres, dv1, dv2)
        sres = tc.tbi.summary_diff_xdec(sres, dv1, dv2)

    # nested function used below
    def append_year(dframe):
        """
        append_year embedded function revises all column names in dframe
        """
        dframe.columns = [str(col) + '_{}'.format(year_n)
                          for col in dframe.columns]
        return dframe

    # optionally return non-JSON-like results
    if not return_dict:
        res = dict()
        for tbl in sres:
            res[tbl] = append_year(sres[tbl])
        return res

    # optionally construct JSON-like results dictionaries for year n
    dec_rownames = list(sres['diff_comb_xdec'].index.values)
    dec_row_names_n = [x + '_' + str(year_n) for x in dec_rownames]
    bin_rownames = list(sres['diff_comb_xbin'].index.values)
    bin_row_names_n = [x + '_' + str(year_n) for x in bin_rownames]
    agg_row_names_n = [x + '_' + str(year_n) for x in tc.tbi.AGG_ROW_NAMES]
    dist_column_types = [float] * len(tc.tbi.DIST_TABLE_LABELS)
    diff_column_types = [float] * len(tc.tbi.DIFF_TABLE_LABELS)
    info = dict()
    for tbl in sres:
        info[tbl] = {'row_names': [], 'col_types': []}
        if 'dec' in tbl:
            info[tbl]['row_names'] = dec_row_names_n
        elif 'bin' in tbl:
            info[tbl]['row_names'] = bin_row_names_n
        else:
            info[tbl]['row_names'] = agg_row_names_n
        if 'dist' in tbl:
            info[tbl]['col_types'] = dist_column_types
        elif 'diff' in tbl:
            info[tbl]['col_types'] = diff_column_types
    res = dict()
    for tbl in sres:
        if 'aggr' in tbl:
            res_table = tc.tbi.create_dict_table(
                sres[tbl], row_names=info[tbl]['row_names'])
            res[tbl] = dict((k, v[0]) for k, v in res_table.items())
        else:
            col_types_info = info[tbl]['col_types']
            res[tbl] = tc.tbi.create_dict_table(
                sres[tbl], row_names=info[tbl]['row_names'],
                column_types=col_types_info)
    return res
