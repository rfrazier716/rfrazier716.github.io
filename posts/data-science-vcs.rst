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

This data analysis style has caused issues and schedule slips, which drove me to create a Python-centric, version controlled workflow that can be easily adopted and adapted to any analysis.

.. contents::
    :depth: 2
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

* A Python Distribution - The base Python Interpreter, at the time of writing I recommend version 3.8, which is well supported. It's worth noting that if you are on windows, the :code:`pywinpty` package (required by Jupyter) only supports 64-bit Python versions, so make sure to download a 64-bit interpreter.
* Poetry - We'll use Poetry to manage virtual environments as well as make sure others can install the same package versions we're using (via the poetry.lock file)
* Visual Studio Code (Optional) - While any text editor will work, VSCode's extensive Python support (Including a Jupyter extension that runs a server in the editor) as well as git integration make it a one-stop shop for data analysis.
* Git - At the end of the day Jupyter notebooks are still code, and we want to exercise best software practices when writing them, including a robust version control system. Git can be daunting at first, but VSCode's git integration means your commits can be done through the UI instead of command line.

Once everything is installed we're ready to set up the environment.

Setting up our Python Environment
==================================

We want the packages we depend on to be isolated from the rest of the Python installation. Since Python dynamically links libraries at runtime, updating a package down the line (e.g. to install a different library with a newer dependency) might break your old code, or worse, introduce a subtle bug that you don't catch until much further down the line. While we could go to an extreme and containerize all of our code, running it in a Docker Environment or similar, Python instead offers a simpler solution through virtual environments. If virtual environments are a new concept, I recommend reading the `tutorial on python.org`_.

.. _`tutorial on python.org`: https://docs.python.org/3/tutorial/venv.html

Easy Virtual Environments with Poetry
``````````````````````````````````````
Poetry makes creating new environments easy with its :code:`poetry init` command. This will ask a series of questions about your project which the tool will use to generate a `pyproject.toml`_ file. You can also choose to add any package dependencies when creating the environment. It's simple and often faster to add dependencies later, so I typically skip this step.

.. _`pyproject.toml`: https://snarky.ca/what-the-heck-is-pyproject-toml/

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

Once it's done, :code:`pyproject.toml` will be generated in the root directory with the information you entered. By default Poetry will create the environment in a separate directly, but you can access it with :code:`poetry run`. Test that the environment is running by executing :code:`poetry run py --version`, and making sure it matches the version you specified.

Adding Common Dependencies 
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The specific packages you need will vary project-to-project, you'll almost always be using the `Scientific Python Stack <https://www.scipy.org/stackspec.html>`_, so lets add it to our dependencies! We also need to install the `Interactive Python (IPython) <https://ipython.org/ipython-doc/3/interactive/tutorial.html>`_ Kernel so we can register this environment as a Jupyter Kernel later. All of these can be installed using poetry's :code:`add` command.

.. code:: console

    $ poetry add jupyterlab numpy scipy matplotlib pandas ipykernel

If you open :code:`pyproject.toml` you'll see all those packages are now listed in the dependencies section. Additionally, Poetry created a :code:`poetry.lock` file which is used to store the exact versions of every package and dependency in the environment. 

Registering Our Environment as an IPython Kernel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jupyter uses `IPython Kernels`_ running as a separate process to evaluate cells. In order for Jupyter to use our newly created virtual environment, we need to register it with a kernel using the ipykernel package. Run the below command replacing :code:`name` and :code:`display-name` with appropriate values for the project.

.. _`IPython Kernels`: https://ipython.readthedocs.io/en/stable/development/how_ipython_works.html?highlight=kernel#the-ipython-kernel

.. code:: console

    $ poetry run python -m ipykernel install --user --name project_x_env --display-name "My Awesome Data Science Environment"

Now you can Launch Jupyter from **any** environment, including the global environment, and still access this environment's packages.

.. figure:: /images/data_science_vcs/kernel_addition.png
    :align: center

    Our newly created Kernel as a selectable option

Adding Version Control
=======================

Making a New Repository
````````````````````````

To keep things simple we'll use VSCode's git plugins to create, commit to, and push our repository. Start by opening the project folder in VSCode, on the left side of the screen you should see the directory structure with the pyproject and poetry.lock files. Depending on your Poetry settings the virtual environment may also be in this base directory.

.. figure:: /images/data_science_vcs/empty_repository.png
    :align: center

Open the Command Pallette (Ctrl+Shift+P or f1 on Windows) and type "git init". There should be only one option that reads "Git: Initialize Repository". Press Enter and select the current folder to initialize the repository.

Notice that :code:`pyproject.toml` and :code:`poetry.lock` have turned green in the Explorer (Ctrl+Shift+E)! This is because VSCode knows you have a repository in the directory and that those files have not been staged for a commit. If you open the Source Control Panel (Ctrl+Shift+G) you'll see both those files listed as changes with a "U" on the right meaning they're unstaged. Before staging and making our initial commit, however, we want to add a few more files that will help flesh out the repository. These include:

* a :code:`readme.md` file in the base directory
* a :code:`.gitignore` file in the base directory
* a new directory :code:`/notebooks/` with a :code:`readme.md` inside of it.
* a :code:`/data/` directory with an empty :code:`.gitkeep` file  inside of it.

When you've added the files your project directory should look similar to below:

.. figure:: /images/data_science_vcs/adding_readme_and_ignore.png
    :align: center

Choosing what files to ignore
``````````````````````````````

Git uses the .gitignore file to black-list specific files or even entire directories from being captured into version control. This helps keep the repository size small and only commit files that are necessary to reproduce the environment. As a rule of thumb the following should be excluded from your commits:

* Any IDE settings (the :code:`./.vscode/` directory )
* Auto-generated files (:code:`*.pyc`, file backups etc.)
* User specific environment files
* Large files that don't often change (downloaded datasets, third-party libraries)

It might seem alarming that datasets should not be part of version control, after all you have nothing to analyze without data! Further down we'll talk about how to synchronize data with the repository, but for now we'll ignore all files in the /data/ directory except for our whitelisted :code:`.gitkeep` file.

.. code::

    # Ignore data directories
    /data/*
    !/data/.gitkeep

The rest of our :code:`.gitignore` file is built off of GitHub's `python.gitignore`_ with the above additions to ignore our data directory, as well as VSCode settings, and Jupyter backup files. The entire file can be found here. 

.. _`python.gitignore`: https://github.com/github/gitignore/blob/master/Python.gitignore

Creating a Git Hook to Prevent Messy Commits
`````````````````````````````````````````````

While I love Jupyter for exploration and data analysis, one thing that always bothers me is how the code lives in the same file as evaluated evaluated output. When version controlling notebooks this can cause issues for a couple of reasons:

#. If the data you're working on is private but the code is public, the private data could end up in an output and committed, available for anybody to see
#. Git works by logging differences in your file. This includes things like cell number, cell output, and picture metadata, if you version control an evaluated notebook you'll have unstaged changes as soon as you evaluate a cell, even though none of the written code actually changed!

We want a way to scrub our notebooks of all evaluated output before committing, them. To do so we'll use `githooks`_ which are custom scripts that run when you perform a git command. Flipping through the githook documentation, the pre-commit hook is exactly what we need. Unfortunately, installing a git hook is a manual process that requires you to add a file to your :code:`/.git/` directory. 

.. container::
    class: alert alert-warning

    .. raw:: html
    
        <i class="fas fa-exclamation-triangle"></i> Githooks are a great way to keep your repository clean, but you <b>must</b> make sure your file is saved before running the hook, otherwise the script will overwrite any unsaved changes.

.. _`githooks`: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks

In order to make it as easy as possible for anybody to use this template, as well as make writing the githook simple, we'll instead use the `pre-commit`_ python package and write our hook with a YAML file that will live in the root of our version control. The pre-commit config we'll be using comes from `Yuri Zhauniarovich's blog`_ and uses nbconvert to scrub the output in-place. 

.. _`Yuri Zhauniarovich's blog`: https://zhauniarovich.com/post/2020/2020-06-clearing-jupyter-output/

Let's add :code:`pre-commit` and :code:`nbconvert` to our poetry environment. Since it's not needed to actually run the notebooks, and will only be used by people contributing to the codebase we'll install them as developer packages.

.. _`pre-commit`: https://pre-commit.com/

.. code:: shell-session

    $ poetry add pre-commit nbconvert --dev

To define the hook, a new file in the base directory called :code:`.pre-commit-config.yaml` and add the following text:

.. code:: YAML

    repos:
    - repo: local
        hooks:
        - id: jupyter-nb-clear-output
            name: jupyter-nb-clear-output
            files: \.ipynb$
            stages: [commit]
            language: system
            entry: jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace

The last piece is to install the githook so that it's run before every commit. Pre-commit makes this easy for us with it's :code:`install` argument.

.. code:: shell-session

    $ poetry run pre-commit install
    pre-commit installed at .git\hooks\pre-commit

This is a good spot for our first commit! We've fleshed out the repository, filled our :code:`.gitignore` and added most of our template files (even if they are empty). To commit using VSCode we'll again use the Source Control Panel (Ctrl+Shift+G). You can manually stage files by pressing the "+" icon to the right of the files, or you can stage all changes by clicking the "+" to the right of the "Changes" drop-down.

All commits should have a meaningful message so that you can look back and quickly understand what was changed. `Chris Beam's Blog <https://chris.beams.io>`_ has a great `post <https://chris.beams.io/posts/git-commit/>`_ on the importance of a good commit message and how to write one, but for our first commit message we'll keep it simple with "initial commit". 

with the files staged and commit message filled out, press the check-mark at the top of the panel to commit the changes. 

Version Controlling Data
=========================

Next comes adding data to the repository. Copy them over to the :code:`/data/` directory we made earlier. You can have a nested folder structure inside of that directory so organize it into a structure that works for you. Looking at the Explorer panel you'll notice all these files are greyed out and don't show up if you tab over to the Source Control panel. Since :code:`/data/` is ignored every file and folder below is is subsequently ignored as well.

Why don't we store everything in the Git Repository?
`````````````````````````````````````````````````````
To understand why we wouldn't want to store our large data files in a git repository, lets peel back what happens when you clone an existing repository onto your local system. From Atlassian's `Git-LFS tutorial <https://www.atlassian.com/git/tutorials/git-lfs>`_:

.. container::
    class: alert alert-info

    *Git is a distributed version control system, meaning the entire history of the repository is transferred to the client during the cloning process. For projects containing large files, particularly large files that are modified regularly, this initial clone can take a huge amount of time, as every version of every file has to be downloaded by the client.*    

The solution to this problem is to not version control the large files at all, but instead version control small reference files that tell you *where* the data lives so you only check-out the version you want, instead of the entire history. `Git-LFS <https://git-lfs.github.com/>`_ (Large File System) is one implementation of this strategy, but we're going to instead use the `Data Version Control (DVC) <https://dvc.org/>`_ Python package, which is specifically designed with data-analysis in mind. 

Setting up DVC
```````````````

Since DVC is a python package, we can install it with Pip just like our other dependencies. The assumption is anybody using our repository will want access to the data, not just developers, so we won't both with the :code:`--dev` flag either.

.. code:: shell-session

    $ poetry add dvc

Stage the pyproject.toml and poetry.lock files for as a new commit with the message:

.. code::

    added DVC as a dependency

DVC is designed to mimic a git work flow, so many of the commands you'd use for git have DVC parallels. for example. To initialize DVC in our repository and add the data directory we use the :code:`init` and :code:`add` commands respectively.

.. code:: shell-session

    $ poetry run dvc init
    $ poetry run dvc add ./data/
    ~~~
    To track the changes with git, run: 
            git add data.dvc .gitignore

Notice the final output after adding the data directory, DVC is telling us that it's created a new file called :code:`data.dvc` that's tracking changes to our data directory. It's also updated :code:`.gitignore` automatically for us to ignore :code:`/data/` (Our previously committed .gitkeep will not be ignored since it's already tracked). DVC's offering a convenience in case we had forgotten to ignore the directory ourselves, but since we already had, let's revert our :code:`.gitignore` to its previous state. In the Source Control Panel, right click :code:`.gitignore` and select "Discard Changes". This will reset the file to its state in the previous commit.

If you add new data to the directory, you can update :code:`data.dvc` by running :code:`dvc add ./data/` again. Make sure to commit :code:`data.dvc` as soon as you add new data, otherwise committed notebooks might lose sync with the data changes.

Adding a Remote
````````````````

DVC allows you to back-up version-controlled data to remote servers, perfect for enabling computers/users to access the same dataset. From the `documentation <https://dvc.org/doc/command-reference/remote#remote>`_: 

.. container::
    class: alert alert-info

    *The same way as GitHub provides storage hosting for Git repositories, DVC remotes provide a location to store and share data and models. You can pull data assets created by colleagues from DVC remotes without spending time and resources to build or process them locally. Remote storage can also save space on your local environment – DVC can fetch into the cache directory only the data you need for a specific branch/commit.*
    
    *Using DVC with remote storage is optional. DVC commands use the local cache (usually in dir .dvc/cache) as data storage by default. This enables the main DVC usage scenarios out of the box.* 

I recommend setting up a default remote even if you're the only one looking at the dataset. Mine are usually directories on an internal network drive, but DVC has `support for multiple storage types <https://dvc.org/doc/command-reference/remote/add#supported-storage-types>`, so use whichever structure works best for you. The remote can even be a separate directory on you computer, so if you ever need to delete your local code and clone a fresh repository you can painlessly pull your data.

Once the remote is set-up pushing to it is as simple as running :code:`dvc push <remote>`. To pull from your remote you similarly run :code:`dvc pull <remote>`.

Document Everything with a ReadMe 
==================================

A good readme will elevate your repository from "that collection of code that only you know how to use" to "an easily understood project that anybody can contribute to." Think of the readme like a lab report with instruction on how to reproduce the analysis, it should:

* Clearly summarize the goal of the repository
* Explain How to duplicate the code on a user's machine. This includes:

  * Installing required software (Python, Poetry, etc.) 
  * Creating the Virtual Environment and installing necessary packages.
  * Registering the Environment with Jupyter
  * Pulling data from the DVC remote

* Give Clear instructions for how users can contribute to/extend the repository:

  * Installing the additional developer dependencies
  * Making sure the githook is set-up so only clean files are committed

I'm a big fan of `othneildrew's Best ReadMe Template <https://github.com/othneildrew/Best-README-Template>`_ And use it for most of my projects. A reimplemented version can be found on the example repository which covers all of the above requirements.

Remember we also had a second ReadMe in the :code:`/notebooks/` directory. Use that one to describe each notebook in greater detail. You can even include example plots and outputs that the notebooks should generate. GitHub will show a rendered readme in every directory that has one, so you can even group all your notebooks into separate subdirectories, and have a specific readme explaining the purpose of every group!

With data added, committed, and readme's filled in it's time for our next commit! stage all the changed files and give it a meaningful message. E.g. highlight what data was added and where it came from. Be sure to follow the `50-72 rule <https://www.midori-global.com/blog/2018/04/02/git-50-72-rule>`_ so your messages stay meaningful and concise.

This is also a great time to push your commits up to your favorite server. If VCS is completely new to you, I'd recommend `github <https://docs.github.com/en/github/getting-started-with-github>`_ for its sheer popularity and option to make both public and private repositories with a free account.


How to Save Results 
====================

This repository structure does a great job making sure analysis is done in a clear, reproducible matter, but I haven't touched on how to actually save results. In fact, because of our commit-hook, even if your VCS server rendered Jupyter notebooks (and many do) there would be no output and only code! So how to we actually save results in a format that can be looked back on? This will vary from person-to-person, but I like to create a :code:`/results/` directory and use Sphinx to create a static website with a new page for each result. Be sure to populate them with saved images and hard coded values so that the results persist even if you edit the code later on. 

Static site generation with Sphinx can easily be integrated into a CI/CD workflow and Github even offers free hosting of static pages. Look into `gh-pages <https://github.com/c-w/ghp-import>`_ for an easy way to deploy your pages into a github hosted Static site.

