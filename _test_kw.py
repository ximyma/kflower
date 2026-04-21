import os, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'E:\kkflower\kflower-backend')
os.environ['HF_HUB_OFFLINE'] = '1'
from app.core.ai_digital_base.local_services import text_parser_service
text = 'AI knowledge base system test content with keywords about vector search and semantic matching.'
r = text_parser_service.extract_keywords(text, top_k=5, method='tfidf')
print(f'Keywords: {r}')
r2 = text_parser_service.extract_summary(text, max_length=100)
print(f'Summary: {r2}')
