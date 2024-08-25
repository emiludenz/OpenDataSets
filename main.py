import re
import requests
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# Step 1: Read the README.md file
readme_file = "README.md"

with open(readme_file, 'r') as file:
    content = file.read()

# Step 2: Find all links in the README.md file
links = re.findall(r'\[(.*?)\]\((.*?)\)', content)

# Function to check if a link is valid (does not return 404)
def check_link(link):
    url = link[1]
    try:
        response = requests.get(url, timeout=10)
        return link, response.status_code != 404
    except requests.RequestException as e:
        print(f"Error checking link {url}: {e}")
        return link, True

# Step 3: Check all links in parallel using ThreadPoolExecutor
valid_links = []
with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers based on your needs
    futures = {executor.submit(check_link, link): link for link in links}
    for future in as_completed(futures):
        link, is_valid = future.result()
        if is_valid:
            valid_links.append(link)

# Step 4: Update the README.md file to strikethrough broken links and append "Link Broken"
updated_content = content
for link_text, link_url in links:
    if (link_text, link_url) not in valid_links:
        # Strikethrough the link text and append "Link Broken"
        broken_link = f"~~[{link_text}]({link_url})~~ (Link Broken)"
        # Replace the original link with the modified broken link
        updated_content = updated_content.replace(f"[{link_text}]({link_url})", broken_link)

# Step 5: Write the updated content back to the README.md file
with open(readme_file, 'w') as file:
    file.write(updated_content)

# Step 6: Commit and push changes to git
try:
    # Add the file to the git staging area
    subprocess.run(["git", "add", readme_file], check=True)

    # Commit the changes
    commit_message = "Mark broken links in README.md"
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    # Push the changes to the remote repository
    subprocess.run(["git", "push"], check=True)
    print("Changes pushed to git successfully.")
except subprocess.CalledProcessError as e:
    print(f"An error occurred while pushing changes to git: {e}")
