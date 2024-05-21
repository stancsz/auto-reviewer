import os
from git import Repo, GitCommandError
from openai import OpenAI

# Get the OpenAI API key from environment variable
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    print("Error: OpenAI API key not found in environment variables.")
    exit(1)

# Initialize the OpenAI client
def get_code_review(file_content):
    client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You're a code review bot. Focus on user's code comments where there's a TODO or asking for help. Your job is to help people review code. Sound like a human. Your code and writings are short and concise. If there's something that looks wrong, you'll repeat the section of code that's off, then another section for correction. You'll encourage people to do better."
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
    return response.choices[0].message.content

try:
    # Initialize the repo
    repo = Repo(".")
    print("Repository initialized successfully.")
except GitCommandError as e:
    print(f"Error initializing the repository: {e}")
    exit(1)

# Get the list of changed files in the last commit
try:
    changed_files = [item.a_path for item in repo.index.diff("HEAD~1")]
    print(f"Changed files in the last commit: {changed_files}")
except GitCommandError as e:
    print(f"Error getting the list of changed files: {e}")
    exit(1)

# Specify file extensions for code-related files
code_extensions = ['.java', '.py', '.js', '.html', '.css', '.cpp', '.c', '.cs']

# Loop through the changed files and create a README file for each code-related file
for file in changed_files:
    if any(file.endswith(ext) for ext in code_extensions):
        print(f"Processing file: {file}")
        base, ext = os.path.splitext(file)
        ext_without_dot = ext[1:]  # Remove the leading dot from the extension
        readme_filename = f"review_{base.replace('.', '_')}_{ext_without_dot}.md"
        readme_dir = os.path.dirname(readme_filename)

        # Create the directory if it doesn't exist
        if readme_dir and not os.path.exists(readme_dir):
            try:
                os.makedirs(readme_dir, exist_ok=True)
                print(f"Created directory for README file: {readme_dir}")
            except OSError as e:
                print(f"Error creating directory {readme_dir}: {e}")
                continue

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
                print(f"Read content from {file}")
        except IOError as e:
            print(f"Error reading file {file}: {e}")
            continue

        # Get the code review from OpenAI
        try:
            review_content = get_code_review(code_content)
            print(f"Received code review for {file}")
        except Exception as e:
            print(f"Error getting code review for {file}: {e}")
            continue

        # Write the review content to the README file
        try:
            with open(readme_filename, 'w') as readme_file:
                readme_file.write(f"# Documentation for {file}\n\n")
                readme_file.write("## Code Review\n\n")
                readme_file.write(review_content)
                print(f"Created README file: {readme_filename}")
        except IOError as e:
            print(f"Error creating README file for {file}: {e}")
            continue

        try:
            # Stage the new README file
            repo.index.add([readme_filename])
            print(f"Staged README file: {readme_filename}")
        except GitCommandError as e:
            print(f"Error staging README file for {file}: {e}")
            continue

try:
    # Commit the new README files if any were added
    if repo.index.diff("HEAD"):
        repo.index.commit("Add README files for changed code-related files")
        print("Committed README files.")
    else:
        print("No README files to commit.")
except GitCommandError as e:
    print(f"Error committing README files: {e}")
    exit(1)

try:
    # Push the changes
    origin = repo.remote(name='origin')
    origin.push()
    print("Pushed changes to the remote repository.")
except GitCommandError as e:
    print(f"Error pushing changes to the remote repository: {e}")
    exit(1)

print("README files created, committed, and pushed successfully.")
