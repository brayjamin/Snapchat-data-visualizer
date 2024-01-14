# Code by Tikolu.net
import json
import os
from datetime import datetime, timezone

illegal_chars = r"\"\/:*?<>|"
username = None  # Initialize username

def cancel():
    print("\n\nPress enter to exit...")
    input()
    exit()

def process_message(message):
    message["Type"] = message.pop("Media Type")
    if message["Type"] != "TEXT" and "Content" in message:
        del message["Content"]
    message["Date"] = int(datetime.timestamp(datetime.strptime(message.pop("Created", message.pop("Date", None)), "%Y-%m-%d %H:%M:%S %Z")))
    return message

# Load chat history from file
try:
    with open("chat_history.json", encoding="utf8") as f:
        sections = json.load(f)
except:
    print("Error opening 'chat_history.json'")
    cancel()

# Create a dictionary to store conversations with messages from both parties
user_conversations = {}

# Extract the username from the first occurrence where IsSender is True
for section in sections:
    for message in sections[section]:
        if "IsSender" in message and message["IsSender"]:
            username = message["From"]
            break

if username is None:
    print("Error: Unable to determine the username.")
    cancel()

print(f"\nUsername: {username}")
print("\nChoose export format:")
print("1 - HTML (Viewable in a web browser)")
print("2 - Plain Text (one message per line)")
print("3 - JSON (split into separate files)")
format = int(input("Enter number [1 - 3]: ") or 1)
if format < 1 or format > 3:
    exit()

# Create the 'chats' directory if it doesn't exist
if not os.path.exists("chats"):
    os.makedirs("chats")
    
print()

# Process each conversation separately
for section in sections:
    # Create a dictionary to store messages for each conversation
    full_conversation = {"messages": [], "main_user": username, "other_party": None}
    
    for message in sections[section]:
        if "Conversation Title" in message and message["Conversation Title"] is None:
            # Direct messages (2-party DM)
            chat = message["From"]
            full_conversation["other_party"] = chat
            full_conversation["messages"].append(process_message(message))
        elif "From" in message:
            # Group conversations or multi-party DMs
            chat = message["Conversation Title"] or message["From"]
            full_conversation["other_party"] = chat
            full_conversation["messages"].append(process_message(message))

    # Store the conversation data in the user_conversations dictionary
    user_conversations[username + "_" + section] = full_conversation

# Process conversations and generate HTML, plain text, or JSON outputs
print("Processing conversations...")
for chat, data in user_conversations.items():
    messages = sorted(data["messages"], key=lambda d: d["Date"])
    username_messages = [message for message in messages if message["From"] == data["main_user"]]
    # Output based on the selected format
    with open(f"chats/{''.join(i for i in chat if i not in illegal_chars)}.{['html', 'txt', 'json'][format-1]}", "w", encoding="utf8") as f:
        if format == 1:  # HTML output
            f.write(f"<html><head><title>{chat}</title><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"><style>")
            f.write("""
                body {font-family:sans-serif}
                .message {padding: 0.5em; margin-bottom: 0.5em; max-width: 80%; border-radius: 5px; clear: both; overflow-wrap: break-word;}
                .message.sender {background-color: #cde; float: right; text-align: right;}
                .message.receiver {background-color: #eef; float: left; text-align: left;}
                .message.timestamp {font-size: 0.8em; color: #888;}
                .message .username {font-weight: bold; margin-right: 5px;}
            """)
            f.write("</style></head><body>")
            f.write(f"<h1>{chat}</h1>\n")
            for message in messages:
                timestamp = datetime.utcfromtimestamp(message["Date"]).replace(tzinfo=timezone.utc)
                date = timestamp.strftime("%A %e %B %Y")
                time = timestamp.strftime("%H:%M:%S")
                sender_class = 'sender' if message['From'] == data["main_user"] else 'receiver'
                f.write(f"<div class=\"message {sender_class}\">")
                f.write(f"<span class=\"username\">{message['From']}:</span> {message.get('Content', '')}<br>")
                f.write(f"<span class=\"timestamp\">{time}</span>")
                f.write("</div>\n")
        elif format == 2:  # Plain Text output
            for message in messages:
                date = datetime.fromtimestamp(message["Date"], datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                sender_info = f"{message['From']}: " if message['From'] == data["main_user"] else f"{data['main_user']}: "
                f.write(f"{date} - {sender_info}{message.get('Content', '') if message['Type'] == 'TEXT' else message['Type']}\n")
        elif format == 3:  # JSON output
            f.write(json.dumps(messages, indent=4)) 

# Generate index.html
with open("chats/index.html", "w", encoding="utf8") as index_file:
    index_file.write("<html><head><title>Chat Index</title></head><body>")
    index_file.write("<h1>Chat Index</h1><ul>")

    for chat in user_conversations:
        index_file.write(f"<li><a href='{chat}.html'>{chat}</a></li>")

    index_file.write("</ul></body></html>")
    
print("Chat export complete")
print(f"\n{len(user_conversations)} chats saved in {['HTML','plain text','JSON'][format-1]} format")
cancel()
