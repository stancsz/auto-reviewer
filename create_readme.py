import os
from git import Repo, GitCommandError
import openai

# Get the OpenAI API key from environment variable
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    print("Error: OpenAI API key not found in environment variables.")
    exit(1)

# Initialize the OpenAI client
openai.api_key = openai_api_key

def get_code_review(file_content):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You're a code review bot, your job is to help people review code. Sound like a human. Your code and writings are short and concise. If there's something that looks wrong, you'll repeat the section of code that's off, then another section for correction. You'll encourage people to do better."
            },
            {
                "role": "user",
                "content": file_content
            }
        ],
        temperature=1.3,
        max_tokens=4095,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response['choices'][0]['message']['content']

try:
    # Initialize the repo
    repo = Repo(".")
except GitCommandError as e:
    print(f"Error initializing the repository: {e}")
    exit(1)

try:
    # Fetch the latest changes from the remote
    repo.remotes.origin.fetch()
except GitCommandError as e:
    print(f"Error fetching changes from the remote repository: {e}")
    exit(1)

try:
    # Get the list of changed files between the current branch and origin/main
    changed_files = [item.a_path for item in repo.index.diff('origin/main')]
except GitCommandError as e:
    print(f"Error getting the list of changed files: {e}")
    exit(1)

# Specify file extensions for code-related files
code_extensions = ['.java', '.py', '.js', '.html', '.css', '.cpp', '.c', '.cs']

# Loop through the changed files and create a README file for each code-related file
for file in changed_files:
    if any(file.endswith(ext) for ext in code_extensions):
        base, ext = os.path.splitext(file)
        ext_without_dot = ext[1:]  # Remove the leading dot from the extension
        readme_filename = f"review_{base.replace('.', '_')}_{ext_without_dot}.md"
        
        # Delete the existing README file if it exists
        if os.path.exists(readme_filename):
            try:
                os.remove(readme_filename)
                print(f"Deleted existing README file: {readme_filename}")
            except IOError as e:
                print(f"Error deleting README file {readme_filename}: {e}")
                continue

        # Read the content of the changed file
        try:
            with open(file, 'r') as code_file:
                code_content = code_file.read()
        except IOError as e:
            print(f"Error reading file {file}: {e}")
            continue

        # Get the code review from OpenAI
        try:
            review_content = get_code_review(code_content)
        except Exception as e:
            print(f"Error getting code review for {file}: {e}")
            continue

        # Write the review content to the README file
        try:
            with open(readme_filename, 'w') as readme_file:
                readme_file.write(f"# Documentation for {file}\n\n")
                readme_file.write("## Code Review\n\n")
                readme_file.write(review_content)
        except IOError as e:
            print(f"Error creating README file for {file}: {e}")
            continue

        try:
            # Stage the new README file
            repo.index.add([readme_filename])
        except GitCommandError as e:
            print(f"Error staging README file for {file}: {e}")
            continue

try:
    # Commit the new README files if any were added
    if repo.index.diff("HEAD"):
        repo.index.commit("Add README files for changed code-related files")
except GitCommandError as e:
    print(f"Error committing README files: {e}")
    exit(1)

try:
    # Push the changes
    origin = repo.remote(name='origin')
    origin.push()
except GitCommandError as e:
    print(f"Error pushing changes to the remote repository: {e}")
    exit(1)

print("README files created, committed, and pushed successfully.")
