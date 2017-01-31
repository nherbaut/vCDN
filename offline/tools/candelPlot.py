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
    ax1.set_title('Evolution of the cost of the TE service Embedding')
    # ax1.get_xaxis().set_visible(False)
    plt.legend()

    ax1.grid(True)
    plt.savefig("candel.svg")
    #plt.show()


if __name__ == "__main__":
    d = [
(101615.000000,101615.000000,0.000000,0.000000),
(120598.100000,120598.100000,0.062696,0.000000),
(123293.600000,137493.600000,0.024510,0.000000),
(125813.200000,140013.200000,0.026896,0.000000),
(128325.800000,142525.800000,0.023412,0.000000),
(144055.700000,144055.700000,0.018511,0.000000),
(145171.300000,159371.300000,0.009729,0.000000),
(157313.400000,157313.400000,0.024483,0.002698),
(158481.600000,172681.600000,0.011027,0.000000),
(160322.100000,174522.100000,0.019585,0.000000),
(164636.800000,178836.800000,0.038182,0.000000),
(171955.700000,171955.700000,0.024792,0.022817),
(165799.700000,171955.700000,0.000000,0.042356),
(143176.700000,165799.700000,0.000000,0.111946),
(126167.800000,143176.700000,0.000000,0.182257),
(85899.800000,126167.800000,0.000000,0.213973),
(61128.900000,85899.800000,0.000000,0.235168),
(57229.500000,61128.900000,0.000000,0.153273),
(56160.800000,57229.500000,0.000000,0.063776),
(73957.900000,73957.900000,0.075221,0.026465),
(79536.900000,93736.800000,0.129216,0.000000),
(87851.900000,102051.900000,0.174681,0.000000),
(112463.500000,112463.500000,0.196195,0.000000),
(137964.900000,137964.900000,0.184260,0.000000),
(162081.500000,162081.500000,0.129032,0.000000),
(167056.800000,181256.900000,0.069879,0.000000),
(170162.700000,184362.600000,0.030111,0.000000),
(172263.600000,186463.600000,0.022823,0.000000),
(188958.900000,188958.900000,0.024294,0.000000),
(0.000000,188958.900000,0.000000,1.000000),
]


    y, y1, sla_hi, sla_low = list(zip(*d))
    candelPlot(np.arange(0, len(y)), y, y1, sla_hi, sla_low)
