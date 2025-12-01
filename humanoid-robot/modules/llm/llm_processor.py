import threading
import time
import requests
from llama_cpp import Llama

class LLMProcessor:
    def __init__(self, output_queue, config):
        self.output_queue = output_queue
        self.config = config
        self.running = False
        self.offline_llm = None
        self.offline_available = False
        
        # Initialize offline LLM with error handling
        try:
            import os
            if os.path.exists(self.config.OFFLINE_LLM_PATH):
                self.offline_llm = Llama(
                    model_path=self.config.OFFLINE_LLM_PATH,
                    n_ctx=self.config.LLM_CONTEXT_LENGTH,
                    n_threads=4,  # Use 4 threads for better performance
                    verbose=False
                )
                self.offline_available = True
                print("Offline LLM loaded successfully")
            else:
                print(f"Warning: Offline LLM model not found at {self.config.OFFLINE_LLM_PATH}")
        except Exception as e:
            print(f"Warning: Could not load offline LLM: {e}")
            print("Will use online LLM only")
        
        # Online LLM settings
        self.online_providers = {
            'gemini': self.query_gemini,
            'perplexity': self.query_perplexity,
            'deepseek': self.query_deepseek
        }
    
    def run(self):
        """Run LLM processing in a separate thread"""
        self.running = True
        
        print("LLM processor started.")
        while self.running:
            # This would typically process from an input queue
            # For now, we'll just wait for calls
            time.sleep(0.1)
    
    def process_query(self, query, context, use_online=True):
        """Process a query with LLM"""
        if use_online and self.config.ONLINE_LLM_API_KEY:
            try:
                return self.query_online(query, context)
            except Exception as e:
                print(f"Online LLM failed: {e}. Falling back to offline.")
        
        # Use offline LLM
        return self.query_offline(query, context)
    
    def query_offline(self, query, context):
        """Query offline LLM"""
        if not self.offline_available or not self.offline_llm:
            raise Exception("Offline LLM not available")
        
        try:
            prompt = self.build_prompt(query, context)
            
            response = self.offline_llm(
                prompt,
                max_tokens=150,
                temperature=0.7,
                top_p=0.9,
                echo=False,
                stop=["Human:", "AI:"]
            )
            
            return response['choices'][0]['text'].strip()
        except Exception as e:
            print(f"Error querying offline LLM: {e}")
            raise
    
    def query_online(self, query, context):
        """Query online LLM"""
        provider = self.config.ONLINE_LLM_PROVIDER
        if provider in self.online_providers:
            return self.online_providers[provider](query, context)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def query_gemini(self, query, context):
        """Query Gemini API"""
        # Implement Gemini API call
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={self.config.ONLINE_LLM_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": self.build_prompt(query, context)
                }]
            }]
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    
    def query_perplexity(self, query, context):
        """Query Perplexity API"""
        # Implement Perplexity API call
        pass
    
    def query_deepseek(self, query, context):
        """Query DeepSeek API"""
        # Implement DeepSeek API call
        pass
    
    def build_prompt(self, query, context):
        """Build prompt for LLM"""
        prompt = f"""You are a helpful humanoid robot assistant. Here is your current context:
- Time: {context.get('time', 'unknown')}
- Location: {context.get('location', 'unknown')}
- People present: {', '.join(context.get('people_present', [])) or 'None'}
- Battery level: {context.get('battery_level', 'unknown')}

Human: {query}
AI: """
        
        return prompt
    
    def stop(self):
        """Stop LLM processing"""
        self.running = False