.. title: Getting Up and Running with Nikola
.. slug: getting-up-and-running-with-nikola
.. date: 2021-03-01 16:43:38 UTC-05:00
.. tags: nikola, rst, github
.. category: Programming
.. link: 
.. description: 
.. type: text
.. status: draft


I have no background in web development or design, which is probably as good of a disclosure as any when writing a post about deploying a website. What I do have, however, is a desire to set up a site to share my various projects/software, or at least document it so I don't forget what I was working on 6 months down the road. It needed to be easy to set up, free to host, and give me full control to customize the site and add features as needed (just because I don't currently know web design doesn't mean I won't try to pick it up down the road).

Enter Nikola! I first heard about this at the end of a Real Python podcast where it was described as a quick start static website generator using Python and restructured text. This sounded like a great way to dip my toe into making a website that was somewhere between using an online suite and hand-writing HTML. I know I could have started a blog on Wordpress or Medium, abstracted away all the details, and potentially have had a prettier blog in less time, but where's the fun in that! the fact that Nikola was based around Python was also attractive. I'm a big advocate for Python, it's become my go-to programming language at work (previously it was Mathematica as well as a lot of LabView but that's a topic for a different day) and anywhere I can use it to round out my programming capabilities I'm happy to give it a try.

At work I maintain a data analysis library for our group, which includes writing and hosting documentation on our internal GitLab, so I was already familiar with .rst files. In fact, Nikola feels like an extension of using Sphinx but with more control over the structure over the final site. As an added bonus, it has built in hooks to deploy to github pages, checking the box for "free to host". 

Some Quick Tips
-------------------------

`The Nikola Handbook`__ was a great resource, and I'm not going to bother rewriting that whole page as my own getting started guide. That being said, there were a couple snags I ran into trying to get the site looking how I wanted and up on GitHub, some of it may have been my own fault for not reading the handbook closely enough, but I included a few of the more subtle ones below for reference.

__ https://getnikola.com/handbook.html

A Virtual Environment Helps, But an Environment Manager is Probably Overkill
  Most of my Python projects start with the same three steps: (1) initialize a new github repository (2) create a project directory, and (3) initialize a new pipenv or Poetry_ environment. This site was no exception, but now that I'm looking at the pyproject.toml and poetry.lock file in the root directory I'm realizing the dependency resolution was overkill. There's a grand total of one package in my pyproject dependencies (well two, I installed tox as a dev dependency... again out of habit), so I'll likely delete those and stick to a plain old virtualenv.

.. _Poetry: https://python-poetry.org

The Nav Bar needs to have absolute paths
  Almost immediately after building the site and opening it in a browser, I wanted to customize the navigation bar links at the top of the page. Nikola's documentation has a section for this, but something that wasn't listed is that any internal links need to be start with a '/' or they'll be handled as relative links to whatever page you're on. This resulted in my links working from the homepage, but if I navigated to a different page the they would break. 
  
  In retrospect this is pretty obvious, but it still tripped me up for a solid 20 minutes more than necessary.

  .. code-block:: python
    
    NAVIGATION_LINKS = {
        DEFAULT_LANG: (
            ('/', 'Home'),
            ('/pages/projects/', "Projects"),
            ((
                ("/archive.html", "All"), # This link will work from any page
                ("archive.html", "All"), # This link will break if you're not on the homepage
                ("/categories/cat_programming/", "Programming"),
                ("/categories/cat_gaming/", "Video Games"),
                ("/categories/cat_misc/", "Misc"),
            ),
            "Blog"),
            ('/pages/about', "About"),
            ("/categories/", "Tags"),
        ),
    }

You Can Hide the "Source" Link That Shows Up on the Top Right of Your Pages
  By default each page and blog post will have a hyperlink to the source in the top right corner. Since the site is hosted from a public repository and anybody who wants to can look at the source, I wanted to disable that feature. Turns out it's also an option in the conf.py called ``SHOW_SOURCELINK``, and needs to be set to False.

  .. code-block:: python

    # Show link to source for the posts?
    SHOW_SOURCELINK = False # Set this to False to disable source links
    # Copy the source files for your pages?
    # Setting it to False implies SHOW_SOURCELINK = False
    COPY_SOURCES = False

You're Allowed to Add Build Directories To Your .gitignore
  This is not Nikola specific but more about deploying pages with Nikola and GitHub pages. My thought process was "well the site will be deployed on github, so I guess I need to include all the build files in version control. This was a mental clash with everything I'd been taught about git, specifically that any autogenerated code should be added to your .gitignore file. Turns out Nikola already handles this with the github deploy commands (again configurable in the conf.py). I haven't dug into exactly what's happening under the hood, but my guess is it's creating a git subtree from the output directory, and pushing that newly created subtree branch to github. This let me use the .gitignore like I was used to, since all the build code exists in its own branch.

  The handbook says that you need to set your deploy branch to 'Master' in for user pages, but it works with any branch name as long as you update the `publishing source`__ accordingly in the repository settings. For my repository I use a branch called 'deploy' which lets me keep my source code in the protected 'main' branch.

  __ https://docs.github.com/en/github/working-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site