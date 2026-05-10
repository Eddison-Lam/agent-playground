import logging
import os
from datetime import datetime, timedelta
import chromadb
import ollama
log_dir = "log/rag"
if not os.path.exists(log_dir):os.makedirs(log_dir)
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_dir, f"rag_{current_time}.log")
logging.basicConfig(
    level=logging.INFO, 
    filename=log_filename, 
    encoding='utf-8',
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGManager:
    class QueryError(Exception):
        pass

    def __init__(self, db_path='my_mem', collection_name='chat_hist', EMBED_MODEL="nomic-embed-text"):
        self.db_path = db_path
        self.collection_name = collection_name
        self.embed_model = EMBED_MODEL
        
        os.makedirs(db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(self.collection_name)
        
        logger.info(f"RAGManager initialized. Collection: {self.collection_name} | Count: {self.collection.count()}")

    def add_mem(self, text: str, metadata=None):
        if metadata is None:
            metadata = {}

        metadata["timestamp"] = datetime.now().timestamp()
        mem_id = f'{metadata["timestamp"]:.0f}_{self.collection.count()}'

        try:
            embedding = self._get_embedding(text)

            self.collection.add(
                ids=[mem_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            logger.info(f"Memory added | ID: {mem_id}")
            return mem_id
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return None

    def get_relevant_memories(self, query: str, n_results: int = 6) -> str:
        try:
            embedding = self._get_embedding(query)
            
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                include=["documents", "metadatas"]
            )
            
            docs = results.get('documents', [[]])[0]
            return "\n\n".join(docs) if docs else ""
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return ""

    def delete_by_id(self, mem_id: str):
        try:
            self.collection.delete(ids=[mem_id])
            logger.info(f"🗑️ Memory deleted: {mem_id}")
        except Exception as e:
            logger.error(f"Delete failed: {e}")

    def export_mem_to_markdown(self, time_arg='day', keyword=None):
        try:
            results = self._query_logic(time_arg, keyword)
            
            if not results['data']['ids']:
                return None
            
            file_name = f"RAG_export_{datetime.now().timestamp()}_{time_arg}_{keyword if keyword else ''}.md"
            self._build_markdown(results, file_name)
            return file_name
            
        except self.QueryError as e:
            print(f"Query error: {e}")
            return None
        except IOError as e:
            print(f"File write error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def _build_markdown(self, results, file_name):
        info = results['info']
        data = results['data']
        
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                lines = [
                    "# Agent RAG Memory Export\n",
                    "### 🔍 Search Context",
                    f"- **Time Range**: `{info['time_arg']}`",
                    f"- **Keyword Filter**: `{info['keyword']}`",
                    f"- **Exported At**: {info['exported_at']}",
                    f"- **Total Entries**: {info['count']}\n",
                    "| ID | Timestamp | Content Preview | Command |",
                    "| :--- | :--- | :--- | :--- |"
                ]
                f.writelines("\n".join(lines))
                
                data_rows = []
                for m_id, doc, meta in zip(
                    data['ids'], 
                    data['documents'], 
                    data['metadatas']
                ):
                    try:
                        timestamp_str = self._safe_timestamp_to_str(
                            meta.get('timestamp', 0)
                        )
                        content_preview = self._safe_preview(doc)
                        row = f"| `{m_id}` | {timestamp_str} | {content_preview} | `/del {m_id}` |"
                        data_rows.append(row)
                    except Exception as e:
                        print(f"Warning: Failed to format row {m_id}: {e}")
                        continue
                
                if data_rows:
                    f.writelines("\n" + "\n".join(data_rows))
            
            return file_name
            
        except IOError as e:
            raise IOError(f"Cannot write to file {file_name}: {e}")
    
    def _safe_timestamp_to_str(self, timestamp):
        try:
            if not isinstance(timestamp, (int, float)):
                return "Invalid"
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
        except (ValueError, OSError):
            return "Invalid"

    def _safe_preview(self, doc):
        try:
            return doc.replace('\n', ' ')[:50] + "..."
        except AttributeError:
            return str(doc)[:50] + "..."

    def _query_logic(self, time_arg, keyword):
        now = datetime.now()
        start_ts = 0
        end_ts = None
        
        try:
            match time_arg:
                case 'hour':
                    start_ts = (now - timedelta(hours=1)).timestamp()
                case 'day':
                    start_ts = (now - timedelta(days=1)).timestamp()
                case 'week':
                    start_ts = (now - timedelta(weeks=1)).timestamp()
                case 'month':
                    start_ts = (now - timedelta(days=30)).timestamp()
                case 'all':
                    start_ts = datetime.fromtimestamp(0).timestamp()
                case _:
                    try:
                        start_dt = datetime.strptime(time_arg, "%Y-%m-%d")
                        start_ts = start_dt.timestamp()
                        end_ts = (start_dt + timedelta(days=1)).timestamp()
                    except ValueError:
                        raise self.QueryError(
                            "Invalid time argument. Use: 'hour', 'day', 'week', 'month', 'all', or 'YYYY-MM-DD'"
                        )
            
            where_meta = (
                {"$and": [
                    {"timestamp": {"$gte": start_ts}},
                    {"timestamp": {"$lt": end_ts}}
                ]}
                if end_ts
                else {"timestamp": {"$gte": start_ts}}
            )
            
            where_doc = {"$contains": keyword} if keyword else None
            
            raw_data = self.collection.get(
                where=where_meta,
                where_document=where_doc,
                include=["documents", "metadatas"]
            )
            
            return {
                "info": {
                    "time_arg": time_arg,
                    "keyword": keyword if keyword else "None",
                    "count": len(raw_data['ids']),
                    "exported_at": now.strftime('%Y-%m-%d %H:%M:%S')
                },
                "data": raw_data
            }
            
        except self.QueryError:
            raise
        except Exception as e:
            raise self.QueryError(f"Database query failed: {e}")