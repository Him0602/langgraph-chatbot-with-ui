# 🤖 LangGraph Gemini Chatbot with Streamlit UI

A simple conversational AI chatbot built using **LangGraph, LangChain, Google Gemini, and Streamlit**.

This project extends my basic LangGraph chatbot by adding a simple web-based UI using Streamlit. The backend handles the chatbot workflow using LangGraph, while Streamlit provides the frontend for interacting with the chatbot.

The project also uses LangGraph's checkpointer and `thread_id` to maintain conversation state.

---

## ✨ Features

💬 Simple web-based chat interface using Streamlit

🧠 Conversation memory using LangGraph persistence

🧵 Thread-based conversation state using `thread_id`

🔄 Message history managed with LangGraph's `add_messages`

🤖 Google Gemini integration through `ChatGoogleGenerativeAI`

🕸️ Simple LangGraph workflow: `START → chat_node → END`

🖥️ Separate backend and frontend

🔐 API key stored securely using environment variables

---

## 🛠️ Tech Stack

**Python 3.11+**

**LangGraph** — workflow and state management

**LangChain Core** — message abstractions

**langchain-google-genai** — Google Gemini integration

**Streamlit** — frontend and chat interface

**python-dotenv** — loading environment variables

---

## 📁 Project Structure

```text
LangGraph/
│
├── langgraph_backend.py
├── streamlit-frontend.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
└── venv/
```

> `venv/` is used for the local virtual environment and should not be pushed to GitHub.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Google Gemini API key

Create a `.env` file in the project folder:

```text
GOOGLE_API_KEY=YOUR_API_KEY
```

The backend loads the API key using `python-dotenv`.

Never commit your `.env` file or API key to GitHub.

### 5. Run the chatbot

Run the Streamlit frontend:

```bash
python -m streamlit run streamlit-frontend.py
```

The chatbot will open in your browser.

---

## 🧠 How the Memory Works

The chatbot stores messages in the LangGraph state:

```python
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```

A checkpointer is then attached when compiling the graph:

```python
checkpointer = InMemorySaver()

chatbot = graph.compile(
    checkpointer=checkpointer
)
```

Each conversation is associated with a `thread_id`:

```python
CONFIG = {
    "configurable": {
        "thread_id": "thread-1"
    }
}
```

When the chatbot is invoked using the same `thread_id`, LangGraph can maintain the previous conversation state.

---

## 🖥️ Streamlit UI

The frontend is built using Streamlit's chat components:

```python
st.chat_message()
st.chat_input()
```

The frontend also uses Streamlit's session state to maintain the messages displayed in the UI:

```python
st.session_state["message_history"]
```

When the user enters a message, the frontend sends it to the LangGraph chatbot:

```python
response = chatbot.invoke(
    {
        "messages": [
            HumanMessage(content=user_input)
        ]
    },
    config=CONFIG
)
```

The response from Gemini is then displayed in the Streamlit interface.

---

## 🕸️ Graph Architecture

The current LangGraph workflow is intentionally simple:

```text
    ┌─────────┐
    │  START  │
    └────┬────┘
         │
         ▼
  ┌─────────────┐
  │  chat_node  │
  │             │
  │ Gemini LLM  │
  └──────┬──────┘
         │
         ▼
    ┌─────────┐
    │   END   │
    └─────────┘
```

Inside `chat_node`, the current message history is passed to Gemini:

```python
def chat_node(state: ChatState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}
```

Because the state uses `add_messages`, new messages are added to the existing conversation state.

---

## 🔄 How the Application Works

The application has two main parts:

```text
             Streamlit UI
                  │
                  ▼
       streamlit-frontend.py
                  │
                  ▼
        langgraph_backend.py
                  │
                  ▼
             LangGraph
                  │
                  ▼
            Gemini LLM
                  │
                  ▼
            AI Response
                  │
                  ▼
             Streamlit UI
```

The user enters a message in the Streamlit UI.

The frontend sends the message to the LangGraph backend.

LangGraph passes the messages to the Gemini model.

The generated response is returned and displayed in the Streamlit UI.

---

## 💬 Running the Chatbot

After starting the application:

```bash
python -m streamlit run streamlit-frontend.py
```

You can interact with the chatbot through the web interface.

Example:

```text
User: My name is Himanshu

AI: Nice to meet you, Himanshu!

User: What is my name?

AI: Your name is Himanshu.
```

The conversation is maintained using the LangGraph state and `thread_id`.

---

## ⚠️ Important: Memory Persistence

This project currently uses `InMemorySaver`, which keeps the state in the running Python process.

That means:

- Same `thread_id` → conversation can be remembered.
- Different `thread_id` → separate conversation.
- Restarting the application → in-memory conversation state is lost.

For production applications, a persistent checkpointer such as SQLite or PostgreSQL can be used.

---

## 🔐 Security

Never upload your Gemini API key to GitHub.

The API key should be stored inside `.env`:

```text
GOOGLE_API_KEY=YOUR_API_KEY
```

Before pushing the project to GitHub, check:

```bash
git status
```

Make sure files such as `.env`, API-key files, and your virtual environment are not being committed.

---

## 📌 Future Improvements

Possible next steps for this project:

- Add multiple conversation threads
- Add a new chat option
- Add streaming responses
- Add persistent SQLite/PostgreSQL memory
- Add LangSmith tracing
- Add tool calling
- Add retrieval-augmented generation (RAG)
- Add conversation export
- Add automated tests
- Deploy the chatbot as a web application

---

## 📚 Learning Goals

This project was built to understand:

- How LangGraph can be connected with a frontend
- How Streamlit can be used to create a chatbot UI
- How LangGraph represents application state
- How nodes work inside a graph
- How `START` and `END` define a workflow
- How LangChain message objects work
- How Gemini can be integrated with LangChain
- How LangGraph checkpointers provide conversation state
- How `thread_id` separates conversations
- How Streamlit `session_state` maintains UI message history

---

## 📄 License

This project is available for learning and personal use.