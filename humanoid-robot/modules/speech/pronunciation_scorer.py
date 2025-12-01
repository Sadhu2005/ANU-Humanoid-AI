"""
Pronunciation Scoring Module for ANU 6.0
Implements phoneme-level pronunciation scoring and feedback generation
Based on the methodology from the project presentation
"""

import numpy as np
from typing import List, Dict, Tuple
import json

class PronunciationScorer:
    """Scores pronunciation accuracy and provides corrective feedback"""
    
    def __init__(self):
        """Initialize pronunciation scorer"""
        self.phoneme_map = self._load_phoneme_map()
        self.error_threshold = 0.3  # Threshold for pronunciation errors
    
    def _load_phoneme_map(self) -> Dict:
        """Load phoneme mapping for English"""
        # Basic English phoneme set (IPA)
        return {
            'vowels': ['i', 'ɪ', 'e', 'ɛ', 'æ', 'ɑ', 'ɔ', 'o', 'ʊ', 'u', 'ʌ', 'ə', 'ɚ', 'aɪ', 'aʊ', 'ɔɪ'],
            'consonants': ['p', 'b', 't', 'd', 'k', 'g', 'f', 'v', 'θ', 'ð', 's', 'z', 'ʃ', 'ʒ', 'h', 'm', 'n', 'ŋ', 'l', 'r', 'w', 'j', 'tʃ', 'dʒ'],
            'common_errors': {
                'θ': 'th',  # 'think' - common error for Indian English speakers
                'ð': 'th',  # 'this'
                'r': 'r',   # Rolled vs non-rolled
                'v': 'w',   # Common substitution
                'w': 'v'    # Common substitution
            }
        }
    
    def calculate_pronunciation_score(self, 
                                     student_phonemes: List[str],
                                     target_phonemes: List[str],
                                     alignment: List[Tuple[int, int]]) -> Dict:
        """
        Calculate pronunciation score using Phoneme Error Rate (PER)
        
        Args:
            student_phonemes: Phonemes from student's speech
            target_phonemes: Target/correct phonemes
            alignment: Alignment between student and target phonemes
        
        Returns:
            Dictionary with score, errors, and feedback
        """
        if not target_phonemes:
            return {
                'score': 0.0,
                'errors': [],
                'feedback': 'No target phonemes provided'
            }
        
        # Calculate substitutions, insertions, deletions
        substitutions = 0
        insertions = 0
        deletions = 0
        errors = []
        
        # Use alignment to find errors
        target_idx = 0
        student_idx = 0
        
        for target_pos, student_pos in alignment:
            if target_pos < len(target_phonemes) and student_pos < len(student_phonemes):
                target_phoneme = target_phonemes[target_pos]
                student_phoneme = student_phonemes[student_pos]
                
                if target_phoneme != student_phoneme:
                    substitutions += 1
                    errors.append({
                        'type': 'substitution',
                        'position': target_pos,
                        'target': target_phoneme,
                        'student': student_phoneme,
                        'hint': self._generate_hint(target_phoneme, student_phoneme)
                    })
            
            target_idx += 1
            student_idx += 1
        
        # Count deletions (target phonemes not matched)
        if len(target_phonemes) > len(alignment):
            for i in range(len(alignment), len(target_phonemes)):
                deletions += 1
                errors.append({
                    'type': 'deletion',
                    'position': i,
                    'target': target_phonemes[i],
                    'hint': f"Missing sound: {self._get_phoneme_description(target_phonemes[i])}"
                })
        
        # Count insertions (student phonemes not matched)
        if len(student_phonemes) > len(alignment):
            for i in range(len(alignment), len(student_phonemes)):
                insertions += 1
        
        # Calculate PER (Phoneme Error Rate)
        total_errors = substitutions + insertions + deletions
        total_phonemes = len(target_phonemes)
        per = total_errors / total_phonemes if total_phonemes > 0 else 1.0
        
        # Convert PER to score (0-100, where 100 is perfect)
        score = max(0, (1.0 - per) * 100)
        
        return {
            'score': round(score, 2),
            'per': round(per, 3),
            'substitutions': substitutions,
            'insertions': insertions,
            'deletions': deletions,
            'errors': errors,
            'feedback': self._generate_feedback(score, errors)
        }
    
    def _generate_hint(self, target_phoneme: str, student_phoneme: str) -> str:
        """Generate helpful hint for pronunciation correction"""
        hints = {
            'θ': "Try saying 'th' as in 'think' - place tongue between teeth",
            'ð': "Try saying 'th' as in 'this' - place tongue between teeth, voice it",
            'r': "Roll your 'r' sound - curl tongue back",
            'v': "Make 'v' sound by touching lower lip to upper teeth",
            'w': "Make 'w' sound by rounding lips like saying 'oo'",
            'ʃ': "Make 'sh' sound - spread lips, tongue up",
            'ʒ': "Make 'zh' sound like in 'measure'",
            'tʃ': "Make 'ch' sound - tongue touches roof of mouth",
            'dʒ': "Make 'j' sound like in 'judge'"
        }
        
        if target_phoneme in hints:
            return hints[target_phoneme]
        
        # Generic hint
        return f"Try to pronounce '{target_phoneme}' more clearly. Listen and repeat."
    
    def _get_phoneme_description(self, phoneme: str) -> str:
        """Get human-readable description of phoneme"""
        descriptions = {
            'θ': "th (think)",
            'ð': "th (this)",
            'ʃ': "sh",
            'ʒ': "zh",
            'tʃ': "ch",
            'dʒ': "j"
        }
        return descriptions.get(phoneme, phoneme)
    
    def _generate_feedback(self, score: float, errors: List[Dict]) -> str:
        """Generate overall feedback message"""
        if score >= 90:
            return "Excellent pronunciation! Keep practicing!"
        elif score >= 75:
            return f"Good pronunciation! You scored {score:.1f}%. Focus on the highlighted sounds."
        elif score >= 60:
            return f"Fair pronunciation. Score: {score:.1f}%. Practice the corrections below."
        else:
            return f"Needs improvement. Score: {score:.1f}%. Review the hints and try again."
    
    def extract_phonemes(self, text: str) -> List[str]:
        """
        Extract phonemes from text (simplified version)
        In production, use a proper phonemizer like espeak or phonemizer library
        """
        # This is a simplified version
        # For production, use: from phonemizer import phonemize
        # phonemes = phonemize(text, language='en', backend='espeak')
        
        # Placeholder: return basic phoneme representation
        # In real implementation, use espeak or similar
        return text.lower().split()  # Simplified - should be actual phonemes
    
    def align_phonemes(self, 
                      student_phonemes: List[str],
                      target_phonemes: List[str]) -> List[Tuple[int, int]]:
        """
        Align student phonemes with target phonemes using Dynamic Time Warping (DTW)
        Simplified version - for production use proper DTW algorithm
        """
        alignment = []
        
        # Simple greedy alignment (for production, use proper DTW)
        student_idx = 0
        target_idx = 0
        
        while student_idx < len(student_phonemes) and target_idx < len(target_phonemes):
            if student_phonemes[student_idx] == target_phonemes[target_idx]:
                alignment.append((target_idx, student_idx))
                student_idx += 1
                target_idx += 1
            elif student_idx < len(student_phonemes) - 1 and \
                 student_phonemes[student_idx + 1] == target_phonemes[target_idx]:
                # Skip insertion
                student_idx += 1
            elif target_idx < len(target_phonemes) - 1 and \
                 student_phonemes[student_idx] == target_phonemes[target_idx + 1]:
                # Skip deletion
                target_idx += 1
            else:
                # Substitution
                alignment.append((target_idx, student_idx))
                student_idx += 1
                target_idx += 1
        
        return alignment

