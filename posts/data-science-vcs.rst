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

While most of the tools we use will be installed through Python's own package manager, there's a few pieces that need to be downloaded separately:

* A Python Distribution - The base Python Interpreter, at the time of writing I recommend version 3.8, which is well supported.
* Poetry - We'll use Poetry to manage virtual environments as well as make sure others can install the same package versions we're using (via the poetry.lock file)
* Visual Studio Code (Optional) - While any text editor will work, VSCode's extensive Python support (Including a Jupyter extension that runs a server in the editor) as well as git integration make it a one-stop shop for data analysis.
* Git - At the end of the day Jupyter notebooks are still code, and we want to exercise best software practices when writing them, including a robust version control system. Git can be daunting at first, but VSCode's git integration means your commits can be done through the UI instead of command line.

Once everything is installed we're ready to set up the environment.

Setting up our Python environment
==================================

Why Use a Virtual Environment?
```````````````````````````````

Easy Virtual Environments with Poetry
``````````````````````````````````````
In addition to managing dependencies, Poetry makes creating new environments easy with its :code:`poetry init` command. This will ask a series of questions about your project. Ignoring any irrelevant fields, you can also choose to add any package dependencies when creating the environment. It's simple to add dependencies later down though, so I typically skip this step.

.. code:: console

    $ poetry init

    This command will guide you through creating your pyproject.toml config.

    Package name [data_analysis]:  my_awesome_analysis_repository
    Version [0.1.0]:  
    Description []:  
    Author [Ryan Frazier <ryan@fotonixx.com>, n to skip]:  
    License []:  
    Compatible Python versions [^3.9]:  >3.8,<3.9

    Would you like to define your main dependencies interactively? (yes/no) [yes] no
    Would you like to define your development dependencies interactively? (yes/no) [yes] no

Once it's done you will have a "pyproject.toml" in the root directory with the information you entered. By default Poetry will create the environment in a separate directly, but you can access it with :code:`poetry run`. Test that the environment is running by executing :code:`poetry run py --version`, and making sure it matches the version you specified.

Adding Common Dependencies 
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Typically there's some packages that you'll use for every project, so lets add them to the template environment! For me these are numpy, scipy, pandas, and matplotlib. We also need to install the IronPython Kernel so we can register this environment as a Jupyter Kernel later. All of these can be installed using poetry's :code:`add` command.

.. code:: console

    $ poetry add numpy scipy matplotlib pandas ipykernel

If you open the pyproject.toml file now you'll see all those packages are listed in the dependencies section. Additionally, you now have an autogenerated "poetry.lock" file which poetry uses to store the exact package versions of every package and dependency in the environment. 

You'll notice we don't have Jupyter listed as a dependency. I usually only install Jupyter as a global package, and call specific environments as Kernels. If you'd like Jupyter as a package dependency, however, you can add it as well. 

Registering Our Environment as an IPython Kernel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Even though we don't have Jupyter installed in the environment, we still want to be able to have the Jupyter server access and run notebooks using the packages we just installed. For this we'll use the ipykernel package to register a new Kernel to this environment. I won't go into the details of IronPython or the kernels, but they can be thought of as a way to link Jupyter execution to a specific virtual environment. 

.. code:: console

    poetry run python -m ipykernel install --user --name project_x_env --display-name "My Awesome Data Science Environment"

Now you can Launch Jupyter from **any** environment, including the global environment, and still access this environment's packages.

.. figure:: /images/data_science_vcs/kernel_addition.png
    :align: center

    Our newly created Kernel as a selectable option

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
