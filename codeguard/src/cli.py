import os
import getpass

def main():
    print("\n🛡️  Welcome to CodeGuard — Ethical AI Code Reviewer")
    print("=" * 50)

    while True:
        repo_url = input("\n🔗 Enter your private GitHub repo URL: ").strip()

        if not repo_url:
            print("❌ Repo URL cannot be empty. Please try again.")
            continue

        # FIX: Remove .git extension if the user pastes it
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]

        if not repo_url.startswith("https://github.com/"):
            print("❌ Invalid URL. Must start with https://github.com/")
            continue

        break

    # Prompt for Groq API Key
    groq_key = getpass.getpass("\n🔑 Enter your Groq API Key (input will be hidden): ").strip()
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    else:
        print("❌ Groq API Key is required to run CodeGuard.")
        return

    # Prompt the user for their GitHub Token
    token = getpass.getpass("\n🔑 Enter your GitHub Personal Access Token (input will be hidden): ").strip()
    if token:
        os.environ["GITHUB_TOKEN"] = token
    else:
        print("⚠️  No token provided. CodeGuard may fail to clone private repositories.")

    # Now that environment variables are set, import the agent and reporter
    from .agent import agent
    from .reporter import print_report

    print(f"\n🛡️  CodeGuard starting review for: {repo_url}\n")

    # FIX: Capture the final state returned by the LangGraph agent
    final_state = agent.invoke({
        "repo_url": repo_url,
        "is_oss": False,
        "license": "",
        "files": [],
        "reviews": [],
        "error": ""
    })

    # FIX: Output the final results to the console
    if final_state.get("reviews"):
        print_report(final_state["reviews"])
    else:
        print("\n❌ No reviews generated. Check if the repo is empty or open-source.")

if __name__ == "__main__":
    main()