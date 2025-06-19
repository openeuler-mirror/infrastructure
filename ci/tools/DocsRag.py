# To run this script, we need pip some component like this:.
#    1 pip install langchain
#    2 python.exe -m pip install --upgrade pip
#    3 pip install langchain-community
#    4 pip install langchain_deepseek
#    5 pip install sentence-transformers
#    6 pip install -U langchain-huggingface
#    7 pip install hf_xet
#    8 pip install faiss-cpu
import argparse
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from langchain_deepseek import ChatDeepSeek
from langchain.chains import RetrievalQA

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

# LOCAL Knowledge
def load_knowledge_base()->str:
    knowledge_base = """
This is a test text.
"""
    return knowledge_base

#2.分开和向量化
def create_vector_db(txt:str, embeddings: Embeddings) -> FAISS:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,#每块最多100字符
        chunk_overlap=20,#相邻重叠20字符
    )
    # 生产适合大小文本
    chunks = text_splitter.create_documents([txt])

    # 创建向量
    vector_db = FAISS.from_documents(chunks, embeddings)
    return vector_db

#3.检索生成
def setup_rag_chain(vector_db:FAISS, llm) ->RetrievalQA:
    #创检索器
    retriever = vector_db.as_retriever(search_kwargs={"k": 2})
    #创RAG链
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    return rag_chain

#获取embeddings
def get_local_embeddings() -> HuggingFaceEmbeddings:
    """加载本地嵌入模型，兼容TensorFlow格式"""

    embedder = HuggingFaceEmbeddings(
        model_name='bert-base-chinese',
        model_kwargs={"device": "cpu"}
    )
    return embedder

#获取语言模型
def get_deepseek_llm(api_key:str):
    os.environ["DEEPSEEK_API_KEY"] = api_key
    return ChatDeepSeek(
        model="deepseek-chat",  # 支持模型如deepseek-chat（DeepSeek-V3）、deepseek-reasoner（DeepSeek-R1）
        temperature=0,
        max_tokens=1024
    )


def main():
    parser = argparse.ArgumentParser(description="First RAG demo.")
    parser.add_argument("--api_key", type=str, default="*****", help="Please input AI API key.")

    args = parser.parse_args()
    key = args.api_key
    if not key:
        print("The Key input Error.")
        return

    #加载文档库
    knowledge_base = load_knowledge_base()

    #创建embedding模型
    embeddings = get_local_embeddings()
    vector_db = create_vector_db(knowledge_base, embeddings)

    #创建llm
    print(key)
    llm = get_deepseek_llm(key)
    rag_chain = setup_rag_chain(vector_db, llm)

    print("\nRAG系统已就绪，请输入问题(输入'Q'结束对话):")
    while True:
        user_query = input("\n问题: ")
        if user_query.lower() == "Q":
            break

        # 执行RAG流程
        result = rag_chain({"query": user_query})

        # 显示结果
        print("\n回答:")
        print(result["result"])

        # 显示来源
        print("\n参考内容:")
        for doc in result["source_documents"]:
            print(f"- {doc.page_content[:100]}...")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
