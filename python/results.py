import os
import colorsys

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
RESULT_PATH = os.path.abspath(os.path.join(HERE, "..", "results", "2019-04-12"))

COLUMNS = {
    "projects": np.int32,
    "lunch_n": np.int32,
    "lunch_cap": np.int32,
    "work_n": np.int32,
    "work_cap": np.int32,
    "workers": np.int32,
    "hungry": np.int32,
    "full": str,
    "lunchtime": str,
    "i": np.int32,
    "nsec": np.int64,
}

NS_TIME = int(30e9)


def read_csv(label, scaling_factor=1e-6):
    filename = os.path.join(RESULT_PATH, label + ".log")
    df = pd.read_csv(
        filename,
        header=None,
        names=COLUMNS.keys(),
        dtype=COLUMNS,
        skipinitialspace=True,
    )

    df.full = df.full == "true"
    df.lunchtime = df.lunchtime == "true"
    df["failed"] = df.nsec > 30_000_000_000
    df.nsec *= scaling_factor

    return df


def make_colors(n):
    f = 1 / n
    return [colorsys.hsv_to_rgb(i * f, 0.9, 0.76) for i in range(n)]


def box_graph(datasets, labels, colors, x_ticks):
    """
    Datasets is a list of lists of series: the outer list is the number of "lines"
    (i.e., different measure types that will be shown per each tick).
    The inner list has an element for each data point (each x-ticks), and is a series
    of values from which a single candlebar is drawn.

    `colors` is a list of hex/rgb colors, same length as `datasets`

    `x_ticks` is a list of values on the X axis, same length as elements of `datasets`
    """

    def setcolor(bp, color):
        plt.setp(bp["boxes"], color=color)
        plt.setp(bp["whiskers"], color=color)
        plt.setp(bp["caps"], color=color)
        plt.setp(bp["medians"], color=color)

    fig = plt.figure(figsize=(7, 5), dpi=300)
    ax = fig.add_subplot(111)

    assert len(datasets) <= len(colors)
    assert len(datasets) <= len(labels)
    for dataset in datasets:
        if len(dataset) < len(x_ticks):
            dataset.extend([[]] * (len(x_ticks) - len(dataset)))

    group_size = len(datasets)
    step_size = group_size + 1
    x_size = len(x_ticks)

    for idx, (series, label, color) in enumerate(zip(datasets, labels, colors)):
        bp = ax.boxplot(
            series,
            positions=[i * step_size + idx for i in range(x_size)],
            showfliers=False,
        )
        setcolor(bp, color)
        plt.plot([], c=color, label=label)

    plt.legend()
    plt.xticks([(x * step_size) + group_size / 2 - 0.5 for x in range(x_size)], x_ticks)
    plt.xlim(-1, step_size * x_size)

    ax.set_ylabel("Computation time (ms)")
    ax.yaxis.grid(True, linestyle="-", which="major", color="lightgrey", alpha=0.5)

    return fig, ax


def plot_morerooms():
    files = ["morerooms-" + s for s in ("optimizing", "satisfying", "onebyone")]
    headers = ["Optimizing solver", "Satisfying solver", "One-by-one solver"]
    datasets = []
    labels = []
    colors = make_colors(len(files))

    for ifn, header in zip(files, headers):
        data = read_csv(ifn)
        subsel = data[~data.failed & (data.hungry <= 25)]
        subsel = subsel[["hungry", "nsec"]]
        grouping = subsel.groupby("hungry")["nsec"]
        series = [s for _, s in grouping]

        datasets.append(series)
        labels.append(header)

    maxticks = max(len(d) for d in datasets)
    x_ticks = range(5, maxticks + 5)

    fig, ax = box_graph(datasets, labels, colors, x_ticks)
    ax.set_xlabel("Number of workers")

    fig.tight_layout()
    plt.savefig("2.pdf")
    plt.close()


def plot_simple():
    data = read_csv("workercount-simple")
    projects = data.projects.unique()
    colors = make_colors(len(projects))
    labels = [f"{n} projects" for n in projects]
    x_ticks = []
    datasets = []

    for n in projects:
        subsel = data[data.projects == n][["workers", "nsec"]]
        grouping = subsel.groupby("workers")["nsec"]
        ticks, series = zip(*grouping)
        if len(ticks) > len(x_ticks):
            x_ticks = ticks
        datasets.append(series)

    fig, ax = box_graph(datasets, labels, colors, x_ticks)
    ax.set_xlabel("Number of workers")

    fig.tight_layout()
    plt.savefig("1.pdf")
    plt.close()


def plot_onebyone():
    data = read_csv("oneworker-params")
    data = data[~data.failed]
    x_ticks = data.lunch_n.unique()
    project_counts = data.projects.unique()
    colors = make_colors(len(project_counts))
    labels = [f"{n} projects" for n in project_counts]
    datasets = []

    for n in project_counts:
        subsel = data[data.projects == n][["lunch_n", "nsec"]]
        grouping = subsel.groupby("lunch_n")["nsec"]
        series = [s for _, s in grouping]
        datasets.append(series)

    fig, ax = box_graph(datasets, labels, colors, x_ticks)
    ax.set_xlabel("Number of lunch rooms")

    plt.yticks([0, 1000, 2000, 3000, 4000, 5000, 10000, 15000, 20000, 25000, 30000])

    fig.tight_layout()
    plt.savefig("3.pdf")
    plt.close()


def main():
    plot_simple()
    plot_morerooms()
    plot_onebyone()


if __name__ == "__main__":
    main()
