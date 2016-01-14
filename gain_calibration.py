"""some useful functions for sipm gain calibration"""

import numpy as np
from matplotlib import pyplot as plt
from ROOT import TFile, gROOT, gStyle
import sys


def sig_from_diag(x, U, vals):
    """get uncertainty by diagonalizing covariance matrix"""
    p_comps = np.dot(
        U, [x**(len(U) - (i+1)) for i, _ in enumerate(U)])
    return np.sqrt(np.sum(p_comp**2*val for p_comp, val in zip(p_comps, vals)))


def poly(x, coeffs):
    """evaluate polynomial function defined by
    coeffs from np.polyfit at x values"""
    return np.sum([c*x**(len(coeffs) - (i+1))
                   for i, c in enumerate(coeffs)], 0)


def fit_distribution(run_num, attr='sipm1.threeSampleAmpl', draw=False):
    """give an output file number from fitter,
    fit peak to find mean and variance with their errors"""
    in_file = TFile("/home/newg2/Workspace/L1Tests/crunchedFiles/labrun_%05i_crunched.root" % run_num)
    tree = in_file.Get("t")
    tree.Draw("%s>>h1(200)" % attr, "", "goff")
    hist = gROOT.FindObject("h1")
    mean = hist.GetMean()
    std = hist.GetRMS()
    low = mean - 3*std
    high = mean + 3*std
    tree.Draw("%s>>h2(100,%s,%s)" %
              (attr, str(low), str(high)), "", "goff")
    hist = gROOT.FindObject("h2")
    hist.Fit("gaus", "0q")
    func = hist.GetFunction("gaus")
    out = (func.GetParameter(1), func.GetParameter(2),
           func.GetParError(1), func.GetParError(2))
    if draw:
        gStyle.SetOptFit(1)
        hist.Draw()
        hist.GetFunction("gaus").Draw("same")
        raw_input('any key to continue')
    in_file.Close()
    return out


def fit_gain(run_numbers, make_plot=False,
             attr='threeSampleAmpl', file_name='',
             plot_title=''):
    """given list of run numbers, fit with 2nd order polynomial.
    returns parameters and their errors in tuple,
    followed by np array of means, variances, variance errors"""
    means = []
    variances = []
    var_errors = []
    for run in run_numbers:
        mean, sig, mean_err, sig_err = fit_distribution(run, attr=attr)
        means.append(mean)
        variances.append(sig*sig)
        var_errors.append(2*sig*sig_err)

    means = np.array(means)
    variances = np.array(variances)
    var_errors = np.array(var_errors)
    coeffs, cov = np.polyfit(means, variances, 2, w=1.0/var_errors, cov=True)

    if make_plot:
        line_xs = np.linspace(0, np.max(means)*1.2, 1000)
        line_ys = poly(line_xs, coeffs)
        plt.errorbar(means, variances, yerr=var_errors, fmt="bo", markersize=7)
        vals, vecs = np.linalg.eig(cov)
        U = np.transpose(vecs)
        sigs = sig_from_diag(line_xs, U, vals)

        plt.fill_between(line_xs, line_ys + sigs,
                         line_ys - sigs, facecolor='r',
                         alpha=0.5)

        plt.plot(line_xs, line_ys, 'r-')
        plt.xlim(0, max(line_xs))
        chi2 = np.sum(
            (variances - poly(means, coeffs))**2/(var_errors**2)) /\
            (len(means) - len(coeffs))

        rounded_params = []
        rounded_errs = []
        for err, coeff in zip(np.sqrt(np.diagonal(cov)), coeffs):
            precision = np.log10(err)
            rounded_errs.append(round(err, -1*int(np.floor(precision))))
            rounded_params.append(round(coeff, -1*int(np.floor(precision))))

        par_string = ''.join(['$p_%i$ : %s $\pm$ %s\n'
                              % (len(coeffs) - (i+1), c, e)
                              for i, (c, e) in
                              enumerate(zip(rounded_params, rounded_errs))])

        pe_at_max = max(means)/coeffs[1]
        plt.annotate(s='%i pe at max\n\n${\chi^2/ndf}$ : %.1f\n%s'
                     % (int(pe_at_max), chi2, par_string),
                     xy=(0.1, 0.5), xycoords='axes fraction', fontsize=16)

        plt.xlabel('mean', fontsize=16, fontweight='bold')
        plt.ylabel('variance', fontsize=16, fontweight='bold')
        if len(plot_title) > 0:
            plt.title(str(plot_title))
        if len(file_name) > 0:
            plt.savefig('%s.pdf' % file_name)
        plt.show()

    # tuple is gain, quad term, noise term, and then their errors
    out_tuple = (coeffs[1], coeffs[0],
                 coeffs[2], np.sqrt(cov[1, 1]),
                 np.sqrt(cov[0, 0]), np.sqrt(cov[2, 2]))
    return out_tuple, means, variances, var_errors


def main():
    """test with some representative files"""
    file_nums = []
    if len(sys.argv) > 2:
        file_nums.extend(range(int(sys.argv[1]), int(sys.argv[2])))
    else:
        file_nums.extend(range(1732, 1739))
    print fit_gain(file_nums, True)

if __name__ == '__main__':
    main()
