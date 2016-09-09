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


if __name__ == "__main__":
    d = [
        (104959.000000, 104959.000000, 0.000000, 0.000000),
        (123617.000000, 123617.000000, 0.048709, 0.000000),
        (124593.300000, 138793.300000, 0.017437, 0.000000),
        (141059.800000, 141059.800000, 0.023209, 0.000000),
        (131394.100000, 158849.700000, 0.035927, 0.000000),
        (147060.300000, 147060.300000, 0.024282, 0.000000),
        (147060.300000, 147060.300000, 0.000000, 0.000000),
        (150242.300000, 164442.300000, 0.030012, 0.000000),
        (150242.300000, 150242.300000, 0.000000, 0.000000),
        (154417.900000, 168617.900000, 0.038235, 0.000000),
        (154417.900000, 154417.900000, 0.000000, 0.000000),
        (171428.800000, 171428.800000, 0.024792, 0.000000),
        (157917.300000, 171428.800000, 0.000000, 0.041138),
        (130026.300000, 157917.300000, 0.000000, 0.098998),
        (116630.500000, 130026.300000, 0.000000, 0.177921),
        (92391.300000, 116630.500000, 0.000000, 0.175839),
        (62150.500000, 92391.300000, 0.000000, 0.301643),
        (60189.500000, 62150.500000, 0.000000, 0.099092),
        (60189.500000, 60189.500000, 0.000000, 0.000000),
        (79750.800000, 79750.800000, 0.125291, 0.000000),
        (79750.800000, 79750.800000, 0.000000, 0.000000),
        (88847.700000, 103047.700000, 0.141067, 0.000000),
        (113837.600000, 113837.600000, 0.140355, 0.000000),
        (122195.900000, 139339.000000, 0.184260, 0.000000),
        (146312.500000, 146312.500000, 0.129032, 0.000000),
        (167468.500000, 167468.500000, 0.104329, 0.000000),
        (185134.400000, 185134.400000, 0.037463, 0.000000),
        (185134.400000, 185134.400000, 0.000000, 0.000000),
        (202924.300000, 202924.300000, 0.037402, 0.000000),
        (0.000000, 202924.300000, 0.000000, 1.000000), ]

    y, y1, sla_hi, sla_low = zip(*d)
    candelPlot(np.arange(0, len(y)), y, y1, sla_hi, sla_low)
