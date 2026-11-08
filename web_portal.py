import json
import os
import subprocess
from flask import Flask, request, jsonify, render_template
from tools.search_jobs import search

app = Flask(__name__)

def parse_chat_intent(user_prompt):
    """Cleanly parse natural language chat prompts to extract job roles and locations."""
    prompt_lower = user_prompt.lower()
    
    # Default fallback
    query = "salesforce testing"
    location = "chennai"
    
    # 1. Extract location
    cities = ["chennai", "bangalore", "bengaluru", "hyderabad", "mumbai", "pune", "delhi", "ncr", "kolkata", "ahmedabad", "remote"]
    for city in cities:
        if city in prompt_lower:
            location = city.capitalize()
            prompt_lower = prompt_lower.replace(city, "").strip()
            break
            
    # 2. Extract core role by stripping out conversational filler words
    filler_words = [
        "get", "all", "the", "jobs", "job", "opening", "openings", "search", "find", 
        "me", "please", "can", "you", "show", "posted", "just", "now", "recent", 
        "for", "in", "at", "with", "related", "role", "roles"
    ]
    
    words = prompt_lower.split()
    filtered_words = [w for w in words if w not in filler_words]
    
    if filtered_words:
        query = " ".join(filtered_words)
    
    # If the user prompt was too conversational and left query empty, fallback intelligently
    if not query.strip() or len(query.strip()) < 2:
        if "salesforce" in user_prompt:
            query = "salesforce"
        elif "qa" in user_prompt or "testing" in user_prompt:
            query = "qa automation testing"
        elif "python" in user_prompt:
            query = "python developer"
        else:
            query = "software engineer"
            
    return query, location

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/sesans-o/chat", methods=["POST"])
def sesans_o_chat():
    user_prompt = request.json.get("prompt", "").lower().strip()
    if not user_prompt:
        return jsonify({"error": "Please enter a prompt for Sesan's O."}), 400
    
    try:
        # Load user profile / resume context if available
        profile_data = {}
        if os.path.exists("data/profile.json"):
            with open("data/profile.json", encoding="utf-8") as f:
                profile_data = json.load(f)
        
        name = profile_data.get("full_name", "Chandrasesan S.")
        
        # Handle conversational queries intelligently
        if any(greet in user_prompt for greet in ["hi", "hello", "hey", "how are you"]):
            reply = f"Hello {name}! I am **Sesan's O**, your local AI job-hunting agent. I'm ready to help you find and apply for any role in any location. What would you like to search for today?"
        elif "your name" in user_prompt or "who are you" in user_prompt:
            reply = f"My name is **Sesan's O**. I am your dedicated local AI career assistant, built to help you search jobs across any location, tailor your master resume without inventing skills, and track your applications!"
        elif "who am i" in user_prompt or "my name" in user_prompt:
            reply = f"You are **{name}**, an Associate in Quality Engineering and Assurance specializing in Salesforce, Agentforce, Playwright, Veeva CRM, and Tosca!"
        elif any(kw in user_prompt for kw in ["job", "jobs", "opening", "openings", "search", "find", "roles", "developer", "engineer", "qa", "testing", "salesforce"]):
            query, location = parse_chat_intent(user_prompt)
            jobs = search(query, location, 7)
            
            total_found = len(jobs)
            reply_lines = [f"Found **{total_found}** matching jobs for **{query}** in **{location}** scored against your master resume:"]
            if not jobs:
                reply_lines.append(f"\n*No active listings found right now for '{query}' in {location}. Try expanding your search terms or checking another city!*")
            else:
                for i, j in enumerate(jobs, 1):
                    reply_lines.append(
                        f"\n--- \n"
                        f"**#{i} {j['title']}** at **{j['company']}**\n"
                        f"* **Location:** {j['location']} | **Posted:** {j['posted']}\n"
                        f"* [🔗 Open Direct Application Link]({j['url']})"
                    )
            reply = "\n".join(reply_lines)
        elif "tracker" in user_prompt or "applied" in user_prompt:
            proc = subprocess.run(["python", "tools/tracker.py", "followups"], capture_output=True, text=True)
            reply = f"Here is your current application tracker status:\n{proc.stdout}"
        else:
            # Fallback for direct role queries like "software developer in hyderabad"
            query, location = parse_chat_intent(user_prompt)
            jobs = search(query, location, 7)
            total_found = len(jobs)
            
            reply_lines = [f"Found **{total_found}** matching jobs for **{query}** in **{location}** scored against your master resume:"]
            if not jobs:
                reply_lines.append(f"\n*No active listings found right now for '{query}' in {location}.*")
            else:
                for i, j in enumerate(jobs, 1):
                    reply_lines.append(
                        f"\n--- \n"
                        f"**#{i} {j['title']}** at **{j['company']}**\n"
                        f"* **Location:** {j['location']} | **Posted:** {j['posted']}\n"
                        f"* [🔗 Open Direct Application Link]({j['url']})"
                    )
            reply = "\n".join(reply_lines)
            
        return jsonify({
            "agent": "Sesan's O",
            "command": user_prompt,
            "reply": reply
        })
    except Exception as e:
        return jsonify({"agent": "Sesan's O", "reply": f"Error processing request: {str(e)}"})

@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    kw = request.args.get("keywords", "salesforce")
    loc = request.args.get("location", "chennai")
    try:
        days = int(request.args.get("days", 7))
        jobs = search(kw, loc, days)
        return jsonify({"count": len(jobs), "jobs": jobs})
    except Exception as e:
        return jsonify({"error": str(e), "jobs": []}), 500

@app.route("/api/followups", methods=["GET"])
def get_followups():
    proc = subprocess.run(
        ["python", "tools/tracker.py", "followups"],
        capture_output=True, text=True
    )
    return jsonify(json.loads(proc.stdout or '{"count": 0, "applications": []}'))

@app.route("/api/files", methods=["GET"])
def get_master_files():
    resume_text = open("data/resume.md", encoding="utf-8").read() if os.path.exists("data/resume.md") else ""
    profile_text = open("data/profile.json", encoding="utf-8").read() if os.path.exists("data/profile.json") else "{}"
    return jsonify({"resume": resume_text, "profile": profile_text})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)