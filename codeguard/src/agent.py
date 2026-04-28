from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from typing import TypedDict, Annotated
import operator
import os
from .license_checker import is_open_source
from .reporter import print_report
from .config import GROQ_API_KEY, MODEL

# --- State ---
class AgentState(TypedDict):
    repo_url: str
    is_oss: bool
    license: str
    files: list
    reviews: list
    error: str
    messages: Annotated[list, operator.add]

# --- Tools ---
@tool
def check_license_tool(repo_url: str) -> dict:
    """Check if a GitHub repo is open source by detecting its license."""
    is_oss, license_key = is_open_source(repo_url)
    return {"is_oss": is_oss, "license": license_key}

@tool
def review_all_files_tool(repo_url: str) -> dict:
    """Fetch all files, review them, write fixes to disk, then commit with human approval."""
    import os
    import time
    from .git_manager import clone_repo, get_local_files, commit_changes
    from .reviewer import review_file
    from .license_checker import is_open_source

    # safety check
    is_oss, _ = is_open_source(repo_url)
    if is_oss:
        print("\n[agent] Safety block: Refusing to clone open source repository.")
        return {"reviews": []}

    # clone repo
    repo_path = clone_repo(repo_url)
    if not repo_path:
        return {"reviews": []}

    # get files
    files = get_local_files(repo_path)
    MAX_FILES = 15
    files = files[:MAX_FILES]

    all_reviews = []
    files_fixed = []

    print(f"\n[agent] Starting review of {len(files)} file(s)...\n")

    # STEP 1 — review every file and write fixes immediately
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"[agent] ⚠️ Could not read {path}: {e}")
            continue

        rel_path = os.path.relpath(path, repo_path)
        result = review_file(rel_path, content)
        review_text = result["review"]
        fixed_code = result["fixed_code"]

        # store review for report
        all_reviews.append({"file": rel_path, "review": review_text})

        # write fixed code to file if different from original
        if fixed_code and fixed_code.strip() != content.strip():
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(fixed_code)
                print(f"[agent] ✅ Fix written → {rel_path}")
                files_fixed.append(rel_path)
            except Exception as e:
                print(f"[agent] ❌ Failed to write fix to {rel_path}: {e}")
        else:
            print(f"[agent] ℹ️  No changes needed → {rel_path}")

        # avoid groq rate limit
        time.sleep(2.5)

    # STEP 2 — show fix summary
    print(f"\n{'='*50}")
    print(f"[agent] 📝 Fix Summary")
    print(f"{'='*50}")
    if files_fixed:
        print(f"[agent] {len(files_fixed)} file(s) were fixed and written to disk:")
        for f in files_fixed:
            print(f"  ✅ {f}")
    else:
        print("[agent] ℹ️  No files needed fixing.")
    print(f"{'='*50}\n")

    # STEP 3 — now ask human to approve commit and push
    commit_changes(repo_path, repo_url)

    return {"reviews": all_reviews}

# --- LLM with tools bound ---
tools = [check_license_tool, review_all_files_tool]
llm = ChatGroq(model=MODEL, api_key=GROQ_API_KEY)
llm_with_tools = llm.bind_tools(tools)

# --- Nodes ---
def agent_node(state: AgentState) -> AgentState:
    system_prompt = """You are CodeGuard, an Ethical AI Code Reviewer.
Your goal is to review a GitHub repository. Follow these exact steps:
1. Use `check_license_tool` to check if the repository is open source.
2. If the repository is open source, STOP. We do not review open source repositories.
3. If it is NOT open source, use `review_all_files_tool` to fetch, review, fix and commit all files.
4. Once done, summarize that the review is complete.
"""
    from langchain_core.messages import SystemMessage, HumanMessage

    if not state.get("messages"):
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please review this repo: {state['repo_url']}")
        ]
    else:
        messages = [SystemMessage(content=system_prompt)] + state["messages"]

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"

def process_tool_results(state: AgentState) -> AgentState:
    from langchain_core.messages import ToolMessage
    import json

    recent_tool_msgs = []
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage):
            recent_tool_msgs.insert(0, msg)
        else:
            break

    new_reviews = list(state.get("reviews", []))
    is_oss = state.get("is_oss", False)
    license_key = state.get("license", "")
    files = list(state.get("files", []))

    for msg in recent_tool_msgs:
        if hasattr(msg, "name"):
            if msg.name == "check_license_tool":
                try:
                    result = json.loads(msg.content)
                    is_oss = result.get("is_oss", False)
                    license_key = result.get("license", "")
                    if is_oss:
                        print(f"\n❌ Open source repo detected ({license_key} license)")
                        print("CodeGuard does not review open-source repositories.\n")
                except Exception as e:
                    print(f"[process_tool_results] Failed to parse license check: {e}")

            elif msg.name == "review_all_files_tool":
                try:
                    result = json.loads(msg.content)
                    new_reviews.extend(result.get("reviews", []))
                except Exception as e:
                    print(f"[process_tool_results] Failed to parse reviews: {e}")

    return {
        "is_oss": is_oss,
        "license": license_key,
        "files": files,
        "reviews": new_reviews
    }

def check_if_oss(state: AgentState) -> str:
    if state.get("is_oss"):
        return "end"
    return "agent"

# --- Tool Node ---
tool_node = ToolNode(tools)

# --- Build Graph ---
def build_agent():
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("process_results", process_tool_results)

    graph.set_entry_point("agent")

    graph.add_conditional_edges("agent", should_continue, {
        "tools": "tools",
        "end": END
    })

    graph.add_edge("tools", "process_results")

    graph.add_conditional_edges("process_results", check_if_oss, {
        "end": END,
        "agent": "agent"
    })

    return graph.compile()

agent = build_agent()