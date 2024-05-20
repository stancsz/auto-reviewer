import os
import subprocess
from git import Repo

# Get the list of changed files
repo = Repo(".")
changed_files = [item.a_path for item in repo.index.diff("HEAD~1")]

# Specify file extensions for code-related files
code_extensions = ['.java', '.py', '.js', '.html', '.css', '.cpp', '.c', '.cs']

# Loop through the changed files and create a README file for each code-related file
for file in changed_files:
    if any(file.endswith(ext) for ext in code_extensions):
        readme_filename = f"{os.path.splitext(file)[0]}_README.md"
        with open(readme_filename, 'w') as readme_file:
            readme_file.write(f"# Documentation for {file}\n\n")
            readme_file.write("Add your documentation here.")

        # Stage the new README file
        repo.index.add([readme_filename])

# Commit the new README files
repo.index.commit("Add README files for changed code-related files")

# Push the changes
origin = repo.remote(name='origin')
origin.push()


# test