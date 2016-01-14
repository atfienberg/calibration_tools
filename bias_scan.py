from matplotlib import pyplot as plt
import numpy as np
from gain_calibration import fit_gain, sig_from_diag


def sigma_from_cov(params, cov):
    """sample covariance matrix of gain vs voltage parameters
    to get uncertainty in breakdown voltage"""
    rands = np.random.multivariate_normal(params, cov, 10000)
    breakdowns = -1*rands[:, 1]/rands[:, 0]
    return np.std(breakdowns)


def make_summary_plot(run_lists):
    """make summary plot based on run list"""
    biases = []
    gains = []
    pes = []
    currs = []
    gainerrs = []
    quad_terms = []
    quad_errs = []
    for row in sorted(run_lists):
        biases.append(row[0])
        gain_out = fit_gain(row[1])
        out_tuple = gain_out[0]
        gains.append(out_tuple[0])
        gainerrs.append(out_tuple[3])
        smeans = sorted(gain_out[1])
        currs.append(0.5*(smeans[-1] + smeans[-2]))
        pes.append(currs[-1]/gains[-1])
        quad_terms.append(out_tuple[1])
        quad_errs.append(out_tuple[4])

    maxgain = max(gains)
    gains = np.array(gains)/maxgain
    gainerrs = np.array(gainerrs)/maxgain
    # gainerrs = 0.1*gains

    currs = np.array(currs)/max(currs)
    pes = np.array(pes)
    pe_errs = gainerrs/gains*pes
    maxpe = max(pes)
    fig, ax1 = plt.subplots()

    coeffs, V = np.polyfit(biases, gains, 1, w=1.0/gainerrs, cov=True)
    breakdown = -1*coeffs[1]/coeffs[0]

    breakdown_sigma = sigma_from_cov(coeffs, V)

    # calculate sigmas throughout range
    vals, vecs = np.linalg.eig(V)
    U = np.transpose(vecs)
    xs_for_error = np.arange(breakdown - 0.1, max(biases) + 0.1, 0.01)
    gain_sigmas = sig_from_diag(xs_for_error, U, vals)
    error_band_ys = np.array([i*coeffs[0] + coeffs[1] for i in xs_for_error])
    ax1.fill_between(xs_for_error, error_band_ys + gain_sigmas,
                     error_band_ys - gain_sigmas, facecolor='red', alpha=0.5)

    fitline = [i*coeffs[0] + coeffs[1] for i in biases] + [0]
    fitbiases = biases + [breakdown]

    ax1.set_title('bias scan %s' % 'test')
    fitplot = ax1.plot(fitbiases, fitline, 'r-')
    gainplot = ax1.errorbar(
        biases, gains, yerr=gainerrs, fmt='ro', markersize=10)
    currplot = ax1.plot(biases, currs, 'g*', markersize=15)
    ax1.set_ylim(0, 1.105)
    ax1.set_xlim([breakdown - 0.1, max(biases) + 0.1])
    ax1.set_xlabel('bias voltage [V]')
    ax1.set_ylabel('relative gain, charge [a.u.]')

    ticks = [breakdown]
    ticks.extend([bias for bias in biases[::2]])
    tick_labels = ['%.1f $\pm$ %.1f' % (breakdown, breakdown_sigma)]
    tick_labels.extend([str(bias) for bias in biases[::2]])
    ax1.set_xticks(ticks)
    ax1.set_xticklabels(tick_labels)
    ax1.grid()
    ax1.get_xticklabels()[0].set_color('r')

    ax2 = ax1.twinx()
    peplot = ax2.errorbar(biases, pes, yerr=pe_errs, fmt='b^', markersize=10)
    ax2.set_ylabel('pe', color='b')
    ax2.set_ylim(0, maxpe*1.105)
    ax2.set_xlim([breakdown - 0.1, max(biases) + 0.1])
    for tick in ax2.get_yticklabels():
        tick.set_color('b')
    ax1.legend([gainplot[0]]+currplot+[peplot[0]]+fitplot,
               ['gain', 'charge', 'pes', 'gain fit'],
               loc='best', numpoints=1)

    # plt.savefig('pdfs/breakdownPlot%s.pdf' % file_descriptor)
    plt.show()

    quadploterrs = 0.5/np.sqrt(quad_terms)*quad_errs
    plt.errorbar(biases, np.sqrt(quad_terms)*100, yerr=quadploterrs*100, fmt='ko')
    plt.xlim(min(biases) - 0.1, max(biases) + 0.1)
    plt.xlabel('bias [V]')
    plt.ylabel('sqrt(quadratic term) [%]')
    plt.show()
