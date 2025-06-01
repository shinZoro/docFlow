from dotenv import load_dotenv
from typing import Annotated, Literal, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import PyPDFLoader
from datetime import datetime, timezone

load_dotenv()

llm = init_chat_model("groq:llama3-70b-8192")


import sqlite3
import json
from datetime import datetime

def save_to_memory(data: dict):
    conn = sqlite3.connect("docflow_memory.db")
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        type TEXT,
        timestamp TEXT,
        intent TEXT,
        extracted_values TEXT,
        thread_id TEXT
    )''')

    cursor.execute('''
    INSERT INTO memory (source, type, timestamp, intent, extracted_values, thread_id)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data["source"],
        data["type"],
        data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        data["intent"],
        json.dumps(data["extracted_values"]),
        data.get("thread_id")
    ))

    conn.commit()
    conn.close()



#class for structured output
class textClassifier(BaseModel):
    text_format: Literal["pdf", "json", "email"] = Field(
        ...,
        description="Classify the format of the message is a pdf or json or email\
            For messages that have a proper json format\
            that it has a proper key and value separated by a : in this case give output json \
            For messages containing the path of a file and ending with .pdf give output pdf\
            for any other text give output email\
            "
    )



#Graph State
class State(TypedDict):
    messages : Annotated[list, add_messages]
    raw_text : Optional[str]
    extracted_data : Optional[str]



# Prompts

structured_llm_router = llm.with_structured_output(textClassifier)

#Router prompt
system = "You are an expert at classify and route a input message into pdf path or json path or email path\
Pdf path should be used when the user shares a pdf path in the question or it mentions a pdf that they want to process or the path given consist of .pdf at end\
Json path be used when the input given is in proper json format containing key and values\
email path should be used for every other case, any input that cannot be considered as a pdf path or does not have a json structure should be considered as email\
"

route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human"), "{last_msg}"
    ]
)

route_chain = route_prompt | structured_llm_router

#Pdf Agent prompt

pdf_prompt = PromptTemplate.from_template(
    """You are a document processing agent. Your input {input} is a PDF document (converted to plain text).

Your job:
1. Determine the intent of the document (e.g., Invoice, Complaint, Regulation, RFQ).
2. Identify and extract structured values like: sender, recipient, total amount, due date, subject, etc.
3. Return your answer **strictly** in the following JSON format — no extra text, no markdown, no explanation:


{{
  "source": "<name of PDF file>",
  "type": "PDF",
  "timestamp": "<current ISO timestamp>",
  "intent": "<detected intent>",
  "extracted_values": {{
    "sender": "...",
    "recipient": "...",
    "subject": "...",
    "total_amount": "...",
    "due_date": "...",
    "additional_info": "..."
  }},
  "thread_id": null
}}

Only return valid JSON. If any field is unavailable, omit it or set it to null.
"""
)

pdf_flow = pdf_prompt | llm | JsonOutputParser()


#json Agent Prompt

json_prompt = PromptTemplate.from_template(
    """You are a structured data processor. Your input {input} is a JSON object.

Your job:
1. Determine the intent of the JSON data (e.g., Invoice, Complaint, RFQ, Regulation).
2. Validate and extract key values into a target schema.
3. Format your output strictly in the following structure:

{{
  "source": "<source name or file ID from JSON if present>",
  "type": "JSON",
  "timestamp": "<current ISO timestamp>",
  "intent": "<inferred intent>",
  "extracted_values": {{
    "sender": "...",
    "recipient": "...",
    "total_amount": "...",
    "issue_date": "...",
    "due_date": "...",
    "items": [...],
    "notes": "..."
  }},
  "thread_id": null
}}

Return your answer **strictly** in the following JSON format — no extra text, no markdown, no explanation:


If any value is missing or malformed, flag it in `notes` or set it to null.
Return only valid JSON in this format.
"""
)

json_flow = json_prompt | llm | JsonOutputParser()

#email Agent prompt

email_prompt = PromptTemplate.from_template(
    """You are an AI assistant that extracts structured information from emails.

Given an email text input, perform the following:
1. Identify the intent of the email (e.g., Invoice, RFQ, Complaint).
2. Extract values into this schema:
{{
  "source": "<sender's email address>",
  "type": "Email",
  "timestamp": "<current ISO timestamp>",
  "intent": "<inferred intent>",
  "extracted_values": {{
    "sender": "...",
    "recipient": "...",
    "total_amount": "...",
    "issue_date": "...",
    "due_date": "...",
    "items": ["..."],
    "notes": "..."
  }},
  "thread_id": null
}}

❗Return only valid JSON that matches the format above. Do not include any explanation or markdown formatting.
If you are unsure about a value, set it to null or add clarification in the `notes` field.

Input email:
{input}
"""
)


email_flow = email_prompt | llm | JsonOutputParser()

#Nodes

def Classifier(state: State):
    last_msg = state["messages"][-1].content

    format = route_chain.invoke(last_msg)

    if format.text_format == "pdf":
        return "pdf"
    elif format.text_format == "json":
        return "json"
    elif format.text_format == "email":
        return "email"
    

def pdfFlow(state: State):
    last_msg = state["messages"][-1].content
    loader = PyPDFLoader(last_msg)
    raw_text = loader.load()
    extracted_data = pdf_flow.invoke({"input" : raw_text})
    save_to_memory(extracted_data)

    return{"extracted_data": extracted_data , "messages": "Data from Pdf extracted and Saved Sucessfully"}

def jsonFLow(state: State):
    last_msg = state["messages"][-1].content
    extracted_data = json_flow.invoke({"input" : last_msg})
    save_to_memory(extracted_data)

    return{"extracted_data": extracted_data, "messages": "Data from JSON extracted and Saved Sucessfully"}

def emailFlow(state: State):
    last_msg = state["messages"][-1].content
    extracted_data = email_flow.invoke({"input" : last_msg})

    print(extracted_data)
    save_to_memory(extracted_data)

    return{"extracted_data" : extracted_data, "messages": "Data from Email extracted and Saved Sucessfully"}


graph_builder = StateGraph(State)

graph_builder.add_node("Classifier", Classifier)
graph_builder.add_node("pdfFlow", pdfFlow)
graph_builder.add_node("jsonFlow", jsonFLow)
graph_builder.add_node("emailFlow", emailFlow)

graph_builder.add_conditional_edges(START, Classifier,
                                    {
                                        "pdf" : "pdfFlow",
                                        "json" : "jsonFlow",
                                        "email" : "emailFlow"
                                    })

graph_builder.add_edge("pdfFlow", END)
graph_builder.add_edge("jsonFlow", END)
graph_builder.add_edge("emailFlow", END)



graph = graph_builder.compile()

def chatbot():
    state = {"messages": [] , "raw_text": None , "extracted_data" : None}

    while True:
        user_input = input("You: ")
        if user_input == "exit":
            print("Thanks for today")
            break

        state["messages"] = state.get("messages", []) + [{"role" : "user" , "content" : user_input}]

        state = graph.invoke(state)

        if state.get("messages") and len(state["messages"]) > 0:
            last_msg = state["messages"][-1].content

            print(f"Assistant: {last_msg}")

if __name__=="__main__":
    chatbot()