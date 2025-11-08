# backend/app/services/quiz_service.py
"""
Quiz Generation Service
Generates multiple-choice quiz questions based on lecture content using Gemini AI
"""

import google.generativeai as genai
from typing import List, Dict
import json
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_quiz_questions(
    topic: str,
    slides: List[Dict],
    audience: str = "High School",
    num_questions: int = 3
) -> List[Dict]:
    """
    Generate quiz questions based on lecture content
    
    Args:
        topic: Main topic of the lecture
        slides: List of slide dictionaries with titles and points
        audience: Target audience level
        num_questions: Number of questions to generate (default 3)
    
    Returns:
        List of quiz question dictionaries
    """
    
    # Extract key points from slides
    content_summary = f"Topic: {topic}\n\n"
    for slide in slides:
        content_summary += f"Slide {slide.get('index', 0)}: {slide.get('title', '')}\n"
        for point in slide.get('points', []):
            content_summary += f"  • {point}\n"
        content_summary += "\n"
    
    prompt = f"""
You are an expert educational assessment designer.
Generate {num_questions} multiple-choice quiz questions based on this lecture content.

Target Audience: {audience}

Lecture Content:
{content_summary}

Requirements:
1. Questions should test understanding of KEY CONCEPTS from the lecture
2. Each question MUST have EXACTLY 4 options
3. Only ONE option should be correct
4. Include brief explanations for the correct answer
5. Difficulty should match the {audience} level
6. Questions should cover different slides/topics
7. Make questions practical and application-based when possible

Return ONLY valid JSON in this EXACT format (no markdown, no code blocks):
{{
  "questions": [
    {{
      "question": "What is the main purpose of...",
      "options": [
        "First option text",
        "Second option text",
        "Third option text",
        "Fourth option text"
      ],
      "correctAnswer": 1,
      "explanation": "The correct answer is option B because..."
    }}
  ]
}}

CRITICAL: 
- correctAnswer must be the INDEX (0-3) of the correct option in the options array
- Return exactly {num_questions} questions
- Ensure valid JSON format

Generate the quiz now:
"""
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2500,
                response_mime_type="application/json"
            )
        )
        
        # Extract text from response
        if hasattr(response, "text") and response.text:
            response_text = response.text.strip()
        elif getattr(response, "candidates", None):
            response_text = response.candidates[0].content.parts[0].text.strip()
        else:
            raise ValueError("No valid text output from Gemini")
        
        # Remove markdown code blocks if present
        if response_text.startswith("json"):
            response_text = response_text[7:]
        if response_text.startswith(""):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        quiz_data = json.loads(response_text.strip())
        
        # Validate structure
        if "questions" not in quiz_data:
            raise ValueError("Invalid quiz format: missing 'questions' key")
        
        questions = quiz_data["questions"]
        
        # Validate each question
        validated_questions = []
        for q in questions:
            if not all(key in q for key in ["question", "options", "correctAnswer"]):
                continue
            if len(q["options"]) != 4:
                continue
            if not isinstance(q["correctAnswer"], int) or q["correctAnswer"] < 0 or q["correctAnswer"] > 3:
                continue
            validated_questions.append(q)
        
        if len(validated_questions) < num_questions:
            print(f"[QUIZ] Warning: Only {len(validated_questions)}/{num_questions} valid questions generated")
        
        print(f"[QUIZ] ✅ Generated {len(validated_questions)} valid questions")
        return validated_questions[:num_questions]
        
    except json.JSONDecodeError as e:
        print(f"[QUIZ] ❌ JSON parsing error: {e}")
        print(f"[QUIZ] Response text: {response_text[:300]}...")
        return generate_fallback_questions(topic, num_questions)
    except Exception as e:
        print(f"[QUIZ] ❌ Error generating quiz: {e}")
        import traceback
        traceback.print_exc()
        return generate_fallback_questions(topic, num_questions)


def generate_fallback_questions(topic: str, num_questions: int = 3) -> List[Dict]:
    """Generate basic fallback questions if AI generation fails"""
    fallback = [
        {
            "question": f"What is the main concept covered in the {topic} lecture?",
            "options": [
                f"Basic principles of {topic}",
                "Unrelated mathematical concepts",
                "Historical events only",
                "Abstract philosophical theories"
            ],
            "correctAnswer": 0,
            "explanation": f"The lecture primarily covers the basic principles and fundamentals of {topic}."
        },
        {
            "question": f"Which of the following is most likely discussed in a {topic} lecture?",
            "options": [
                "Random unrelated content",
                f"Key applications of {topic}",
                "Ancient mythology",
                "Cooking techniques"
            ],
            "correctAnswer": 1,
            "explanation": f"A {topic} lecture would focus on practical applications and real-world uses."
        },
        {
            "question": f"Why is understanding {topic} important?",
            "options": [
                "It has no practical applications",
                "It only matters for academic research",
                "It helps explain real-world phenomena and solve problems",
                "It's completely obsolete"
            ],
            "correctAnswer": 2,
            "explanation": f"Understanding {topic} is crucial for explaining real-world situations and solving practical problems."
        }
    ]
    return fallback[:num_questions]


def format_quiz_for_lms(questions: List[Dict], format_type: str = "plain", topic: str = "") -> str:
    """
    Format quiz questions for various LMS platforms
    
    Args:
        questions: List of question dictionaries
        format_type: 'plain', 'moodle', 'canvas', 'blackboard'
        topic: Lecture topic for context
    
    Returns:
        Formatted string ready to paste into LMS
    """
    
    if format_type == "plain":
        output = f"QUIZ: {topic}\n" + "=" * 60 + "\n\n"
        for i, q in enumerate(questions, 1):
            output += f"Question {i}:\n{q['question']}\n\n"
            for j, option in enumerate(q['options']):
                letter = chr(65 + j)  # A, B, C, D
                marker = "✓" if j == q['correctAnswer'] else " "
                output += f"  [{marker}] {letter}. {option}\n"
            output += f"\nCorrect Answer: {chr(65 + q['correctAnswer'])}\n"
            output += f"Explanation: {q.get('explanation', 'No explanation provided.')}\n"
            output += "\n" + "-" * 60 + "\n\n"
        return output
    
    elif format_type == "moodle":
        # Moodle GIFT format
        output = f"// Moodle GIFT Format - {topic}\n\n"
        for q in questions:
            output += f"::{q['question'][:50]}::{q['question']}{{\n"
            for j, option in enumerate(q['options']):
                if j == q['correctAnswer']:
                    output += f"={option}\n"
                else:
                    output += f"~{option}\n"
            output += f"####Explanation: {q.get('explanation', '')}\n}}\n\n"
        return output
    
    elif format_type == "canvas":
        # Canvas quiz format (CSV-like)
        output = "Question,Option A,Option B,Option C,Option D,Correct Answer,Explanation\n"
        for q in questions:
            options = q['options']
            row = [
                q['question'],
                options[0] if len(options) > 0 else "",
                options[1] if len(options) > 1 else "",
                options[2] if len(options) > 2 else "",
                options[3] if len(options) > 3 else "",
                chr(65 + q['correctAnswer']),
                q.get('explanation', '')
            ]
            output += ','.join([f'"{item}"' for item in row]) + "\n"
        return output
    
    else:
        return format_quiz_for_lms(questions, "plain", topic)