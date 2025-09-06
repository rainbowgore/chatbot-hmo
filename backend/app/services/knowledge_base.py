import os
import re
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup
from dataclasses import dataclass
import tiktoken

@dataclass
class KnowledgeChunk:
    """Represents a chunk of knowledge base content"""
    content: str
    source_file: str
    service_type: str
    chunk_id: str
    hmos: List[str]  # Which HMOs this content applies to
    tiers: List[str]  # Which membership tiers this applies to

class KnowledgeBaseService:
    def __init__(self, data_directory: str = None):
        if data_directory is None:
            # Get absolute path to phase2_data directory
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            data_directory = os.path.join(current_dir, "phase2_data")
        self.data_directory = data_directory
        self.chunks: List[KnowledgeChunk] = []
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        
    def load_knowledge_base(self) -> None:
        """Load and parse all HTML files in the knowledge base"""
        html_files = [
            "alternative_services.html",
            "communication_clinic_services.html", 
            "dentel_services.html",
            "optometry_services.html",
            "pragrency_services.html",
            "workshops_services.html"
        ]
        
        for file_name in html_files:
            file_path = os.path.join(self.data_directory, file_name)
            if os.path.exists(file_path):
                self._parse_html_file(file_path, file_name)
                
    def _parse_html_file(self, file_path: str, file_name: str) -> None:
        """Parse a single HTML file and extract content chunks"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract service type from filename
            service_type = self._extract_service_type(file_name)
            
            # Parse different sections
            self._parse_header_content(soup, file_name, service_type)
            self._parse_table_content(soup, file_name, service_type)
            self._parse_contact_info(soup, file_name, service_type)
            
        except Exception as e:
            print(f"Error parsing {file_name}: {e}")
            
    def _extract_service_type(self, file_name: str) -> str:
        """Extract service type from filename"""
        service_mapping = {
            "alternative_services.html": "רפואה משלימה",
            "communication_clinic_services.html": "מרפאות תקשורת", 
            "dentel_services.html": "מרפאות שיניים",
            "optometry_services.html": "אופטומטריה",
            "pragrency_services.html": "הריון",
            "workshops_services.html": "סדנאות בריאות"
        }
        return service_mapping.get(file_name, "שירותים כלליים")
        
    def _parse_header_content(self, soup: BeautifulSoup, file_name: str, service_type: str) -> None:
        """Parse header content (title, description, service lists)"""
        # Get main title
        title = soup.find('h2')
        if title:
            title_text = title.get_text().strip()
            
        # Get description paragraphs
        paragraphs = soup.find_all('p')
        description_parts = []
        
        for p in paragraphs:
            text = p.get_text().strip()
            if text and not text.startswith('הטבלה'):
                description_parts.append(text)
                
        # Get service lists
        service_lists = soup.find_all('ul')
        for ul in service_lists:
            if ul.find_parent('table'):  # Skip lists inside tables
                continue
                
            services = []
            for li in ul.find_all('li'):
                service_text = li.get_text().strip()
                if service_text:
                    services.append(service_text)
                    
            if services:
                services_text = "\n".join([f"• {service}" for service in services])
                description_parts.append(f"השירותים כוללים:\n{services_text}")
        
        # Combine all header content
        if description_parts:
            header_content = f"{service_type}\n\n" + "\n\n".join(description_parts)
            
            chunk = KnowledgeChunk(
                content=header_content,
                source_file=file_name,
                service_type=service_type,
                chunk_id=f"{file_name}_header",
                hmos=["מכבי", "מאוחדת", "כללית"],
                tiers=["זהב", "כסף", "ארד"]
            )
            self.chunks.append(chunk)
            
    def _parse_table_content(self, soup: BeautifulSoup, file_name: str, service_type: str) -> None:
        """Parse table content and create chunks for each service"""
        table = soup.find('table')
        if not table:
            return
            
        # Get table headers
        headers = []
        header_row = table.find('tr')
        if header_row:
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text().strip())
                
        # Process each service row
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            if len(cells) < 4:  # Should have service name + 3 HMOs
                continue
                
            service_name = cells[0].get_text().strip()
            
            # Create chunks for each HMO
            hmo_names = ["מכבי", "מאוחדת", "כללית"]
            
            for j, hmo_name in enumerate(hmo_names):
                if j + 1 < len(cells):
                    hmo_details = cells[j + 1].get_text().strip()
                    
                    # Extract tier information
                    tier_info = self._extract_tier_info(hmo_details)
                    
                    chunk_content = f"{service_type} - {service_name}\n\n"
                    chunk_content += f"קופת חולים: {hmo_name}\n\n"
                    chunk_content += hmo_details
                    
                    chunk = KnowledgeChunk(
                        content=chunk_content,
                        source_file=file_name,
                        service_type=service_type,
                        chunk_id=f"{file_name}_{service_name}_{hmo_name}_{i}",
                        hmos=[hmo_name],
                        tiers=tier_info
                    )
                    self.chunks.append(chunk)
                    
    def _extract_tier_info(self, hmo_details: str) -> List[str]:
        """Extract which membership tiers are mentioned in the details"""
        tiers = []
        if "זהב" in hmo_details:
            tiers.append("זהב")
        if "כסף" in hmo_details:
            tiers.append("כסף")
        if "ארד" in hmo_details:
            tiers.append("ארד")
        return tiers if tiers else ["זהב", "כסף", "ארד"]
        
    def _parse_contact_info(self, soup: BeautifulSoup, file_name: str, service_type: str) -> None:
        """Parse contact information sections"""
        # Find contact sections
        contact_sections = []
        
        # Look for h3 headers that indicate contact info
        h3_tags = soup.find_all('h3')
        for h3 in h3_tags:
            if any(keyword in h3.get_text() for keyword in ['טלפון', 'פרטים', 'מידע']):
                # Get the following ul element
                next_ul = h3.find_next_sibling('ul')
                if next_ul:
                    contact_info = []
                    for li in next_ul.find_all('li'):
                        contact_text = li.get_text().strip()
                        contact_info.append(contact_text)
                    
                    if contact_info:
                        section_title = h3.get_text().strip()
                        section_content = f"{section_title}\n\n" + "\n".join(contact_info)
                        contact_sections.append(section_content)
        
        # Create contact info chunk
        if contact_sections:
            contact_content = f"{service_type} - מידע ליצירת קשר\n\n" + "\n\n".join(contact_sections)
            
            chunk = KnowledgeChunk(
                content=contact_content,
                source_file=file_name,
                service_type=service_type,
                chunk_id=f"{file_name}_contact",
                hmos=["מכבי", "מאוחדת", "כללית"],
                tiers=["זהב", "כסף", "ארד"]
            )
            self.chunks.append(chunk)
            
    def chunk_text(self, text: str, max_tokens: int = 400) -> List[str]:
        """Split text into chunks of max_tokens size"""
        tokens = self.encoding.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            
        return chunks
        
    def get_chunks_for_user(self, user_hmo: str = None, user_tier: str = None) -> List[KnowledgeChunk]:
        """Filter chunks relevant to a specific user"""
        if not user_hmo and not user_tier:
            return self.chunks
            
        filtered_chunks = []
        for chunk in self.chunks:
            # Check HMO match
            hmo_match = not user_hmo or user_hmo in chunk.hmos
            
            # Check tier match  
            tier_match = not user_tier or user_tier in chunk.tiers
            
            if hmo_match and tier_match:
                filtered_chunks.append(chunk)
                
        return filtered_chunks
        
    def get_chunk_count(self) -> int:
        """Get total number of chunks"""
        return len(self.chunks)
        
    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics of the knowledge base"""
        summary = {
            "total_chunks": len(self.chunks),
            "by_service": {},
            "by_hmo": {"מכבי": 0, "מאוחדת": 0, "כללית": 0},
            "by_tier": {"זהב": 0, "כסף": 0, "ארד": 0}
        }
        
        for chunk in self.chunks:
            # Count by service type
            service = chunk.service_type
            summary["by_service"][service] = summary["by_service"].get(service, 0) + 1
            
            # Count by HMO
            for hmo in chunk.hmos:
                if hmo in summary["by_hmo"]:
                    summary["by_hmo"][hmo] += 1
                    
            # Count by tier
            for tier in chunk.tiers:
                if tier in summary["by_tier"]:
                    summary["by_tier"][tier] += 1
                    
        return summary
