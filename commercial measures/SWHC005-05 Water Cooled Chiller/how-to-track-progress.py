#!/usr/bin/env python
# coding: utf-8

"""Display simulation progress bars, one for each subfolder under analysis root with model input files.

Usage:
    $terminal1> cd C:/Users/user1/source/DEER-Prototypes-EnergyPlus/Analysis/mymeasure
    $terminal1> modelkit rake compose
    $terminal1> modelkit rake
    $terminal1> cd C:/Users/user1/source/DEER-Prototypes-EnergyPlus
    $terminal2> python scripts/how-to-track-progress.py ./Analysis

Example output:
    Hit Ctrl+C to interrupt.
    DMo_Furnace: 100%|████████████████████████████████████████████████████████████████████████████| 320/320 [00:03<00:00, 88.90it/s]
    MFm_Furnace_Ex: 100%|█████████████████████████████████████████████████████████████████████████| 160/160 [00:03<00:00, 45.05it/s] 
    MFm_Furnace_New: 100%|████████████████████████████████████████████████████████████████████████| 160/160 [00:03<00:00, 45.69it/s] 
    SFm_Furnace_1975: 100%|███████████████████████████████████████████████████████████████████████| 180/180 [00:03<00:00, 52.25it/s] 
    SFm_Furnace_1985: 100%|███████████████████████████████████████████████████████████████████████| 140/140 [00:03<00:00, 41.13it/s] 
    SFm_Furnace_New: 100%|████████████████████████████████████████████████████████████████████████| 320/320 [00:03<00:00, 96.73it/s] 

This script runs separate from Modelkit. For best results, the user should
first compose all the models prior to starting simulations.

@Author: Nicholas Fette <nfette@solaris-technical.com>
@Date: 2023-07-05
"""

import pandas
import glob
from pathlib import Path
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from tqdm import tqdm
from time import sleep

# site.pxt is one per climate zone.
# Regular sim folders have 12 files.
threshold_finished = 10
endings=['.csv', '.err', '.htm', '.idf', '.pxt', '.pxv', '.rdd', '.sql']
names=['instance-inputs.csv',
 'instance-out.err',
 'instance-out.rdd',
 'instance-out.sql',
 'instance-parameters.csv',
 'instance-rules.csv',
 'instance-tbl.htm',
 'instance-var.csv',
 'instance.idf',
 'instance.pxv',
 'stderr', 'stdout',
 'site.pxt']

def get_stats_by_folder(root: Path,
                        list_unfinished: bool = True,
                        plot_stats: bool = False):
    """
    Get statistics on number of sim run files, and count unfinished instances.
    """
    df=pandas.DataFrame(
        [(f.relative_to(root).parent.as_posix(), f.name, f.suffix)
            for f in root.glob('**/runs/**/*.*')
            if f.name != 'site.pxt' and f.is_file()],
        columns=['folder','name','suffix'])
    stats=df.groupby('folder').count()
    stats2=df.groupby('suffix').count()

    unfinished = stats[stats['suffix'] < threshold_finished]
    unfinished_list = unfinished.index.to_list()

    if list_unfinished:
        print(unfinished_list)
        #print(df[df.folder.isin(unfinished.index)])

    if plot_stats:
        stats.hist()
        plt.yscale('log')
        plt.show()

    return stats, unfinished_list

def widget_safety():
    """ Utility function for DIY Jupyter notebooks.
    In a jupyter notebook, display two check box widgets.
    These guard against accidental file deletion and must be manually enabled.
    """
    import ipywidgets as widgets
    cbox1=widgets.Checkbox(description='toggle safety 1')
    cbox2=widgets.Checkbox(description='toggle safety 2')
    display(cbox1,cbox2)

def delete_unfinished(unfinished_list: list,
                      cbox1, cbox2):
    """ Utility function for DIY Jupyter notebooks.
    WARNING: This function deletes unfinished simulation files.
    Only works in a jupyter notebook, when two check box widgets are checked.
    """
    for stem in unfinished_list:
        print(stem)
        for name in names:
            f = Path(stem).joinpath(name)
            if cbox1.value and cbox2.value:
                print(f'Delete {f}')
                f.unlink(missing_ok=True)
            else:
                print('Disarmed')
    cbox1.value=False
    cbox2.value=False

def applyTimeFormat(ax):
    """For matplotlib plotting of time series data, formats time labels."""
    for label in ax.get_xticklabels():
        label.set_rotation(40)
        label.set_horizontalalignment('right')
    locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

def plot_time_series(root):
    """
    Plots a time series chart showing cumulative number of composed input files,
    number of started simulations, and finished simulations over time.

    Plots a second bar chart showing incremental number of simulations over time.
    """

    # input files, timestamped at batch start
    id0,label0 = '.pxv','batch start'
    # input files, timestamped at simulation start
    id1,label1 = '.idf','sim start'
    # output files, timestamped at simulation finish
    id2,label2 = '.sql','sim finish'
    
    dft0=pandas.DataFrame([(f.relative_to(root).parent.as_posix(), f.name, f.suffix, datetime.fromtimestamp(f.lstat().st_mtime))
                           for f in root.glob('**/runs/**/*.pxv')],
                       columns=['folder','name','suffix','mtime'])
    dft1=pandas.DataFrame([(f.relative_to(root).parent.as_posix(), f.name, f.suffix, datetime.fromtimestamp(f.lstat().st_mtime))
                           for f in root.glob('**/runs/**/*.idf')],
                       columns=['folder','name','suffix','mtime'])
    dft2=pandas.DataFrame([(f.relative_to(root).parent.as_posix(), f.name, f.suffix, datetime.fromtimestamp(f.lstat().st_mtime))
                           for f in root.glob('**/runs/**/*.sql')],
                       columns=['folder','name','suffix','mtime'])

    dft=pandas.concat([dft0,dft1,dft2])
    tmin,tmax = dft['mtime'].min(), dft['mtime'].max()
    trange = tmax-tmin
    dftb=dft.pivot(index='folder',columns='suffix',values='mtime').reset_index()
    print(dftb.head())
    print(dftb.tail())

    plt.plot(dftb[id0].sort_values(), range(len(dftb)), 'o', label=label0)
    plt.plot(dftb[id1].sort_values(), range(len(dftb)), '-', label=label1)
    plt.plot(dftb[id2].sort_values(), range(len(dftb)), '.', label=label2)

    plt.xlim([tmin + 0.00 * trange, tmax])
    #plt.xlim([tmax - timedelta(minutes=10), tmax])
    applyTimeFormat(plt.gca())

    plt.legend()
    plt.show()

    dftb['.sql'].hist(bins=10)
    applyTimeFormat(plt.gca())
    plt.show()

def progress_bar1(root):
    # count the models in this batch
    n_models = len(list(root.glob('**/runs/**/*.pxv')))
    n_done = 0
    delta_t = 1.0
    try:
        with tqdm(total=n_models) as pbar:
            while pbar.n < n_models:
                sleep(delta_t)
                n_done = len(list(root.glob('**/runs/**/*.sql')))
                lag = n_done - pbar.n
                pbar.update(min(100,lag))
                if lag < 1:
                    delta_t *= 1.414
                elif lag >= 2:
                    delta_t /= 2
    except KeyboardInterrupt:
        return

def progress_bar2(root):
    """
    Display simulation progress bars, one for each subfolder under analysis root.
    Progress bar total is based on initial number of composed input files (*.pxv).
    Current count is based on the number of output files (*.sql).
    Progress does not change while a simulation is running (no partial progress).

    Assumes that files are placed within a "runs" subfolder.
    """
    
    print("Hit Ctrl+C to interrupt.")

    # count the models in this batch
    a_subroot = []
    a_n_models = []
    a_pbar = []
    a_n_done = []
    overall_models = 0
    overall_done = 0
    overall_lag = 0
    # Loop over subfolders and create progress bars.
    for subroot in root.glob('*'):
        relpath = subroot.relative_to(root)
        # Count composed models.
        n_models = len(list(subroot.glob('**/runs/**/*.pxv')))
        if n_models > 0:
            a_subroot.append(subroot)
            a_n_models.append(n_models)
            # Create the progress bar here.
            a_pbar.append(tqdm(total=n_models, desc=relpath.parts[0]))
            a_n_done.append(0)
            overall_models += n_models
    delta_t = 1.0 # seconds
    delta_t_max = 10.0 # seconds

    try:
        while overall_done < overall_models:
            try:
                sleep(delta_t)
                # loop over subfolders and their respective progress bars
                for i, (subroot, n_models, pbar) in enumerate(zip(
                    a_subroot, a_n_models, a_pbar
                )):
                    # Count finished simulations.
                    n_done = len(list(subroot.glob('**/runs/**/instance*.sql')))
                    # Lag = how many simulations finished since last progress bar update
                    lag = n_done - pbar.n
                    # Update progress bar by at most 100 points, to animate progress already accrued
                    pbar.update(min(100,lag))
                    a_n_done[i] = pbar.n
                    overall_lag += lag
                overall_done = sum(a_n_done)
                # Actively adjust the sleep interval based on rate of progress, to reduce disk activity.
                if overall_lag < 1:
                    delta_t = min(delta_t_max, delta_t*1.414)
                elif overall_lag >= 2:
                    delta_t /= 2
            except FileNotFoundError:
                pass
    except KeyboardInterrupt:
        return
    finally:
        for pbar in a_pbar:
            pbar.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="""Display simulation progress bars, one for each subfolder under analysis root.
    Progress bar total is based on initial number of composed input files (*.pxv).
    Current count is based on the number of output files (*.sql).
    Progress does not change while a simulation is running (no partial progress)."""
    )
    # default_root: assume we are in repo/ and we want to track repo/Analysis:
    #default_root = Path("./Analysis")
    # Assuming we are in repo/scripts, and we want to track repo/Analysis:
    #default_root = Path("../Analysis")

    # default_root: assume we are in repo/Analysis and we want to track repo/Analysis:
    default_root = Path("./")

    parser.add_argument("analysis_root", metavar='analysis-root', nargs="?",
                        type=Path, default=default_root,
                        help="Analysis folder path, e.g. C:/Users/user1/source/DEER-Prototypes-EnergyPlus/Analysis")
    parser.add_argument("--list-unfinished", action="store_true")
    parser.add_argument("--plot-stats", action="store_true")
    parser.add_argument("--time-series", action="store_true")

    args=parser.parse_args()
    progress_bar2(args.analysis_root)
    stats, unfinished_list = get_stats_by_folder(args.analysis_root, args.list_unfinished, args.plot_stats)
    if args.time_series:
        plot_time_series(args.analysis_root)
