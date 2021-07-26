import os
from pathlib import Path

from nikola.plugin_categories import Task
from nikola import utils

# Have to inherit Task to be a task plugin
class GenerateProjects(Task):
    """
    Creates the Projects Page from the projects.yml file
    """

    name = "generate_project_page"

    def gen_tasks(self):
        yield self.group_task()

        # keywords for the task
        kw = {
            "projects_data": "data/projects.yml",
            "template": self.site.config.get('PROJECTS_TEMPLATE', None),
            "output_folder": Path(self.site.config['OUTPUT_FOLDER']) / "projects",
        }

        # Add some context???
        context = {}
        context['permalink'] = "/projects/"
        # create the task
        print(str(kw["output_folder"] / "index.html"))
        if kw["template"] is not None:
            task = self.site.generic_renderer(
                "en",
                str(kw["output_folder"] / "index.html"),
                kw["template"],
                self.site.config["FILTERS"],
                uptodate_deps=[kw["projects_data"]],
                context=context,
                url_type='full_path'
            )
            task['basename'] = self.name
            yield task # yield the task to doit for building