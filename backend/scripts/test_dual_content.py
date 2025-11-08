"""Test script for dual content generation with de-duplication."""
import asyncio
import os
from collections import Counter
from typing import List, Set
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from google.generativeai import GenerativeModel

from app.services.slides.dual_content import DualContentGenerator
from app.services.slides.text_utils import normalize_sentence

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
STOPWORDS = set(stopwords.words('english'))

def jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts, ignoring stopwords."""
    # Tokenize and filter stopwords
    tokens1 = set(word_tokenize(text1.lower())) - STOPWORDS
    tokens2 = set(word_tokenize(text2.lower())) - STOPWORDS
    
    # Calculate Jaccard similarity
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    return intersection / union if union > 0 else 0.0

def validate_content(
    narrative: str,
    key_concepts: List[str],
    supporting_details: List[str]
) -> None:
    """Validate that the generated content meets our requirements."""
    # Split narrative into sentences
    narrative_sentences = set(
        normalize_sentence(s.strip())
        for s in narrative.split('.')
        if s.strip()
    )
    
    # Check key concepts don't duplicate narrative
    for concept in key_concepts:
        concept_norm = normalize_sentence(concept)
        assert all(
            concept_norm != sent 
            for sent in narrative_sentences
        ), f"Key concept duplicates narrative: {concept}"
        
        # Check length
        assert len(concept) <= 160, f"Key concept too long: {concept}"
    
    # Check supporting details don't duplicate others
    seen_details: Set[str] = set()
    for detail in supporting_details:
        detail_norm = normalize_sentence(detail)
        
        # Check against narrative
        assert all(
            detail_norm != sent
            for sent in narrative_sentences
        ), f"Supporting detail duplicates narrative: {detail}"
        
        # Check against concepts
        assert all(
            jaccard_similarity(detail, concept) < 0.8
            for concept in key_concepts
        ), f"Supporting detail too similar to concept: {detail}"
        
        # Check against previous details
        assert detail_norm not in seen_details, f"Duplicate supporting detail: {detail}"
        seen_details.add(detail_norm)
        
        # Check length
        assert len(detail) <= 160, f"Supporting detail too long: {detail}"

async def main():
    """Run test cases for dual content generation."""
    # Test case
    topic = "Binary Trees — Core Ideas"
    title = "What Is a Binary Tree?"
    points = [
        "A binary tree is a hierarchical data structure",
        "Each node has at most two children: left and right",
        "Used for efficient searching and sorting",
        "Foundation for binary search trees and heaps"
    ]
    
    # Initialize generator
    model = GenerativeModel("gemini-pro")
    generator = DualContentGenerator(model, level="detailed")
    
    print(f"\nGenerating content for: {title}")
    print("-" * 50)
    
    # Generate content
    result = await generator.generate_dual_content(
        topic=topic,
        title=title,
        points=points
    )
    
    # Print sections
    print("\nExpanded Content:")
    print(result["expanded_content"])
    
    print("\nKey Concepts:")
    for concept in result["key_concepts"]:
        print(f"- {concept}")
    
    print("\nSupporting Details:")
    for detail in result["supporting_details"]:
        print(f"- {detail}")
        
    print("\nValidating content...")
    validate_content(
        result["expanded_content"],
        result["key_concepts"],
        result["supporting_details"]
    )
    print("All validation checks passed!")

if __name__ == "__main__":
    asyncio.run(main())