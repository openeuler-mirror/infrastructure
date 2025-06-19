import unittest
from unittest.mock import Mock, patch
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores import FAISS
from myFirstRagDemo import (
    load_knowledge_base,
    create_vector_db,
    setup_rag_chain,
    get_local_embeddings,
    get_deepseek_llm
)
import os

class TestRAGDemo(unittest.TestCase):
    def test_load_knowledge_base(self):
        """测试知识库加载功能"""
        # 执行函数
        knowledge_base = load_knowledge_base()
        
        # 验证结果
        self.assertEqual(knowledge_base.strip(), "This is a test text.")
        self.assertIsInstance(knowledge_base, str)
    
    def test_create_vector_db(self):
        """测试向量数据库创建功能"""
        # 创建模拟嵌入模型
        class MockEmbeddings(Embeddings):
            def embed_query(self, text):
                return [0.1] * 768  # 假设BERT输出768维向量
            
            def embed_documents(self, texts):
                return [[0.1] * 768 for _ in texts]
        
        mock_embeddings = MockEmbeddings()
        test_text = "这是一个测试文本，用于验证向量数据库创建功能。"
        
        # 执行函数
        vector_db = create_vector_db(test_text, mock_embeddings)
        
        # 验证结果
        self.assertIsInstance(vector_db, FAISS)
        self.assertEqual(len(vector_db.docstore._dict), 1)  # 检查文档数量
    
    def test_setup_rag_chain(self):
        """测试RAG链设置功能"""
        # 创建模拟向量数据库
        class MockFAISS(FAISS):
            def as_retriever(self, search_kwargs=None):
                return Mock()  # 返回模拟检索器
        
        mock_vector_db = MockFAISS()
        mock_llm = Mock()  # 模拟语言模型
        
        # 执行函数
        rag_chain = setup_rag_chain(mock_vector_db, mock_llm)
        
        # 验证结果
        self.assertIsNotNone(rag_chain)
        self.assertEqual(rag_chain.return_source_documents, True)
    
    def test_get_local_embeddings(self):
        """测试本地嵌入模型加载功能"""
        # 执行函数
        embeddings = get_local_embeddings()
        
        # 验证结果
        self.assertIsNotNone(embeddings)
        self.assertEqual(embeddings.model_name, 'bert-base-chinese')
        self.assertEqual(embeddings.model_kwargs, {"device": "cpu"})
    
    @patch('langchain_deepseek.ChatDeepSeek')
    def test_get_deepseek_llm(self, mock_chat_deepseek):
        """测试DeepSeek语言模型加载功能"""
        # 设置测试API密钥
        test_api_key = "test_api_key_123"
        
        # 执行函数
        llm = get_deepseek_llm(test_api_key)
        
        # 验证环境变量是否正确设置
        self.assertEqual(os.environ["DEEPSEEK_API_KEY"], test_api_key)
        
        # 验证ChatDeepSeek是否被正确调用
        mock_chat_deepseek.assert_called_once_with(
            model="deepseek-chat",
            temperature=0,
            max_tokens=1024
        )
        self.assertIsInstance(llm, Mock)  # 由于使用了mock，应该返回一个Mock对象

if __name__ == '__main__':
    unittest.main()