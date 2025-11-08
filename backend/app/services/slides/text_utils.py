"""Text utilities for processing and de-duplicating content."""
import re
import string
from typing import Set, List
from difflib import SequenceMatcher

def normalize_sentence(s: str) -> str:
    """
    Normalize a sentence for comparison by lowercasing, trimming, and removing punctuation.
    
    Args:
        s: The sentence to normalize
        
    Returns:
        Normalized sentence string
    """
    # Convert to lowercase and strip whitespace
    s = s.lower().strip()
    
    # Remove punctuation except hyphens and apostrophes in words
    s = re.sub(f'[{re.escape(string.punctuation.replace("-", "").replace("'", ""))}]', '', s)
    
    # Normalize spaces
    s = re.sub(r'\s+', ' ', s)
    
    return s

def is_near_duplicate(a: str, b: str, threshold: float = 0.9) -> bool:
    """
    Check if two strings are near-duplicates using sequence matching.
    
    Args:
        a: First string
        b: Second string
        threshold: Similarity threshold (0-1, default 0.9)
        
    Returns:
        True if strings are similar enough to be considered duplicates
    """
    # Normalize both strings first
    a_norm = normalize_sentence(a)
    b_norm = normalize_sentence(b)
    
    # Use sequence matcher to compute similarity
    matcher = SequenceMatcher(None, a_norm, b_norm)
    ratio = matcher.ratio()
    
    return ratio >= threshold

def deduplicate_content(
    narrative: str,
    key_concepts: List[str],
    supporting_details: List[str],
) -> tuple[str, List[str], List[str]]:
    """
    Remove duplicates across sections while preserving structure.
    
    Args:
        narrative: Main content text
        key_concepts: List of key concepts
        supporting_details: List of supporting details
        
    Returns:
        Tuple of (filtered_narrative, filtered_concepts, filtered_details)
    """
    # Build set of normalized narrative sentences
    seen_sentences: Set[str] = set()
    
    # Split narrative into sentences and normalize each
    for sentence in re.split(r'[.!?]+', narrative):
        if sentence.strip():
            seen_sentences.add(normalize_sentence(sentence))
    
    # Filter key concepts
    filtered_concepts = []
    for concept in key_concepts:
        normalized = normalize_sentence(concept)
        is_duplicate = False
        
        # Check against narrative sentences
        for seen in seen_sentences:
            if is_near_duplicate(normalized, seen):
                is_duplicate = True
                break
                
        if not is_duplicate and len(concept) <= 160:
            filtered_concepts.append(concept)
            seen_sentences.add(normalized)
    
    # Ensure we have minimum required concepts
    filtered_concepts = filtered_concepts[:6]  # Max 6
    if len(filtered_concepts) < 3:
        # We should regenerate concepts, but for now keep originals
        filtered_concepts.extend(
            concept for concept in key_concepts 
            if concept not in filtered_concepts
        )[:3]
    
    # Filter supporting details
    filtered_details = []
    for detail in supporting_details:
        normalized = normalize_sentence(detail)
        is_duplicate = False
        
        # Check against all previous content
        for seen in seen_sentences:
            if is_near_duplicate(normalized, seen):
                is_duplicate = True
                break
                
        if not is_duplicate and len(detail) <= 160:
            filtered_details.append(detail)
            seen_sentences.add(normalized)
    
    # Ensure minimum required details
    filtered_details = filtered_details[:6]  # Max 6
    if len(filtered_details) < 3:
        # We should regenerate details, but for now keep originals
        filtered_details.extend(
            detail for detail in supporting_details 
            if detail not in filtered_details
        )[:3]
    
    return narrative, filtered_concepts, filtered_details