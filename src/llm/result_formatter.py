from typing import Dict, Any, List
import json
import time
from datetime import datetime


class ResultFormatter:
    """Formats search results for better presentation"""
    
    @staticmethod
    def format_console_output(result: Dict[str, Any]) -> str:
        """Format results for console output with rich formatting"""
        output = []
        
        # Header
        output.append("\n" + "="*80)
        output.append("🎯 CU BOULDER SEARCH RESULTS")
        output.append("="*80)
        
        # Query info
        metadata = result.get('metadata', {})
        output.append(f"\n🔍 Query: {metadata.get('query', 'Unknown')}")
        output.append(f"⏱️  Processed in {metadata.get('total_time', 0):.2f}s")
        
        # Answer
        answer = result.get('answer', 'No answer available')
        output.append(f"\n📝 ANSWER:")
        output.append("-" * 40)
        output.append(answer)
        
        # Sources
        sources = result.get('sources', [])
        if sources:
            output.append(f"\n\n🔗 SOURCES ({len(sources)}):")
            output.append("-" * 40)
            
            for source in sources:
                source_id = source.get('id', '?')
                title = source.get('title', 'Untitled')
                url = source.get('url', 'Unknown URL')
                snippet = source.get('snippet', '')
                
                output.append(f"\n[{source_id}] 📄 {title}")
                output.append(f"    🔗 {url}")
                if snippet:
                    output.append(f"    💡 {snippet}")
        
        # Footer with metadata
        output.append(f"\n📊 METADATA:")
        output.append(f"    • Documents retrieved: {metadata.get('total_docs', 0)}")
        output.append(f"    • Context length: {metadata.get('context_length', 0)} chars")
        output.append(f"    • Retrieval time: {metadata.get('retrieval_time', 0):.2f}s")
        output.append(f"    • Generation time: {metadata.get('generation_time', 0):.2f}s")
        
        output.append("\n" + "="*80)
        
        return "\n".join(output)
    
    @staticmethod
    def format_markdown(result: Dict[str, Any]) -> str:
        """Format results as Markdown"""
        output = []
        
        # Title and query
        metadata = result.get('metadata', {})
        query = metadata.get('query', 'Unknown')
        output.append(f"# CU Boulder Search Results")
        output.append(f"**Query:** {query}")
        output.append(f"**Processed in:** {metadata.get('total_time', 0):.2f}s")
        output.append("")
        
        # Answer
        answer = result.get('answer', 'No answer available')
        output.append("## Answer")
        output.append(answer)
        output.append("")
        
        # Sources
        sources = result.get('sources', [])
        if sources:
            output.append(f"## Sources ({len(sources)})")
            output.append("")
            
            for source in sources:
                source_id = source.get('id', '?')
                title = source.get('title', 'Untitled')
                url = source.get('url', 'Unknown URL')
                snippet = source.get('snippet', '')
                
                output.append(f"### [{source_id}] {title}")
                output.append(f"**URL:** {url}")
                if snippet:
                    output.append(f"**Snippet:** {snippet}")
                output.append("")
        
        # Metadata
        output.append("## Metadata")
        output.append(f"- **Documents retrieved:** {metadata.get('total_docs', 0)}")
        output.append(f"- **Context length:** {metadata.get('context_length', 0)} characters")
        output.append(f"- **Retrieval time:** {metadata.get('retrieval_time', 0):.2f}s")
        output.append(f"- **Generation time:** {metadata.get('generation_time', 0):.2f}s")
        output.append(f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_html(result: Dict[str, Any]) -> str:
        """Format results as HTML for web display"""
        metadata = result.get('metadata', {})
        answer = result.get('answer', 'No answer available')
        sources = result.get('sources', [])
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CU Boulder Search Results</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ border-bottom: 2px solid #cf4446; padding-bottom: 20px; margin-bottom: 30px; }}
        .query {{ font-size: 24px; color: #333; margin-bottom: 10px; }}
        .meta {{ color: #666; font-size: 14px; }}
        .answer {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; white-space: pre-wrap; }}
        .sources {{ margin-bottom: 20px; }}
        .source {{ border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 15px; background: #fafafa; }}
        .source-title {{ font-weight: bold; color: #333; margin-bottom: 5px; }}
        .source-url {{ color: #007bff; text-decoration: none; font-size: 14px; margin-bottom: 10px; display: block; }}
        .source-snippet {{ color: #555; font-size: 14px; font-style: italic; }}
        .footer {{ border-top: 1px solid #e0e0e0; padding-top: 20px; margin-top: 30px; font-size: 12px; color: #666; }}
        .badge {{ background: #cf4446; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-right: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="query">🔍 {metadata.get('query', 'Unknown')}</div>
            <div class="meta">
                <span class="badge">⏱️ {metadata.get('total_time', 0):.2f}s</span>
                <span class="badge">📄 {metadata.get('total_docs', 0)} sources</span>
                <span>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
            </div>
        </div>
        
        <div class="answer">
            <h3>📝 Answer</h3>
            {answer.replace('\n', '<br>')}
        </div>
        
        <div class="sources">
            <h3>🔗 Sources ({len(sources)})</h3>
            """
        
        for source in sources:
            source_id = source.get('id', '?')
            title = source.get('title', 'Untitled').replace('<', '&lt;').replace('>', '&gt;')
            url = source.get('url', 'Unknown URL')
            snippet = source.get('snippet', '').replace('<', '&lt;').replace('>', '&gt;')
            
            html += f"""
            <div class="source">
                <div class="source-title">[{source_id}] {title}</div>
                <a href="{url}" class="source-url" target="_blank">{url}</a>
                <div class="source-snippet">{snippet}</div>
            </div>
            """
        
        html += f"""
        </div>
        
        <div class="footer">
            <strong>Performance:</strong> 
            Retrieval: {metadata.get('retrieval_time', 0):.2f}s | 
            Generation: {metadata.get('generation_time', 0):.2f}s | 
            Context: {metadata.get('context_length', 0)} chars
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    @staticmethod
    def save_results(result: Dict[str, Any], filename: str = None, format_type: str = "json"):
        """
        Save results to file in specified format
        
        Args:
            result: Search result dictionary
            filename: Output filename (auto-generated if None)
            format_type: Output format - "json", "markdown", "html"
        """
        if filename is None:
            timestamp = int(time.time())
            extensions = {
                "json": "json",
                "markdown": "md", 
                "html": "html"
            }
            ext = extensions.get(format_type, "json")
            filename = f"search_result_{timestamp}.{ext}"
        
        try:
            if format_type == "json":
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            
            elif format_type == "markdown":
                content = ResultFormatter.format_markdown(result)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            elif format_type == "html":
                content = ResultFormatter.format_html(result)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            return filename
            
        except Exception as e:
            raise Exception(f"Failed to save results: {e}")
    
    @staticmethod
    def print_summary(result: Dict[str, Any]):
        """Print a brief summary of the search results"""
        metadata = result.get('metadata', {})
        sources = result.get('sources', [])
        
        print(f"\n🎯 Search Summary:")
        print(f"   Query: {metadata.get('query', 'Unknown')}")
        print(f"   Time: {metadata.get('total_time', 0):.2f}s")
        print(f"   Sources: {len(sources)}")
        print(f"   Context: {metadata.get('context_length', 0)} chars")
        
        # Show top 3 sources
        if sources:
            print(f"\n🔗 Top Sources:")
            for i, source in enumerate(sources[:3], 1):
                title = source.get('title', 'Untitled')[:60]
                if len(source.get('title', '')) > 60:
                    title += "..."
                print(f"   {i}. {title}")
                print(f"      {source.get('url', 'Unknown URL')}")
        
        # Answer preview
        answer = result.get('answer', '')
        if answer:
            preview = answer[:200] + "..." if len(answer) > 200 else answer
            print(f"\n📝 Answer Preview:")
            print(f"   {preview}")


class SearchSession:
    """Manages a search session with history and result management"""
    
    def __init__(self):
        self.history = []
        self.session_start = datetime.now()
    
    def add_result(self, result: Dict[str, Any]):
        """Add a search result to the session history"""
        result['session_timestamp'] = datetime.now().isoformat()
        self.history.append(result)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for the current session"""
        if not self.history:
            return {"queries": 0, "total_time": 0, "avg_time": 0}
        
        total_queries = len(self.history)
        total_time = sum(r.get('metadata', {}).get('total_time', 0) for r in self.history)
        avg_time = total_time / total_queries if total_queries > 0 else 0
        
        return {
            "session_start": self.session_start.isoformat(),
            "queries": total_queries,
            "total_time": total_time,
            "avg_time": avg_time,
            "total_sources": sum(len(r.get('sources', [])) for r in self.history)
        }
    
    def save_session(self, filename: str = None):
        """Save entire session to JSON file"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"search_session_{timestamp}.json"
        
        session_data = {
            "session_stats": self.get_session_stats(),
            "history": self.history
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return filename
