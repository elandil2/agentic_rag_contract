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
import re
import pandas as pd
from langchain_core.documents import Document

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

def extract_customer_name(filename: str) -> str:
    """Extract customer name from filename"""
    # Remove file extension
    name = os.path.splitext(filename)[0]

    # Common customer names to look for
    customers = ['TESLA', 'BARRY', 'PRYSMIAN', 'CARLSBERG', 'CALLEBAUT']

    # Check if any customer name is in the filename (case insensitive)
    filename_upper = name.upper()
    for customer in customers:
        if customer in filename_upper:
            return customer.title()

    # If no known customer found, try to extract from path or filename
    # Pattern: Look for capital words or words after common separators
    parts = re.split(r'[_\-\s]+', name)
    if parts:
        # Return first meaningful part (skip dates and common words)
        for part in parts:
            if len(part) > 3 and not part.isdigit() and part.upper() not in ['FTL', 'LTL', 'TERMS', 'CONDITIONS']:
                return part.title()

    return "Unknown Customer"

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
        """Process uploaded contract documents including Excel files with multiple sheets"""
        try:
            all_documents = []

            for uploaded_file in uploaded_files:
                # Extract customer name from filename
                customer_name = extract_customer_name(uploaded_file.name)

                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    tmp_file_path = tmp_file.name

                # Load document based on type
                if uploaded_file.name.endswith('.pdf'):
                    loader = PyPDFLoader(tmp_file_path)
                    documents = loader.load()

                elif uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
                    # Load Excel file with all sheets
                    try:
                        excel_file = pd.ExcelFile(tmp_file_path)
                        documents = []

                        for sheet_name in excel_file.sheet_names:
                            df = pd.read_excel(tmp_file_path, sheet_name=sheet_name)

                            # Convert DataFrame to text
                            sheet_text = f"Sheet: {sheet_name}\n\n"
                            sheet_text += df.to_string(index=False)

                            # Create Document object
                            doc = Document(
                                page_content=sheet_text,
                                metadata={
                                    'source': uploaded_file.name,
                                    'sheet_name': sheet_name,
                                    'customer': customer_name
                                }
                            )
                            documents.append(doc)

                        logger.info(f"Loaded {len(excel_file.sheet_names)} sheets from {uploaded_file.name}")
                        excel_file.close()  # Close Excel file to release file lock on Windows
                    except Exception as e:
                        logger.error(f"Error reading Excel file {uploaded_file.name}: {str(e)}")
                        st.warning(f"Could not process Excel file {uploaded_file.name}: {str(e)}")
                        documents = []

                else:
                    # Text file
                    loader = TextLoader(tmp_file_path)
                    documents = loader.load()

                # Add metadata to all documents
                for doc in documents:
                    if 'source' not in doc.metadata:
                        doc.metadata['source'] = uploaded_file.name
                    doc.metadata['upload_time'] = datetime.now().isoformat()
                    doc.metadata['customer'] = customer_name

                all_documents.extend(documents)
                logger.info(f"Processed {uploaded_file.name} - Customer: {customer_name}, Documents: {len(documents)}")

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
            logger.info(f"Created {len(splits)} document chunks from {len(all_documents)} documents")

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
            logger.error(f"Error details: {str(e)}", exc_info=True)
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

                # Format the retrieved information with source tracking
                result = ""
                for i, doc in enumerate(relevant_docs, 1):
                    source = doc.metadata.get('source', 'Unknown')
                    customer = doc.metadata.get('customer', 'Unknown Customer')
                    sheet_name = doc.metadata.get('sheet_name', None)
                    content = doc.page_content.strip()

                    # Include source information for each retrieved chunk
                    source_info = f"[Customer: {customer} | File: {source}"
                    if sheet_name:
                        source_info += f" | Sheet: {sheet_name}"
                    source_info += "]\n"

                    result += source_info + content + "\n\n"

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

        @tool
        def calculate_trip_cost(
            base_rate: Annotated[float, "Base FTL rate (€/km or €/shipment)"],
            distance_km: Annotated[float, "Distance in kilometers"] = 0,
            fuel_surcharge_pct: Annotated[float, "Fuel surcharge percentage (e.g., 25 for 25%)"] = 25,
            waiting_hours: Annotated[float, "Waiting time in hours beyond free time"] = 0,
            waiting_rate: Annotated[float, "Waiting charge rate (€/hour)"] = 35,
            multi_stop_fee: Annotated[float, "Additional fee for multi-stop delivery (€)"] = 0
        ) -> str:
            """Calculate total trip cost for FTL transportation including all charges"""
            try:
                # Calculate base cost
                if distance_km > 0:
                    base_cost = base_rate * distance_km
                else:
                    base_cost = base_rate  # Flat rate per shipment

                # Calculate fuel surcharge
                fuel_cost = base_cost * (fuel_surcharge_pct / 100)

                # Calculate waiting charges
                waiting_cost = waiting_hours * waiting_rate

                # Calculate total
                total_cost = base_cost + fuel_cost + waiting_cost + multi_stop_fee

                # Format result
                result = f"""**Trip Cost Calculation:**

📦 Base Rate: €{base_cost:.2f}
⛽ Fuel Surcharge ({fuel_surcharge_pct}%): €{fuel_cost:.2f}
⏰ Waiting Charges ({waiting_hours}h @ €{waiting_rate}/h): €{waiting_cost:.2f}
🚛 Multi-Stop Fee: €{multi_stop_fee:.2f}

**💰 Total Trip Cost: €{total_cost:.2f}**

Breakdown:
- Base + Fuel: €{base_cost + fuel_cost:.2f}
- Additional Charges: €{waiting_cost + multi_stop_fee:.2f}
"""
                return result

            except Exception as e:
                return f"Error calculating trip cost: {str(e)}"

        @tool
        def check_kpi_compliance(
            kpi_type: Annotated[str, "KPI type: 'otd', 'claims', 'booking_acceptance', 'pod_upload'"],
            actual_value: Annotated[float, "Actual KPI value (percentage, e.g., 96.5 for 96.5%)"],
            target_value: Annotated[float, "Target KPI value (percentage)"] = 0,
            minimum_value: Annotated[float, "Minimum acceptable KPI value (percentage)"] = 0,
            customer: Annotated[str, "Customer name (Tesla, Barry, Prysmian, Carlsberg)"] = "General"
        ) -> str:
            """Check if KPI performance meets contract requirements and calculate penalties if applicable"""
            try:
                # Define standard KPI thresholds (can be overridden by parameters)
                kpi_standards = {
                    "otd": {"target": 98, "minimum": 95, "penalty": "7% chargeback or lane reassignment"},
                    "claims": {"target": 0.2, "minimum": 0.5, "penalty": "Contract review"},
                    "booking_acceptance": {"target": 99, "minimum": 95, "penalty": "€75/rejection"},
                    "pod_upload": {"target": 95, "minimum": 90, "penalty": "Administrative fee"}
                }

                kpi_info = kpi_standards.get(kpi_type.lower(), {"target": target_value, "minimum": minimum_value, "penalty": "See contract"})

                # Use provided values or defaults
                target = target_value if target_value > 0 else kpi_info["target"]
                minimum = minimum_value if minimum_value > 0 else kpi_info["minimum"]
                penalty_info = kpi_info["penalty"]

                # Determine compliance status
                if actual_value >= target:
                    status = "✅ EXCELLENT"
                    message = f"Performance exceeds target! Keep up the great work."
                elif actual_value >= minimum:
                    status = "⚠️ WARNING"
                    message = f"Performance meets minimum but below target. Improvement needed."
                else:
                    status = "❌ NON-COMPLIANT"
                    message = f"Performance below minimum threshold. Penalty applies: {penalty_info}"

                # Format result
                result = f"""**KPI Compliance Check: {kpi_type.upper()}**
Customer: {customer}

📊 Current Performance: {actual_value}%
🎯 Target: {target}%
⚡ Minimum Acceptable: {minimum}%

**Status: {status}**
{message}

Gap Analysis:
- vs Target: {actual_value - target:+.1f}%
- vs Minimum: {actual_value - minimum:+.1f}%
"""

                if actual_value < minimum:
                    result += f"\n⚠️ **Action Required:** {penalty_info}"
                    if "consecutive months" in penalty_info.lower() or kpi_type == "otd":
                        result += "\n📌 Note: Sustained non-compliance may result in lane reassignment or contract termination."

                return result

            except Exception as e:
                return f"Error checking KPI compliance: {str(e)}"

        return retrieve_contract_info, analyze_contract_terms, summarize_contract, calculate_trip_cost, check_kpi_compliance
    
    def create_supervisor(self):
        """Create the supervisor multi-agent system using new LangGraph API"""

        retrieve_tool, analyze_tool, summarize_tool, calc_cost_tool, kpi_check_tool = self.create_tools()

        # Create tool nodes for each agent
        retriever_tools = ToolNode([retrieve_tool])
        analyst_tools = ToolNode([analyze_tool])
        summarizer_tools = ToolNode([summarize_tool])
        # Domain-specific logistics tools (available for future integration)
        # calc_cost_tool and kpi_check_tool can be added to analyst_tools if needed

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
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for professional styling
    st.markdown("""
        <style>
        /* Logo styling */
        .logo-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px 30px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .logo-text {
            color: white;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin: 0;
            font-family: 'Helvetica Neue', sans-serif;
        }
        .logo-subtitle {
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
            margin-top: 5px;
            letter-spacing: 1px;
        }

        /* Badge styling for counts */
        .custom-badge {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin-left: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            vertical-align: middle;
        }

        /* Section header styling */
        .section-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }

        /* Custom button styling */
        .custom-button {
            display: inline-block;
            width: 100%;
            padding: 12px 20px;
            margin: 8px 0;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            color: #333;
            font-size: 15px;
            font-weight: 600;
            text-align: left;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .custom-button:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        .custom-button-icon {
            font-size: 18px;
            margin-right: 10px;
        }

        /* Improve default streamlit button styling */
        .stButton>button {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
            border: 2px solid #e0e0e0 !important;
            border-radius: 10px !important;
            color: #333 !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            padding: 12px 20px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
            height: auto !important;
            min-height: 48px !important;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border-color: #667eea !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
        }
        .stButton>button:active {
            transform: translateY(0px) !important;
        }

        /* Button icons */
        .stButton>button>div {
            display: flex;
            align-items: center;
            justify-content: flex-start;
        }
        </style>
    """, unsafe_allow_html=True)

    # Professional Logo
    st.markdown("""
        <div class="logo-container">
            <h1 class="logo-text">ContractAI</h1>
            <p class="logo-subtitle">Advanced Contract Analysis System</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("Upload contracts and ask questions about them")
    
    # Initialize system
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = ContractRAGSystem()
    
    # Sidebar for document upload
    with st.sidebar:
        # Professional Logo in Sidebar
        st.markdown("""
            <div style="text-align: center; padding: 20px 0; margin-bottom: 30px;">
                <svg width="150" height="150" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                    <!-- Background Circle -->
                    <defs>
                        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <circle cx="100" cy="100" r="90" fill="url(#grad1)" opacity="0.9"/>
                    <!-- Document Icon -->
                    <rect x="65" y="50" width="70" height="90" rx="5" fill="white" opacity="0.95"/>
                    <line x1="75" y1="70" x2="125" y2="70" stroke="#667eea" stroke-width="3" stroke-linecap="round"/>
                    <line x1="75" y1="85" x2="115" y2="85" stroke="#667eea" stroke-width="3" stroke-linecap="round"/>
                    <line x1="75" y1="100" x2="120" y2="100" stroke="#667eea" stroke-width="3" stroke-linecap="round"/>
                    <line x1="75" y1="115" x2="110" y2="115" stroke="#764ba2" stroke-width="3" stroke-linecap="round"/>
                    <!-- AI Sparkle -->
                    <circle cx="140" cy="60" r="8" fill="#FFD700"/>
                    <path d="M 140 52 L 142 58 L 148 60 L 142 62 L 140 68 L 138 62 L 132 60 L 138 58 Z" fill="white"/>
                </svg>
                <h2 style="color: #667eea; margin-top: 10px; font-weight: 700; letter-spacing: 1px;">ContractAI</h2>
                <p style="color: #666; font-size: 12px; margin-top: -10px;">Powered by RAG Technology</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <h3 style="color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 20px;">
                <span style="font-size: 20px;">📂</span> Document Management
            </h3>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Upload Contract Documents",
            type=['pdf', 'txt', 'xlsx', 'xls'],
            accept_multiple_files=True,
            help="Upload contract documents (PDF, TXT, Excel)"
        )
        
        if uploaded_files:
            if st.button("Process Documents"):
                with st.spinner("Processing documents..."):
                    if st.session_state.rag_system.process_documents(uploaded_files):
                        st.success(f"✓ Processed {len(uploaded_files)} documents")
                        st.session_state.supervisor = st.session_state.rag_system.create_supervisor()
                    else:
                        st.error("Failed to process documents")

        # System prompt configuration
        st.markdown("""
            <h3 style="color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin: 30px 0 20px 0;">
                <span style="font-size: 20px;">⚙</span> System Configuration
            </h3>
        """, unsafe_allow_html=True)
        
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
            if st.button("⬇ Download Conversation"):
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
        st.markdown("""
            <h2 style="color: #667eea; margin-bottom: 20px;">
                <span style="font-size: 28px;">💭</span> Chat Interface
            </h2>
        """, unsafe_allow_html=True)
        
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
        # Professional Analysis Options Panel
        st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 20px;
                        border-radius: 15px;
                        margin-bottom: 20px;
                        box-shadow: 0 8px 16px rgba(0,0,0,0.1);">
                <h2 style="color: white; margin: 0; font-size: 24px; font-weight: 700;">
                    <span style="font-size: 26px;">📋</span> Analysis Options
                </h2>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 14px;">
                    AI-Powered Contract Intelligence
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Frequent Questions Section
        st.markdown("""
            <div style="background: #f8f9fa;
                        padding: 15px;
                        border-radius: 10px;
                        border-left: 4px solid #667eea;
                        margin-bottom: 20px;">
                <h3 style="color: #667eea; margin: 0 0 10px 0; font-size: 18px;">
                    ❓ Frequent Questions (23)
                </h3>
                <p style="color: #666; margin: 0; font-size: 13px;">Click any question to analyze contracts</p>
            </div>
        """, unsafe_allow_html=True)

        # 23 Questions from questions.csv
        questions = [
            "What is customers name?",
            "What is the customers sector?",
            "Which product do customers offer?",
            "When is the deadline?",
            "How many rounds is the tender?",
            "What is the service type? Explain regularly intermodal, short-sea, road, rail",
            "Which types of equipment / vehicle are in demand?",
            "What is the ADR conditions?",
            "If the contract mentions the existence of any ADR, summarise its type.",
            "Whats is the ADR class types?",
            "If the contract mentions the existence of any temperature controlled or reefer or frigo, summarise its type and tell me what is the ratings?",
            "What is the payment term?",
            "What is the Expected Go-Live Date?",
            "How long is price validity?",
            "Is contract mentions double driver?",
            "Is contract mentions safety equipments? If the contract mentions safety conditions, summarise.",
            "What is pre-advise? When does the customer request a vehicle and how long do we have to fulfil the request?",
            "Summarise KPI conditions. Is there any penalty or demurrage fee?",
            "If contract contain, free time costs, weekend loading, Summarise",
            "Summarise if there are FSC requirements",
            "What is the base fuel rate?",
            "What is the fuel effect ratio?"
        ]

        # Create scrollable container
        with st.container():
            for idx, question in enumerate(questions, 1):
                # Shorter label for button
                btn_label = f"Q{idx}: {question[:50]}{'...' if len(question) > 50 else ''}"

                if st.button(btn_label, key=f"q_{idx}", use_container_width=True, help=question):
                    if not st.session_state.supervisor:
                        st.warning("Please upload and process documents first!")
                    else:
                        with st.spinner(f"Analyzing Q{idx}..."):
                            try:
                                config = {"configurable": {"thread_id": f"question_{idx}"}}
                                response = st.session_state.supervisor.invoke({
                                    "messages": [HumanMessage(content=question)],
                                    "next": ""
                                }, config=config)
                                ai_response = response["messages"][-1].content if response.get("messages") else "No response"
                                st.success(f"✓ Q{idx} Answered!")
                                st.write(ai_response)

                                # Add to chat history
                                st.session_state.chat_history.append({
                                    "role": "user",
                                    "content": question
                                })
                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": ai_response
                                })
                            except Exception as e:
                                logger.error(f"Error in Q{idx}: {str(e)}")
                                st.error(f"Error: {str(e)}")

        # Statistics Section with Professional Cards
        if st.session_state.rag_system and st.session_state.rag_system.vector_store:
            st.markdown("""
                <div style="background: #f8f9fa;
                            padding: 15px;
                            border-radius: 10px;
                            border-left: 4px solid #667eea;
                            margin: 20px 0;">
                    <h3 style="color: #667eea; margin: 0 0 15px 0; font-size: 18px;">
                        📊 Statistics
                    </h3>
                </div>
            """, unsafe_allow_html=True)

            # Documents Loaded Card
            doc_count = len(uploaded_files) if uploaded_files else 0
            st.markdown(f"""
                <div style="background: white;
                            padding: 15px;
                            border-radius: 8px;
                            margin: 10px 0;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                            border-left: 3px solid #667eea;">
                    <p style="color: #666; margin: 0; font-size: 12px; font-weight: 600; text-transform: uppercase;">Documents Loaded</p>
                    <h2 style="color: #667eea; margin: 5px 0 0 0; font-size: 32px; font-weight: 700;">{doc_count}</h2>
                </div>
            """, unsafe_allow_html=True)

            # Total Chunks Card
            try:
                chunk_count = st.session_state.rag_system.vector_store._collection.count()
            except Exception as e:
                logger.error(f"Error getting chunk count: {str(e)}")
                chunk_count = "N/A"

            st.markdown(f"""
                <div style="background: white;
                            padding: 15px;
                            border-radius: 8px;
                            margin: 10px 0;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                            border-left: 3px solid #764ba2;">
                    <p style="color: #666; margin: 0; font-size: 12px; font-weight: 600; text-transform: uppercase;">Total Chunks</p>
                    <h2 style="color: #764ba2; margin: 5px 0 0 0; font-size: 32px; font-weight: 700;">{chunk_count}</h2>
                </div>
            """, unsafe_allow_html=True)

            # Messages Card
            msg_count = len(st.session_state.chat_history)
            st.markdown(f"""
                <div style="background: white;
                            padding: 15px;
                            border-radius: 8px;
                            margin: 10px 0;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                            border-left: 3px solid #FF6B6B;">
                    <p style="color: #666; margin: 0; font-size: 12px; font-weight: 600; text-transform: uppercase;">Messages</p>
                    <h2 style="color: #FF6B6B; margin: 5px 0 0 0; font-size: 32px; font-weight: 700;">{msg_count}</h2>
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()