# HR Policy Chatbot

## Description
AI-powered policy assistant that lets employees upload company policy documents and ask questions in plain language to get instant, context-aware answers.

## Project Goal
**Primary Goal:** The system aims to streamline HR policy access by offering a conversational AI assistant that captures employee queries, delivers personalized policy information, and facilitates quick understanding, reducing manual HR inquiries and improving employee satisfaction.

## Overview
HR Policy Chatbot is a conversational system designed to streamline the discovery and understanding of company policies. It enables employees to interact naturally, express their questions, and receive curated answers along with relevant policy references.

## Objective
- Deliver a conversational experience for policy inquiries
- Lead capture for HR follow-ups
- Capture user preferences efficiently

## Tech Stack
- LLMs
- RAG
- Embeddings and vector search
- PDF Parser
- Streamlit
- SQLite

## Use Case
Users interact with a conversational assistant to understand HR policies and get answers efficiently. The system supports:
- Capturing user questions about policies such as leave, benefits, workplace guidelines.
- Recommending personalized policy information based on uploaded documents.

## Need
HR policy understanding is often fragmented and manual, leading to delays and employee confusion. This system addresses these challenges by:
- Automating user interaction and query handling through AI.
- Delivering personalized answers to improve employee experience.
- Bridging the gap between policy documents and quick access in a single flow.
- Increasing efficiency and reducing HR workload.

## Benefits
- **Higher Efficiency:** Easy access to policy information.
- **Automation:** No manual lookup required.
- **Scalable:** Handles multiple employee queries simultaneously.

## Links
- **Video:** [https://youtu.be/cqVcHBNB7WU](https://youtu.be/cqVcHBNB7WU)
- **Demo:** [https://ai-in-hr-domain.streamlit.app/](https://ai-in-hr-domain.streamlit.app/)
- **Docs:** [https://1drv.ms/b/c/ebab0d4d1fda8714/IQA_9zWJMKK_T4FMQlK7IiptAeEFjT4LSDzFPp3nI4dohmY?e=tMnMIF](https://1drv.ms/b/c/ebab0d4d1fda8714/IQA_9zWJMKK_T4FMQlK7IiptAeEFjT4LSDzFPp3nI4dohmY?e=tMnMIF)

## Installation and Setup
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (e.g., GROQ_API_KEY).
4. Run the application: `streamlit run app.py`

## Usage
Upload PDF policy documents, then ask questions in natural language to receive answers based on the content.