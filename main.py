import re
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def read_file(file_path):
    """Read the contents of a file."""
    with open(file_path, 'r') as file:
        return file.read()

def find_links(content):
    """Find all links in the content of a Markdown file."""
    return re.findall(r'\[(.*?)\]\((.*?)\)', content)

def check_link(link):
    """Check if a link is valid (does not return 404)."""
    link_text, url = link
    try:
        response = requests.get(url, timeout=10)
        return link, response.status_code != 404
    except requests.RequestException as e:
        print(f"Error checking link {url}: {e}")
        return link, False

def check_links_in_parallel(links, max_workers=10):
    """Check all links in parallel using ThreadPoolExecutor."""
    valid_links = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_link, link): link for link in links}
        for future in as_completed(futures):
            link, is_valid = future.result()
            if is_valid:
                valid_links.append(link)
    return valid_links

def update_content(content, links, valid_links):
    """Update the content to strikethrough broken links and append 'Link Broken'."""
    updated_content = content
    skip_links = []
    for skip_link in updated_content.split('\n'):
        if "(Link Broken)" in skip_link:
            skip_links.append(skip_link)

    print(skip_links)
    for link_text, link_url in links:
        if (link_text, link_url) not in valid_links:
            broken_link = f"~~[{link_text}]({link_url})~~ (Link Broken)"
            shouldAdd = True
            for l in skip_links:
                if l in link_url:
                    shouldAdd = False
                    break
            if shouldAdd:
                updated_content = updated_content.replace(f"[{link_text}]({link_url})", broken_link)


    return updated_content

def write_file(file_path, content):
    """Write the updated content back to the file."""
    with open(file_path, 'w') as file:
        file.write(content)

def git_commit_and_push(file_path, commit_message):
    """Commit and push changes to git."""
    try:
        # Add the file to the git staging area
        subprocess.run(["git", "add", file_path], check=True)

        # Commit the changes
        subprocess.run(["git", "commit", "-m", commit_message], check=True)

        # Push the changes to the remote repository
        subprocess.run(["git", "push"], check=True)
        print("Changes pushed to git successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while pushing changes to git: {e}")

def main():
    readme_file = "README.md"
    commit_message = "Mark broken links in README.md"

    # Read the README.md file
    content = read_file(readme_file)

    # Find all links in the README.md file
    links = find_links(content)

    # Check all links in parallel
    valid_links = check_links_in_parallel(links)

    # Update the README.md file to strikethrough broken links
    updated_content = update_content(content, links, valid_links)

    # Write the updated content back to the README.md file
    write_file(readme_file, updated_content)

    # Commit and push changes to git
    #git_commit_and_push(readme_file, commit_message)

if __name__ == "__main__":
    main()
