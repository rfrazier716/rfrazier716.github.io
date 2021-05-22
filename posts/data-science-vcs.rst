.. title: Data Science VCS
.. slug: data-science-vcs
.. date: 2021-05-22 11:46:46 UTC-04:00
.. tags: 
.. category: 
.. link: 
.. description: 
.. type: text

There's a recurring pattern I've encountered at work involving data analysis that goes something like this: 

.. container::
    class: alert alert-secondary

    *A large amount of data has been taken, typically saved across multiple CSV files. The engineer responsible for looking at the data then opens the files directly in Excel, and either plots results in place, or copies specific columns into a new "summary" file and starts processing the data there. When it's time to share results with the rest of the team, The excel files are brought up during a meeting, and once a conclusion is made they're often discarded.*

Time and time again this data analysis style has caused issues and schedule slips, which drove me to create a Python-centric, version controlled workflow to this issue (**USE BETTER WORD CHOICE**)

.. contents::
    :class: alert alert-primary

.. contents:: Quick Links
    :depth: 1
    :class: alert alert-primary ml-0


Why Doesn't This Current Method Work?
=====================================

The main problems with the above method stem from difficulty scaling to larger datasets with more than just one engineer looking at them:

CSV is a poor format for large datasets
    As a plain text file, I understand the preference for CSV when you just want to open the data in and flip through it, but as the datasets grow, the unnecessary bloat of CSV files compared to more memory efficient formats (e.g. HDF5) outweighs any benefits. This is especially true once you start generating multidimensional datasets (I recently had to look over a 4D array which was saved as 500 unique CSV files. Converting everything to an hdf5 file decreased the disk space used by 10x as well and made it significantly easier to slice the data into arbitrary views). The main preference I hear for CSV over other formats is that it can be natively opened in Excel, which leads to the next point.

Excel is too manual for efficient analysis
    This comes back to the scaling problem. If you are only looking at a single, two-dimensional dataset Excel does make it easy to generate nice looking plots. It might even seem scalable from the context of "well every new dataset I just open the file in excel and plot the result. But what happens if you decide those plots should be normalized to a certain value, or all plotted with the same scale? Now you need to go back into each file, add a new column which is your processing, and then plot that processed result. This manual step is error prone and is a perfect candidate for automation.

Editing data files can break them for other users
    This is another huge issue with processing data directly in Excel: the data and the analysis are in one file, This prevents multiple people from independently analyzing data. Regardless of that though, **data files should be treated as read-only**, and not edited or renamed after the fact. We've had cases in the past where somebody opens up a csv file with excel, and even though they didn't intentionally make any changes, when they closed it excel had updated the datetime format for all of the timestamps, which causing analysis scripts to break on seemingly random files. 

The Value of the data is only as good as the team's memory
    A graph in an Excel file by itself carries no meaning, and there's a much higher burden on the engineer who created it to remember what he was doing at the time. Six months down the line if the file is opened will they remember what they were looking for? If the engineer has since left and new data comes in will somebody be able to replicate the analysis and get the same results? If the answer to these is no the validity of the results is very fragile, and you'll likely find yourself repeating measurements in the future.


How Do We Fix it?
``````````````````

Our new analysis flow is going to borrow extensively from the great open source tools that have come about for data science, combined with best practices for software maintenance. In the end we will have a template that can be used as a jumping off point for any data analysis project featuring:

* A Version controlled git repository with hooks in place to only store code
* Jupyter Notebook integration to perform the actual Analysis
* A managed Python environment to keep track of dependencies (Numpy, SciPy, etc.)
* Version controlled data which is stored separately from your code, but tracked in the main repository
* A clean, informative readme enabling other users to download and run the same analysis

This project will assume you have familiarity with Python_ and the `Jupyter Notebook environment`_, as well as a light understanding of Git_.

.. _Python: https://www.python.org/
.. _`Jupyter Notebook environment`: https://jupyter.org/
.. _`Git`: https://git-scm.com/


Getting Required software
==========================


Setting up our Python environment
==================================

Why Use a Virtual Environment?
```````````````````````````````

Top Level Modules
``````````````````

Poetry vs. Conda
``````````````````

Pyproject and lock files
`````````````````````````

Registering The Environment with Jupyter
`````````````````````````````````````````

Adding Version Control
=======================

Making a New Repository
````````````````````````

Choosing what files to ignore
``````````````````````````````

Creating a Git Hook to Prevent Messy Commits
`````````````````````````````````````````````

Version Controlling Data
=========================

Why don't we store everything in the Git Repository?
`````````````````````````````````````````````````````

Setting up DVC
```````````````

Adding a Remote
````````````````

Document Everything with a ReadMe 
==================================


Using Our template
===================

A Git Trunk workflow
`````````````````````

Writing good Commit Messages
`````````````````````````````

How to Save Results 
====================
