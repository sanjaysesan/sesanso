import json
import os
import subprocess
from flask import Flask, request, jsonify, render_template
from tools.search_jobs import search

app = Flask(__name__)

def parse_chat_intent(user_prompt):
    """Dynamically extract exact job query keywords and target location from user prompt."""
    prompt_lower = user_prompt.lower()
    
    # Default fallback query and location
    query = "salesforce testing automation"
    location = "chennai"
    
    # Comprehensive list of cities to detect
    cities = ["chennai", "bangalore", "bengaluru", "hyderabad", "mumbai", "pune", "delhi", "ncr", "kolkata", "ahmedabad", "remote"]
    for city in cities:
        if city in prompt_lower:
            location = city.capitalize()
            # Remove city name from prompt to isolate the role keywords
            prompt_lower = prompt_lower.replace(city, "").strip()
            break
            
    # Extract specific job role phrases if introduced by preposition/trigger words
    for prefix in ["jobs for", "job for", "looking for", "search for", "find"]:
        if prefix in prompt_lower:
            parts = prompt_lower.split(prefix)
            if len(parts) > 1 and parts[1].strip():
                extracted = parts[1].replace("in", "").replace("at", "").strip()
                if extracted:
                    query = extracted
            break
    else:
        # If no explicit prefix, check if the prompt itself is a custom role description (excluding basic chat words)
        cleaned_prompt = prompt_lower
        for stop_word in ["please", "show", "me", "can", "you", "jobs", "job", "openings", "role", "roles"]:
            cleaned_prompt = cleaned_prompt.replace(stop_word, "").strip()
        
        if cleaned_prompt:
            query = cleaned_prompt

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