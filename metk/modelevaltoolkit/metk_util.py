#!/usr/bin/env python

from __future__ import print_function
import sys
import math
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from scipy.stats import norm
from scipy.stats import spearmanr

def rmse(pred_array, ref_array):
    """
    Calculate root mean squared (rms) error
    :param pred_array: the predicted values
    :param ref_array: the reference values
    :return: the rms error
    """
    return np.sqrt(np.mean((pred_array - ref_array) ** 2))


def mean_absolute_error(pred_array, ref_array):
    """
    Calculate mean absolute error
    :param pred_array: the predicted values
    :param ref_array: the reference values
    :return: the mean absolute error
    """
    return np.mean(np.abs(pred_array - ref_array))


def get_unit_multiplier(units):
    """
    Function so that I only have to put the unit dictionary in one place
    :param: units: units
    :return: unit dictionary
    """
    multiplier_dict = {"M": 1, "mM": 1e-3, "uM": 1e-6, "nM": 1e-9}
    try:
        multiplier = multiplier_dict[units]
        return multiplier
    except KeyError:
        print("Error:", units, "is not supported in ki_to_kcal")
        sys.exit(0)


def ki_to_kcal(ic50, units="uM"):
    """
    convert a Ki or IC50 value in M to kcal/mol
    :param units: units
    :param ic50: IC50 value in M
    :return: IC50 value converted to kcal/mol
    """
    multiplier = get_unit_multiplier(units)
    return math.log(ic50 * multiplier) * 0.5961


def kcal_to_ki(kcal, units="uM"):
    """
    Convert a binding energy in kcal to a Ki or IC50 value
    :param kcal: binding energy in kcal/mol
    :param units: units for the return value
    :return: binding energy as Ki or IC50
    """
    multiplier = get_unit_multiplier(units)
    return math.exp(kcal / 0.5961) / multiplier


def pearson_confidence(r, num, interval=0.95):
    """
    Calculate upper and lower 95% CI for a Pearson r
    Inspired by https://stats.stackexchange.com/questions/18887
    :param r: Pearson's R
    :param num: number of data points
    :param interval: confidence interval (0-1.0)
    :return: lower bound, upper bound
    """
    stderr = 1.0 / math.sqrt(num - 3)
    z_score = norm.ppf(interval)
    delta = z_score * stderr
    lower = math.tanh(math.atanh(r) - delta)
    upper = math.tanh(math.atanh(r) + delta)
    print('lower=', lower)
    print('upper=', upper)
    return lower, upper

def spearman_confidence(rho, num, interval=0.95):
    """ 
    Calculate upper and lower 95% CI for a spearman (not R**2)
    Inspired by https://stats.stackexchange.com/questions/18887
    :param r: spearman's rho
    :param num: number of data points
    :param interval: confidence interval (0-1.0)
    :return: lower bound, upper bound
    """
    stderr = 1.0 / math.sqrt(num - 3)
    z_score = norm.ppf(interval)
    delta = z_score * stderr
    lower = math.tanh(math.atanh(rho) - delta)
    upper = math.tanh(math.atanh(rho) + delta)
    return lower, upper


def max_possible_correlation(vals, error=1 / 3.0, method=pearsonr, cycles=1000):
    """
    Calculate the maximum possible correlation given a particular experimental error
    Based on Brown, Muchmore, Hajduk http://www.sciencedirect.com/science/article/pii/S1359644609000403
    :param vals: experimental values (should be on a log scale)
    :param error: experimental error
    :param method: method for calculating the correlation, must take 2 lists and return correlation and p_value
    :param cycles: number of random cycles
    :return: maximum possible correlation
    """
    cor_list = []
    for i in range(0, cycles):
        noisy_vals = []
        for val in vals:
            noisy_vals.append(val + np.random.normal(0, error))
        cor_list.append(method(vals, noisy_vals)[0])
    return np.mean(cor_list)


def kcal_to_ki_df(df, units="uM"):
    """
    Convert a data frame with values in kcal/mol to a dataframe with Ki values
    :param df: input dataframe with units of kcal/mol
    :param units: units to use (passed to kcal_to_ki)
    :return: new dataframe with Pred and Exp expressed as a Ki (or IC50)
    """
    new_df = pd.DataFrame(df)
    new_df['Pred'] = [kcal_to_ki(x, units) for x in df['Pred']]
    new_df['Exp'] = [kcal_to_ki(x, units) for x in df['Exp']]
    return new_df


def ki_to_kcal_df(df, units="uM"):
    """
    Convert a data frame with values as IC50 or Ki to a dataframe with values in kcal/mol
    :param df: input dataframe with data expressed as Ki or Ic50
    :param units: units to use (passed to ki_to_kcal)
    :return: new dataframe with Pred and Exp expressed in kcal/mol
    """
    new_df = pd.DataFrame(df)
    new_df['Pred'] = [ki_to_kcal(x, units) for x in df['Pred']]
    new_df['Exp'] = [ki_to_kcal(x, units) for x in df['Exp']]
    return new_df


def check_dataframe(df):
    """
    Check a dataframe to ensure that we have columns called "Pred" and "Exp"
    :param df: input dataframe
    :return: no return value, exits on error
    """
    cols = df.columns
    if "Pred" not in cols:
        print('Input Error: Your input file does not have a column named "Pred"', file=sys.stderr)
        sys.exit(0)
    if "Exp" not in cols:
        print('Input Error: Your input file does not have a column named "Exp"', file=sys.stderr)
        sys.exit(0)


def test():
    """
    Stupid test function
    :return:
    """
    df = pd.read_csv(sys.argv[1])
    n_row, n_col = df.shape
    pred = np.log10(df['Pred'])
    expr = np.log10(df['Exp'])
    #   for idx,(e,p) in enumerate(zip(pred,expr),1):
    #        print("MOL%03d" % idx,"%0.3f %0.3f" % (kcal_to_ki(e),kcal_to_ki(p)))
    print("rmse = ", rmse(pred, expr))
    pearson_p, pearson_cor = pearsonr(pred, expr)
    spearman_p, spearman_cor = spearmanr(pred, expr)
    print('Printing pearson_p', pearson_p)
    print('Printing pearson_cor', pearson_cor)
    print(pearson_confidence(pearson_cor, n_row))
    print(spearman_confidence(spearman_cor, n_row))
    print(max_possible_correlation(expr))
    print(ki_to_kcal(8, "nM"))
    print(kcal_to_ki(-11.11, "nM"))


if __name__ == "__main__":
    test()
