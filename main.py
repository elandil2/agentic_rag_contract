"""
Main RAG Contract Analysis Application
"""

import streamlit as st
from typing import List, Dict, Any, Annotated, TypedDict, Sequence, Literal
import os
import tempfile
from datetime import datetime
import json
import logging

# LangChain imports
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, ToolMessage, SystemMessage
from langchain_huggingface import HuggingFaceEmbeddings

# LangGraph imports - Updated for new API
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# Import configuration
from config import *

# Setup logging
logger = logging.getLogger(__name__)

# Define the state for our graph
class AgentState(TypedDict):
    """State for the multi-agent system"""
    messages: Sequence[BaseMessage]
    next: str

# Initialize session state
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'supervisor' not in st.session_state:
    st.session_state.supervisor = None

class ContractRAGSystem:
    """Main RAG system for contract analysis"""

    def __init__(self):
        """Initialize the RAG system"""
        try:
            # Validate configuration
            validate_config()

            # Initialize LLM with updated configuration
            self.llm = ChatGroq(
                api_key=GROQ_API_KEY,
                model=GROQ_MODEL,
                temperature=GROQ_TEMPERATURE,
                max_tokens=GROQ_MAX_TOKENS,
                streaming=True  # Enable streaming
            )

            # Initialize proper HuggingFace embeddings
            logger.info(f"Loading embeddings model: {EMBEDDING_MODEL}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={'device': EMBEDDING_DEVICE},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("Embeddings loaded successfully")

            self.vector_store = None
            self.retriever = None

        except Exception as e:
            logger.error(f"Error initializing RAG system: {str(e)}")
            raise
        
    def process_documents(self, uploaded_files) -> bool:
        """Process uploaded contract documents"""
        try:
            all_documents = []
            
            for uploaded_file in uploaded_files:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    tmp_file_path = tmp_file.name
                
                # Load document based on type
                if uploaded_file.name.endswith('.pdf'):
                    loader = PyPDFLoader(tmp_file_path)
                else:
                    loader = TextLoader(tmp_file_path)
                
                documents = loader.load()
                
                # Add metadata
                for doc in documents:
                    doc.metadata['source'] = uploaded_file.name
                    doc.metadata['upload_time'] = datetime.now().isoformat()
                
                all_documents.extend(documents)
                
                # Clean up temp file
                os.unlink(tmp_file_path)
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            splits = text_splitter.split_documents(all_documents)
            logger.info(f"Created {len(splits)} document chunks")

            # Create vector store with proper persistence
            self.vector_store = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                persist_directory=CHROMA_PERSIST_DIR,
                collection_name="contracts"
            )
            logger.info("Vector store created successfully")

            # Create retriever with configurable k
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": TOP_K_RESULTS}
            )

            return True
            
        except Exception as e:
            st.error(f"Error processing documents: {str(e)}")
            return False
    
    def create_tools(self):
        """Create tools for the agents"""
        
        @tool
        def retrieve_contract_info(
            query: Annotated[str, "The query to search for in the contracts"]
        ) -> str:
            """Search and retrieve relevant information from contract documents"""
            if not self.retriever:
                return "No contracts loaded. Please upload contract documents first."

            try:
                # Retrieve relevant documents
                relevant_docs = self.retriever.get_relevant_documents(query)

                if not relevant_docs:
                    return "No relevant information found in the contracts."

                # Format the retrieved information - more concise format
                result = ""
                for i, doc in enumerate(relevant_docs, 1):
                    source = doc.metadata.get('source', 'Unknown')
                    content = doc.page_content.strip()
                    # Only include the content, no extra formatting
                    result += f"{content}\n\n"

                return result.strip()

            except Exception as e:
                return f"Error retrieving information: {str(e)}"
        
        @tool
        def analyze_contract_terms(
            contract_text: Annotated[str, "The contract text to analyze"],
            analysis_type: Annotated[str, "Type of analysis: 'risks', 'obligations', 'dates', 'general'"]
        ) -> str:
            """Analyze contract terms and provide insights"""
            try:
                analysis_prompts = {
                    "risks": "Identify potential risks and liabilities in this contract text:",
                    "obligations": "List all obligations and responsibilities of each party:",
                    "dates": "Extract all important dates and deadlines:",
                    "general": "Provide a general analysis of key terms and conditions:"
                }
                
                prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])
                
                analysis = f"{prompt}\n\n{contract_text}\n\nAnalysis:\n"
                
                # This is a simplified analysis - in production, you'd use the LLM
                if "termination" in contract_text.lower():
                    analysis += "- Termination clause found\n"
                if "payment" in contract_text.lower():
                    analysis += "- Payment terms identified\n"
                if "confidential" in contract_text.lower():
                    analysis += "- Confidentiality provisions present\n"
                
                return analysis
                
            except Exception as e:
                return f"Error analyzing contract: {str(e)}"
        
        @tool
        def summarize_contract(
            contract_text: Annotated[str, "The contract text to summarize"]
        ) -> str:
            """Generate a concise summary of the contract"""
            try:
                summary_prompt = f"""
                {SUMMARIZER_PROMPT}

                Contract Text:
                {contract_text}

                Please provide a comprehensive yet concise summary of this contract.
                """

                summary = self.llm.invoke([HumanMessage(content=summary_prompt)]).content

                return summary

            except Exception as e:
                return f"Error summarizing contract: {str(e)}"

        return retrieve_contract_info, analyze_contract_terms, summarize_contract
    
    def create_supervisor(self):
        """Create the supervisor multi-agent system using new LangGraph API"""

        retrieve_tool, analyze_tool, summarize_tool = self.create_tools()

        # Create tool nodes for each agent
        retriever_tools = ToolNode([retrieve_tool])
        analyst_tools = ToolNode([analyze_tool])
        summarizer_tools = ToolNode([summarize_tool])

        # Create workflow with AgentState
        workflow = StateGraph(AgentState)

        def supervisor_node(state: AgentState) -> AgentState:
            """Supervisor decides which agent to call next"""
            messages = state["messages"]
            last_message = messages[-1].content if messages else ""

            # Create routing prompt
            routing_prompt = f"""
{SUPERVISOR_PROMPT}

User query: {last_message}

Based on the query, decide which agent should handle this:
- "retriever" - for finding information in contracts
- "analyst" - for analyzing contract terms
- "summarizer" - for summarizing contracts
- "end" - if the query has been fully answered

Respond with ONLY the agent name (retriever/analyst/summarizer/end).
"""

            response = self.llm.invoke([SystemMessage(content=routing_prompt)])
            next_agent = response.content.strip().lower()

            # Validate next agent
            if next_agent not in ["retriever", "analyst", "summarizer", "end"]:
                next_agent = "retriever"  # Default to retriever

            logger.info(f"Supervisor routing to: {next_agent}")
            return {"messages": messages, "next": next_agent}

        def retriever_node(state: AgentState) -> AgentState:
            """Retriever agent retrieves relevant contract information"""
            messages = state["messages"]
            last_message = messages[-1].content if messages else ""

            # Create retrieval prompt
            prompt = f"{RETRIEVER_PROMPT}\n\nQuery: {last_message}"

            # Use the retrieve tool
            tool_result = retrieve_tool.invoke(last_message)

            response = AIMessage(content=f"Retrieved Information:\n{tool_result}")
            return {"messages": messages + [response], "next": "analyst"}

        def analyst_node(state: AgentState) -> AgentState:
            """Analyst agent analyzes the retrieved information"""
            messages = state["messages"]

            # Get the original user question
            user_question = ""
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    user_question = msg.content
                    break

            # Get the last retrieval result
            context = ""
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and "Retrieved Information" in msg.content:
                    context = msg.content
                    break

            # Create analysis prompt with user's question
            prompt = f"""{ANALYST_PROMPT}

User's Question: {user_question}

Retrieved Contract Information:
{context}

Answer the user's question directly and concisely based on the retrieved information above."""

            response = self.llm.invoke([SystemMessage(content=prompt)])
            return {"messages": messages + [response], "next": "end"}

        def summarizer_node(state: AgentState) -> AgentState:
            """Summarizer agent creates summaries"""
            messages = state["messages"]
            last_message = messages[-1].content if messages else ""

            # Use the summarize tool
            tool_result = summarize_tool.invoke(last_message)

            response = AIMessage(content=tool_result)
            return {"messages": messages + [response], "next": "end"}

        # Add nodes to workflow
        workflow.add_node("supervisor", supervisor_node)
        workflow.add_node("retriever", retriever_node)
        workflow.add_node("analyst", analyst_node)
        workflow.add_node("summarizer", summarizer_node)

        # Define routing logic
        def route_supervisor(state: AgentState) -> Literal["retriever", "analyst", "summarizer", "__end__"]:
            """Route based on supervisor's decision"""
            next_step = state.get("next", "end")
            if next_step == "end":
                return "__end__"
            return next_step

        # Add conditional edges
        workflow.add_edge(START, "supervisor")
        workflow.add_conditional_edges(
            "supervisor",
            route_supervisor,
            {
                "retriever": "retriever",
                "analyst": "analyst",
                "summarizer": "summarizer",
                "__end__": END
            }
        )
        workflow.add_edge("retriever", "analyst")
        workflow.add_edge("analyst", END)
        workflow.add_edge("summarizer", END)

        # Compile with memory
        memory = MemorySaver()
        app = workflow.compile(checkpointer=memory)

        logger.info("Supervisor workflow compiled successfully")
        return app

# Streamlit UI
def main():
    st.set_page_config(
        page_title="Contract Analysis RAG System",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Contract Analysis RAG System")
    st.markdown("Upload contracts and ask questions about them")
    
    # Initialize system
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = ContractRAGSystem()
    
    # Sidebar for document upload
    with st.sidebar:
        st.header("📁 Document Management")
        
        uploaded_files = st.file_uploader(
            "Upload Contract Documents",
            type=['pdf', 'txt'],
            accept_multiple_files=True,
            help="Upload 3-10 contract documents"
        )
        
        if uploaded_files:
            if st.button("Process Documents"):
                with st.spinner("Processing documents..."):
                    if st.session_state.rag_system.process_documents(uploaded_files):
                        st.success(f"✅ Processed {len(uploaded_files)} documents")
                        st.session_state.supervisor = st.session_state.rag_system.create_supervisor()
                    else:
                        st.error("Failed to process documents")
        
        # System prompt configuration
        st.header("⚙️ System Configuration")
        
        if st.checkbox("Show/Edit System Prompts"):
            retriever_prompt = st.text_area(
                "Retriever Prompt",
                value=RETRIEVER_PROMPT,
                height=150
            )
            
            analyst_prompt = st.text_area(
                "Analyst Prompt", 
                value=ANALYST_PROMPT,
                height=150
            )
            
            if st.button("Update Prompts"):
                # Update prompts in config
                st.success("Prompts updated!")
        
        # Download conversation
        if st.session_state.chat_history:
            if st.button("📥 Download Conversation"):
                conversation_json = json.dumps(
                    st.session_state.chat_history,
                    indent=2,
                    default=str
                )
                st.download_button(
                    label="Download JSON",
                    data=conversation_json,
                    file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat Interface")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about your contracts..."):
            if not st.session_state.supervisor:
                st.warning("Please upload and process documents first!")
            else:
                # Add user message
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": prompt
                })
                
                with st.chat_message("user"):
                    st.write(prompt)
                
                # Get response with streaming
                with st.chat_message("assistant"):
                    try:
                        # Create a placeholder for streaming
                        response_placeholder = st.empty()
                        full_response = ""

                        # Invoke supervisor with streaming
                        config = {"configurable": {"thread_id": "streamlit_session"}}

                        with st.spinner("Analyzing contracts..."):
                            result = st.session_state.supervisor.invoke(
                                {"messages": [HumanMessage(content=prompt)], "next": ""},
                                config=config
                            )

                            # Extract the final response
                            if "messages" in result and len(result["messages"]) > 0:
                                ai_response = result["messages"][-1].content
                                full_response = ai_response
                            else:
                                full_response = "I apologize, but I couldn't generate a response. Please try again."

                        # Display the response
                        response_placeholder.write(full_response)

                        # Add to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": full_response
                        })

                    except Exception as e:
                        logger.error(f"Error processing query: {str(e)}", exc_info=True)
                        st.error(f"Error: {str(e)}\n\nPlease check your configuration and try again.")
    
    with col2:
        st.header("📊 Analysis Options")
        
        # Quick action buttons
        st.subheader("Quick Analysis")

        if st.button("🔍 Find Key Terms"):
            if not st.session_state.supervisor:
                st.warning("Please upload and process documents first!")
            else:
                with st.spinner("Finding key terms..."):
                    try:
                        config = {"configurable": {"thread_id": "quick_analysis"}}
                        response = st.session_state.supervisor.invoke({
                            "messages": [HumanMessage(content="Identify and list all key terms, definitions, and important clauses from the uploaded contracts.")],
                            "next": ""
                        }, config=config)
                        ai_response = response["messages"][-1].content if response.get("messages") else "No response"
                        st.success("✅ Key Terms Identified!")
                        st.write(ai_response)
                    except Exception as e:
                        logger.error(f"Error in key terms analysis: {str(e)}")
                        st.error(f"Error: {str(e)}")

        if st.button("⚠️ Identify Risks"):
            if not st.session_state.supervisor:
                st.warning("Please upload and process documents first!")
            else:
                with st.spinner("Analyzing risks..."):
                    try:
                        config = {"configurable": {"thread_id": "risk_analysis"}}
                        response = st.session_state.supervisor.invoke({
                            "messages": [HumanMessage(content="Analyze the uploaded contracts and identify all potential risks, liabilities, and concerning clauses.")],
                            "next": ""
                        }, config=config)
                        ai_response = response["messages"][-1].content if response.get("messages") else "No response"
                        st.success("✅ Risks Identified!")
                        st.write(ai_response)
                    except Exception as e:
                        logger.error(f"Error in risk analysis: {str(e)}")
                        st.error(f"Error: {str(e)}")

        if st.button("📅 Extract Dates"):
            if not st.session_state.supervisor:
                st.warning("Please upload and process documents first!")
            else:
                with st.spinner("Extracting dates..."):
                    try:
                        config = {"configurable": {"thread_id": "date_extraction"}}
                        response = st.session_state.supervisor.invoke({
                            "messages": [HumanMessage(content="Extract and list all important dates, deadlines, and time-related clauses from the uploaded contracts.")],
                            "next": ""
                        }, config=config)
                        ai_response = response["messages"][-1].content if response.get("messages") else "No response"
                        st.success("✅ Dates Extracted!")
                        st.write(ai_response)
                    except Exception as e:
                        logger.error(f"Error in date extraction: {str(e)}")
                        st.error(f"Error: {str(e)}")

        if st.button("💰 Payment Terms"):
            if not st.session_state.supervisor:
                st.warning("Please upload and process documents first!")
            else:
                with st.spinner("Analyzing payment terms..."):
                    try:
                        config = {"configurable": {"thread_id": "payment_analysis"}}
                        response = st.session_state.supervisor.invoke({
                            "messages": [HumanMessage(content="Analyze and summarize all payment terms, amounts, conditions, and financial obligations from the uploaded contracts.")],
                            "next": ""
                        }, config=config)
                        ai_response = response["messages"][-1].content if response.get("messages") else "No response"
                        st.success("✅ Payment Terms Analyzed!")
                        st.write(ai_response)
                    except Exception as e:
                        logger.error(f"Error in payment analysis: {str(e)}")
                        st.error(f"Error: {str(e)}")
        
        # Summarization
        st.subheader("📝 Contract Summarization")
        if st.button("📋 Summarize All Contracts"):
            if not st.session_state.supervisor:
                st.warning("Please upload and process documents first!")
            else:
                with st.spinner("Generating contract summaries..."):
                    try:
                        # Get all documents from vector store
                        all_docs = st.session_state.rag_system.vector_store._collection.get(include=['documents', 'metadatas'])
                        if all_docs['documents']:
                            # Combine representative document chunks (limit to avoid context overflow)
                            sample_text = "\n\n".join(all_docs['documents'][:20])  # Use first 20 chunks

                            # Create summarization request
                            summary_request = f"Please provide a comprehensive summary of all the uploaded contracts based on this sample: {sample_text[:8000]}"

                            config = {"configurable": {"thread_id": "summary_all"}}
                            response = st.session_state.supervisor.invoke({
                                "messages": [HumanMessage(content=summary_request)],
                                "next": ""
                            }, config=config)

                            ai_response = response["messages"][-1].content if response.get("messages") else "No response"

                            st.success("✅ Contract Summary Generated!")
                            st.write(ai_response)

                            # Add to chat history
                            st.session_state.chat_history.append({
                                "role": "user",
                                "content": "Generate contract summary"
                            })
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": ai_response
                            })
                        else:
                            st.warning("No documents found to summarize.")
                    except Exception as e:
                        logger.error(f"Error generating summary: {str(e)}")
                        st.error(f"Error generating summary: {str(e)}")

        # Statistics
        if st.session_state.rag_system and st.session_state.rag_system.vector_store:
            st.subheader("📈 Statistics")
            st.metric("Documents Loaded", len(uploaded_files) if uploaded_files else 0)
            try:
                st.metric("Total Chunks", st.session_state.rag_system.vector_store._collection.count())
            except Exception as e:
                logger.error(f"Error getting chunk count: {str(e)}")
                st.metric("Total Chunks", "N/A")
            st.metric("Messages", len(st.session_state.chat_history))

if __name__ == "__main__":
    main()