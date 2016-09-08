"""
Demo of errorbar function with different ways of specifying error bars.

Errors can be specified as a constant value (as shown in `errorbar_demo.py`),
or as demonstrated in this example, they can be specified by an N x 1 or 2 x N,
where N is the number of data points.

N x 1:
    Error varies for each point, but the error values are symmetric (i.e. the
    lower and upper values are equal).

2 x N:
    Error varies for each point, and the lower and upper limits (in that order)
    are different (asymmetric case)

In addition, this example demonstrates how to use log scale with errorbar.
"""
from pylab import *

rcParams['legend.loc'] = 'best'


# error bar values w/ different -/+ errors

def candelPlot(x, y, y1, sla_hi, sla_low):
    fig, ax1 = plt.subplots()

    ax1.set_xlim([0, max(x)])
    ax1.set_ylim([0, max(y1) * 1.1])

    # ax2.set_ylim([0,max(y)+max(sla_hi)])
    sla_hi = np.multiply(np.array(sla_hi), y)
    sla_low = np.multiply(np.array(sla_low), y)

    sla_hi = np.concatenate((sla_hi[1:], [0]))
    sla_low = np.concatenate((sla_low[1:], [0]))

    ax1.plot(x, y, color="black", linewidth=3, marker=".", label="total embedding cost")
    ax1.errorbar(x, y, yerr=[np.zeros(len(y)), sla_hi], fmt='.', color="green", linewidth=3,
                 label="bandwidth demand increase")
    ax1.errorbar(x, y, yerr=[sla_low, np.zeros(len(y))], fmt='.', color="red", linewidth=3,
                 label="bandwidth demand decrease")
    mig_legend = False
    for i in range(0, len(y) - 1):
        if y[i] != y1[i + 1]:
            if not mig_legend:
                ax1.plot([x[i], x[i + 1]], [y[i], y1[i + 1]], ls="--", marker='o', color="gray", markersize=5,
                         label="Cost without recombination")
                mig_legend = True
            else:
                ax1.plot([x[i], x[i + 1]], [y[i], y1[i + 1]], ls="--", marker='o', color="gray", markersize=5)

    ax1.set_xticklabels([])
    ax1.set_xlabel("time")
    ax1.set_ylabel("cost in $")
    ax1.set_title('Evolution of the cost of the vCDN service Embedding')
    # ax1.get_xaxis().set_visible(False)
    plt.legend()

    ax1.grid(True)
    plt.savefig("candel.svg")
    plt.show()



if __name__=="__main__":

    d = [
    (91519.900000, 183039.800000, 0.000000, 0.000000),

    (91519.900000, 91519.900000, 0.000000, 0.000000),

    (106983.000000, 122446.100000, 0.015510, 0.000000),

    (112763.800000, 129230.300000, 0.027405, 0.037808),

    (112763.800000, 112763.800000, 0.000000, 0.000000),

    (135353.500000, 157943.200000, 0.073280, 0.000000),

    (110197.700000, 135353.500000, 0.000000, 0.103332),

    (108362.100000, 110197.700000, 0.000000, 0.027966),

    (108362.100000, 108362.100000, 0.000000, 0.000000),

    (147581.000000, 186799.900000, 0.328322, 0.000000),

    (163353.300000, 179125.600000, 0.026503, 0.000000),

    (108738.700000, 124578.400000, 0.026926, 0.278708),

    (92272.200000, 108738.700000, 0.000000, 0.029017),

    (93542.300000, 110652.100000, 0.065770, 0.037062),

    (109346.900000, 130274.600000, 0.147824, 0.034547),

    (123470.200000, 142732.200000, 0.099907, 0.031465),

    (109216.800000, 128596.600000, 0.095683, 0.167571),

    (120811.300000, 138366.900000, 0.066787, 0.054644),

    (76432.500000, 120811.300000, 0.000000, 0.162258),

    (94223.300000, 112014.100000, 0.049167, 0.000000),

    (110193.800000, 126164.300000, 0.023107, 0.000000),

    (110630.400000, 128857.800000, 0.051375, 0.045804),

    (118892.800000, 143125.700000, 0.145368, 0.022460),

    (129119.100000, 146446.000000, 0.035325, 0.084067),

    (111038.700000, 128318.000000, 0.036569, 0.095545),

    (111038.700000, 111038.700000, 0.000000, 0.000000),

    (127441.400000, 143844.100000, 0.027799, 0.000000),

    (125577.600000, 141040.700000, 0.015510, 0.038395),

    (125577.600000, 125577.600000, 0.000000, 0.000000),

    (0.000000, 125577.600000, 0.000000, 1.000000),
]


    y, y1, sla_hi, sla_low = zip(*d)
    candelPlot(np.arange(0, len(y)), y, y1, sla_hi, sla_low)
