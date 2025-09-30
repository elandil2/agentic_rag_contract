"""
Comprehensive Test Suite for RAG Contract Analysis System
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import modules to test
from config import validate_config, GROQ_MODEL, CHUNK_SIZE
from main import ContractRAGSystem, AgentState


class TestConfiguration:
    """Test configuration management"""

    def test_groq_api_key_present(self):
        """Test that GROQ_API_KEY is configured"""
        from config import GROQ_API_KEY
        assert GROQ_API_KEY is not None, "GROQ_API_KEY must be set in .env"

    def test_valid_model_name(self):
        """Test that a valid Groq model is configured"""
        valid_models = [
            "llama3-groq-70b-8192-tool-use-preview",
            "llama3-70b-8192",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        assert GROQ_MODEL in valid_models, f"Invalid model: {GROQ_MODEL}"

    def test_chunk_size_reasonable(self):
        """Test that chunk size is within reasonable bounds"""
        assert 100 <= CHUNK_SIZE <= 5000, "Chunk size should be between 100 and 5000"

    def test_validate_config_function(self):
        """Test configuration validation function"""
        try:
            result = validate_config()
            assert result is True
        except ValueError as e:
            pytest.fail(f"Configuration validation failed: {str(e)}")


class TestContractRAGSystem:
    """Test the ContractRAGSystem class"""

    @pytest.fixture
    def rag_system(self):
        """Create a RAG system instance for testing"""
        return ContractRAGSystem()

    def test_initialization(self, rag_system):
        """Test that RAG system initializes correctly"""
        assert rag_system.llm is not None
        assert rag_system.embeddings is not None
        assert rag_system.vector_store is None  # Not initialized until docs processed
        assert rag_system.retriever is None

    def test_embeddings_loaded(self, rag_system):
        """Test that embeddings model is loaded"""
        assert hasattr(rag_system.embeddings, 'embed_documents')
        assert hasattr(rag_system.embeddings, 'embed_query')

    @patch('main.PyPDFLoader')
    @patch('main.TextLoader')
    def test_process_documents_pdf(self, mock_text_loader, mock_pdf_loader, rag_system):
        """Test document processing with PDF files"""
        # Create mock uploaded file
        mock_file = Mock()
        mock_file.name = "test.pdf"
        mock_file.getbuffer.return_value = b"test content"

        # Mock the loader
        mock_loader_instance = Mock()
        mock_loader_instance.load.return_value = [
            Mock(page_content="Test contract content", metadata={})
        ]
        mock_pdf_loader.return_value = mock_loader_instance

        # Test processing
        with patch('tempfile.NamedTemporaryFile'), \
             patch('os.unlink'), \
             patch.object(rag_system, 'embeddings'):
            result = rag_system.process_documents([mock_file])
            assert result is True

    def test_create_tools(self, rag_system):
        """Test that tools are created correctly"""
        tools = rag_system.create_tools()
        assert len(tools) == 3  # retrieve, analyze, summarize
        assert all(callable(tool) for tool in tools)

    def test_create_supervisor(self, rag_system):
        """Test supervisor workflow creation"""
        supervisor = rag_system.create_supervisor()
        assert supervisor is not None
        # Test that it's a compiled graph
        assert hasattr(supervisor, 'invoke')


class TestTools:
    """Test individual tools"""

    @pytest.fixture
    def rag_system_with_docs(self):
        """Create a RAG system with mock documents"""
        rag_system = ContractRAGSystem()
        # Mock the retriever
        rag_system.retriever = Mock()
        rag_system.retriever.get_relevant_documents.return_value = [
            Mock(page_content="Contract clause about payment", metadata={"source": "test.pdf"})
        ]
        return rag_system

    def test_retrieve_contract_info_tool(self, rag_system_with_docs):
        """Test the retrieve_contract_info tool"""
        retrieve_tool, _, _ = rag_system_with_docs.create_tools()
        result = retrieve_tool.invoke("payment terms")
        assert "Contract clause" in result or "Retrieved" in result

    def test_retrieve_without_docs(self):
        """Test retrieval when no documents are loaded"""
        rag_system = ContractRAGSystem()
        retrieve_tool, _, _ = rag_system.create_tools()
        result = retrieve_tool.invoke("test query")
        assert "No contracts loaded" in result

    def test_analyze_contract_terms_tool(self, rag_system_with_docs):
        """Test the analyze_contract_terms tool"""
        _, analyze_tool, _ = rag_system_with_docs.create_tools()
        result = analyze_tool.invoke({
            "contract_text": "Payment terms: Net 30 days",
            "analysis_type": "general"
        })
        assert isinstance(result, str)
        assert len(result) > 0

    def test_summarize_contract_tool(self, rag_system_with_docs):
        """Test the summarize_contract tool"""
        _, _, summarize_tool = rag_system_with_docs.create_tools()
        # Mock the LLM response
        with patch.object(rag_system_with_docs.llm, 'invoke') as mock_invoke:
            mock_response = Mock()
            mock_response.content = "Contract summary"
            mock_invoke.return_value = mock_response

            result = summarize_tool.invoke("Contract text here")
            assert "summary" in result.lower() or "Contract" in result


class TestAgentState:
    """Test the AgentState TypedDict"""

    def test_agent_state_structure(self):
        """Test that AgentState has correct structure"""
        from main import AgentState
        # Check that it's a TypedDict with required fields
        assert 'messages' in AgentState.__annotations__
        assert 'next' in AgentState.__annotations__


class TestEmbeddings:
    """Test embeddings functionality"""

    @pytest.fixture
    def rag_system(self):
        """Create RAG system for embeddings tests"""
        return ContractRAGSystem()

    def test_embed_documents(self, rag_system):
        """Test embedding documents"""
        texts = ["This is a test contract", "This is another test"]
        embeddings = rag_system.embeddings.embed_documents(texts)
        assert len(embeddings) == 2
        assert len(embeddings[0]) > 0  # Should have embedding dimensions
        assert all(isinstance(x, float) for x in embeddings[0])

    def test_embed_query(self, rag_system):
        """Test embedding a single query"""
        query = "What are the payment terms?"
        embedding = rag_system.embeddings.embed_query(query)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)


class TestWorkflow:
    """Test the LangGraph workflow"""

    @pytest.fixture
    def supervisor(self):
        """Create supervisor for testing"""
        rag_system = ContractRAGSystem()
        return rag_system.create_supervisor()

    def test_supervisor_invoke(self, supervisor):
        """Test invoking the supervisor"""
        from langchain_core.messages import HumanMessage
        config = {"configurable": {"thread_id": "test_thread"}}

        # Test basic invocation
        result = supervisor.invoke({
            "messages": [HumanMessage(content="Hello")],
            "next": ""
        }, config=config)

        assert "messages" in result
        assert isinstance(result["messages"], list)


class TestIntegration:
    """Integration tests"""

    def test_end_to_end_mock(self):
        """Test end-to-end workflow with mocked components"""
        # Create system
        rag_system = ContractRAGSystem()

        # Mock file upload
        mock_file = Mock()
        mock_file.name = "test.txt"
        mock_file.getbuffer.return_value = b"Test contract with payment terms"

        # Mock dependencies
        with patch('main.TextLoader') as mock_loader, \
             patch('tempfile.NamedTemporaryFile'), \
             patch('os.unlink'):

            mock_loader_instance = Mock()
            mock_loader_instance.load.return_value = [
                Mock(
                    page_content="Test contract with payment terms",
                    metadata={"source": "test.txt"}
                )
            ]
            mock_loader.return_value = mock_loader_instance

            # Process documents
            result = rag_system.process_documents([mock_file])
            assert result is True

            # Verify vector store created
            assert rag_system.vector_store is not None
            assert rag_system.retriever is not None


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_file_processing(self):
        """Test handling of invalid files"""
        rag_system = ContractRAGSystem()

        # Create invalid mock file
        mock_file = Mock()
        mock_file.name = "test.invalid"
        mock_file.getbuffer.side_effect = Exception("Invalid file")

        result = rag_system.process_documents([mock_file])
        assert result is False

    def test_missing_retriever(self):
        """Test retrieval tool when retriever is not initialized"""
        rag_system = ContractRAGSystem()
        retrieve_tool, _, _ = rag_system.create_tools()

        result = retrieve_tool.invoke("test query")
        assert "No contracts loaded" in result


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])