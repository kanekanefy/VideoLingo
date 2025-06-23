"""
Emotion Detection Module

Provides AI-powered emotion detection and classification for text content.
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import time

class EmotionLabel(Enum):
    """Standard emotion labels."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    EXCITED = "excited"
    CALM = "calm"
    ANXIOUS = "anxious"
    LOVING = "loving"
    NOSTALGIC = "nostalgic"

@dataclass
class EmotionScore:
    """Emotion detection result."""
    emotion: EmotionLabel
    confidence: float
    intensity: float  # 0.0 to 1.0
    context_clues: List[str]

@dataclass
class EmotionAnalysisResult:
    """Complete emotion analysis result."""
    text: str
    primary_emotion: EmotionScore
    secondary_emotions: List[EmotionScore]
    overall_sentiment: str  # "positive", "negative", "neutral"
    emotional_keywords: List[str]
    analysis_timestamp: str

class EmotionDetector:
    """AI-powered emotion detection for text content."""
    
    def __init__(self):
        self.emotion_keywords = self._load_emotion_keywords()
        self.sentiment_patterns = self._load_sentiment_patterns()
        self.context_rules = self._load_context_rules()
        
        # Cache for expensive operations
        self._analysis_cache = {}
        self.cache_max_size = 1000
    
    def _load_emotion_keywords(self) -> Dict[EmotionLabel, List[str]]:
        """Load emotion keyword mappings."""
        return {
            EmotionLabel.HAPPY: [
                "happy", "joy", "delight", "pleased", "cheerful", "glad", "elated",
                "euphoric", "blissful", "content", "satisfied", "thrilled", "excited",
                "laugh", "smile", "grin", "chuckle", "giggle", "celebrate"
            ],
            EmotionLabel.SAD: [
                "sad", "sorrow", "grief", "melancholy", "depressed", "downcast",
                "dejected", "mournful", "somber", "gloomy", "despondent", "heartbroken",
                "cry", "weep", "tears", "sob", "mourn", "lament"
            ],
            EmotionLabel.ANGRY: [
                "angry", "rage", "fury", "wrath", "irritated", "annoyed", "furious",
                "livid", "enraged", "incensed", "outraged", "infuriated", "mad",
                "shout", "yell", "scream", "argue", "fight", "aggressive"
            ],
            EmotionLabel.FEARFUL: [
                "fear", "afraid", "scared", "terrified", "frightened", "anxious",
                "worried", "nervous", "panicked", "alarmed", "horrified", "dread",
                "tremble", "shake", "hide", "flee", "escape", "threat"
            ],
            EmotionLabel.SURPRISED: [
                "surprised", "shocked", "astonished", "amazed", "stunned", "bewildered",
                "startled", "taken aback", "flabbergasted", "dumbfounded", "wow",
                "gasp", "unexpected", "sudden", "unbelievable", "incredible"
            ],
            EmotionLabel.DISGUSTED: [
                "disgusted", "revolted", "repulsed", "sickened", "nauseated", "appalled",
                "horrified", "abhorrent", "loathsome", "vile", "gross", "yuck",
                "ew", "awful", "terrible", "horrible"
            ],
            EmotionLabel.EXCITED: [
                "excited", "thrilled", "enthusiastic", "eager", "pumped", "energetic",
                "passionate", "fervent", "zealous", "animated", "vibrant", "dynamic",
                "can't wait", "looking forward", "anticipate", "hyped"
            ],
            EmotionLabel.CALM: [
                "calm", "peaceful", "serene", "tranquil", "relaxed", "composed",
                "cool", "collected", "steady", "stable", "quiet", "still",
                "meditate", "breathe", "center", "balance"
            ],
            EmotionLabel.ANXIOUS: [
                "anxious", "worried", "concerned", "troubled", "uneasy", "restless",
                "agitated", "nervous", "tense", "stressed", "overwhelmed", "frantic",
                "panic", "worry", "fret", "obsess"
            ],
            EmotionLabel.LOVING: [
                "love", "adore", "cherish", "treasure", "affection", "devotion",
                "care", "warmth", "tenderness", "fondness", "attachment", "bond",
                "hug", "kiss", "embrace", "heart", "beloved", "darling"
            ],
            EmotionLabel.NOSTALGIC: [
                "nostalgic", "reminisce", "remember", "memory", "past", "childhood",
                "miss", "longing", "wistful", "sentimental", "bittersweet", "yearning",
                "used to", "back then", "old days", "memories"
            ]
        }
    
    def _load_sentiment_patterns(self) -> Dict[str, List[str]]:
        """Load sentiment analysis patterns."""
        return {
            "positive": [
                r"\b(great|excellent|amazing|wonderful|fantastic|brilliant|perfect|outstanding)\b",
                r"\b(love|like|enjoy|appreciate|pleased|satisfied|happy|glad)\b",
                r"\b(success|win|victory|triumph|achieve|accomplish|excel)\b",
                r"\b(beautiful|gorgeous|stunning|magnificent|splendid)\b"
            ],
            "negative": [
                r"\b(terrible|awful|horrible|bad|worst|hate|disgusting|revolting)\b",
                r"\b(fail|failure|lose|loss|defeat|disaster|catastrophe)\b",
                r"\b(difficult|hard|tough|challenging|struggle|problem|issue)\b",
                r"\b(ugly|hideous|repulsive|unattractive|unpleasant)\b"
            ],
            "intensifiers": [
                r"\b(very|extremely|incredibly|absolutely|completely|totally|utterly)\b",
                r"\b(so|such|quite|rather|really|truly|genuinely)\b",
                r"\b(most|more|less|least|much|many|few)\b"
            ]
        }
    
    def _load_context_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load contextual analysis rules."""
        return {
            "negation": {
                "patterns": [r"\b(not|no|never|nothing|nobody|nowhere|none)\b"],
                "effect": "invert_sentiment"
            },
            "conditional": {
                "patterns": [r"\b(if|unless|when|whenever|while|although|though)\b"],
                "effect": "reduce_confidence"
            },
            "question": {
                "patterns": [r"\?", r"\b(what|who|where|when|why|how|which|whose)\b"],
                "effect": "neutral_tendency"
            },
            "exclamation": {
                "patterns": [r"!", r"\b(wow|oh|ah|hey|yay|hooray)\b"],
                "effect": "amplify_emotion"
            }
        }
    
    def detect_emotion(self, text: str, language: str = "en") -> EmotionAnalysisResult:
        """Detect emotions in text."""
        # Check cache first
        cache_key = hashlib.md5(f"{text}_{language}".encode()).hexdigest()
        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]
        
        # Clean and normalize text
        normalized_text = self._normalize_text(text)
        
        # Detect emotions
        emotion_scores = self._calculate_emotion_scores(normalized_text)
        
        # Sort by confidence
        emotion_scores.sort(key=lambda x: x.confidence, reverse=True)
        
        # Get primary and secondary emotions
        primary_emotion = emotion_scores[0] if emotion_scores else EmotionScore(
            EmotionLabel.NEUTRAL, 0.5, 0.3, []
        )
        
        secondary_emotions = [e for e in emotion_scores[1:4] if e.confidence > 0.2]
        
        # Calculate overall sentiment
        overall_sentiment = self._calculate_overall_sentiment(normalized_text, emotion_scores)
        
        # Extract emotional keywords
        emotional_keywords = self._extract_emotional_keywords(normalized_text)
        
        result = EmotionAnalysisResult(
            text=text,
            primary_emotion=primary_emotion,
            secondary_emotions=secondary_emotions,
            overall_sentiment=overall_sentiment,
            emotional_keywords=emotional_keywords,
            analysis_timestamp=time.time()
        )
        
        # Cache result
        if len(self._analysis_cache) >= self.cache_max_size:
            # Remove oldest entries
            oldest_key = min(self._analysis_cache.keys(), 
                           key=lambda k: self._analysis_cache[k].analysis_timestamp)
            del self._analysis_cache[oldest_key]
        
        self._analysis_cache[cache_key] = result
        return result
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for analysis."""
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Handle contractions
        contractions = {
            "won't": "will not", "can't": "cannot", "n't": " not",
            "'ll": " will", "'re": " are", "'ve": " have",
            "'d": " would", "'m": " am"
        }
        
        for contraction, expansion in contractions.items():
            normalized = normalized.replace(contraction, expansion)
        
        return normalized
    
    def _calculate_emotion_scores(self, text: str) -> List[EmotionScore]:
        """Calculate emotion scores for text."""
        scores = []
        
        for emotion, keywords in self.emotion_keywords.items():
            confidence, intensity, context_clues = self._calculate_emotion_confidence(
                text, keywords, emotion
            )
            
            if confidence > 0.1:  # Only include emotions with some confidence
                scores.append(EmotionScore(
                    emotion=emotion,
                    confidence=confidence,
                    intensity=intensity,
                    context_clues=context_clues
                ))
        
        return scores
    
    def _calculate_emotion_confidence(self, text: str, keywords: List[str], emotion: EmotionLabel) -> Tuple[float, float, List[str]]:
        """Calculate confidence score for a specific emotion."""
        found_keywords = []
        keyword_scores = []
        
        for keyword in keywords:
            # Count occurrences
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            if matches:
                found_keywords.extend(matches)
                # Weight by keyword strength and frequency
                keyword_strength = self._get_keyword_strength(keyword, emotion)
                frequency_score = min(len(matches) * 0.2, 1.0)
                keyword_scores.append(keyword_strength * frequency_score)
        
        if not keyword_scores:
            return 0.0, 0.0, []
        
        # Base confidence from keyword matches
        base_confidence = min(sum(keyword_scores) / len(keywords), 1.0)
        
        # Apply contextual modifiers
        confidence_modifier, intensity_modifier = self._apply_context_rules(text, emotion)
        
        final_confidence = max(0.0, min(1.0, base_confidence * confidence_modifier))
        final_intensity = max(0.0, min(1.0, base_confidence * intensity_modifier))
        
        return final_confidence, final_intensity, found_keywords
    
    def _get_keyword_strength(self, keyword: str, emotion: EmotionLabel) -> float:
        """Get the strength of a keyword for an emotion."""
        # Strong emotion words get higher weights
        strong_keywords = {
            EmotionLabel.HAPPY: ["euphoric", "blissful", "thrilled", "elated"],
            EmotionLabel.SAD: ["heartbroken", "devastated", "grief", "despair"],
            EmotionLabel.ANGRY: ["furious", "enraged", "livid", "incensed"],
            EmotionLabel.FEARFUL: ["terrified", "horrified", "panicked"],
            EmotionLabel.SURPRISED: ["astonished", "flabbergasted", "stunned"],
        }
        
        if emotion in strong_keywords and keyword in strong_keywords[emotion]:
            return 0.9
        
        # Medium strength for common emotion words
        medium_keywords = ["happy", "sad", "angry", "scared", "surprised"]
        if keyword in medium_keywords:
            return 0.7
        
        # Default strength for other keywords
        return 0.5
    
    def _apply_context_rules(self, text: str, emotion: EmotionLabel) -> Tuple[float, float]:
        """Apply contextual rules to modify confidence and intensity."""
        confidence_modifier = 1.0
        intensity_modifier = 1.0
        
        for rule_name, rule_config in self.context_rules.items():
            for pattern in rule_config["patterns"]:
                if re.search(pattern, text, re.IGNORECASE):
                    effect = rule_config["effect"]
                    
                    if effect == "invert_sentiment":
                        confidence_modifier *= 0.3  # Reduce confidence for negated emotions
                    elif effect == "reduce_confidence":
                        confidence_modifier *= 0.7
                    elif effect == "neutral_tendency":
                        if emotion != EmotionLabel.NEUTRAL:
                            confidence_modifier *= 0.6
                    elif effect == "amplify_emotion":
                        intensity_modifier *= 1.3
        
        return confidence_modifier, intensity_modifier
    
    def _calculate_overall_sentiment(self, text: str, emotion_scores: List[EmotionScore]) -> str:
        """Calculate overall sentiment polarity."""
        positive_emotions = [EmotionLabel.HAPPY, EmotionLabel.EXCITED, EmotionLabel.LOVING, EmotionLabel.CALM]
        negative_emotions = [EmotionLabel.SAD, EmotionLabel.ANGRY, EmotionLabel.FEARFUL, 
                           EmotionLabel.DISGUSTED, EmotionLabel.ANXIOUS]
        
        positive_score = sum(
            score.confidence * score.intensity 
            for score in emotion_scores 
            if score.emotion in positive_emotions
        )
        
        negative_score = sum(
            score.confidence * score.intensity 
            for score in emotion_scores 
            if score.emotion in negative_emotions
        )
        
        # Apply pattern-based sentiment analysis
        pattern_sentiment = self._analyze_sentiment_patterns(text)
        
        # Combine emotion-based and pattern-based sentiment
        total_positive = positive_score + pattern_sentiment.get("positive", 0)
        total_negative = negative_score + pattern_sentiment.get("negative", 0)
        
        if total_positive > total_negative + 0.2:
            return "positive"
        elif total_negative > total_positive + 0.2:
            return "negative"
        else:
            return "neutral"
    
    def _analyze_sentiment_patterns(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using regex patterns."""
        sentiment_scores = {"positive": 0.0, "negative": 0.0}
        
        for sentiment, patterns in self.sentiment_patterns.items():
            if sentiment in ["positive", "negative"]:
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    sentiment_scores[sentiment] += len(matches) * 0.3
        
        # Apply intensifier effects
        intensifier_count = 0
        for pattern in self.sentiment_patterns["intensifiers"]:
            intensifier_count += len(re.findall(pattern, text, re.IGNORECASE))
        
        if intensifier_count > 0:
            amplification = min(1.0 + intensifier_count * 0.2, 2.0)
            sentiment_scores["positive"] *= amplification
            sentiment_scores["negative"] *= amplification
        
        return sentiment_scores
    
    def _extract_emotional_keywords(self, text: str) -> List[str]:
        """Extract emotional keywords from text."""
        keywords = []
        
        for emotion_keywords in self.emotion_keywords.values():
            for keyword in emotion_keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    keywords.append(keyword)
        
        return list(set(keywords))  # Remove duplicates
    
    def batch_analyze(self, texts: List[str], language: str = "en") -> List[EmotionAnalysisResult]:
        """Analyze emotions for multiple texts."""
        results = []
        
        for text in texts:
            try:
                result = self.detect_emotion(text, language)
                results.append(result)
            except Exception as e:
                # Create error result
                error_result = EmotionAnalysisResult(
                    text=text,
                    primary_emotion=EmotionScore(EmotionLabel.NEUTRAL, 0.0, 0.0, []),
                    secondary_emotions=[],
                    overall_sentiment="neutral",
                    emotional_keywords=[],
                    analysis_timestamp=time.time()
                )
                results.append(error_result)
        
        return results
    
    def compare_emotions(self, result1: EmotionAnalysisResult, result2: EmotionAnalysisResult) -> Dict[str, Any]:
        """Compare emotions between two analysis results."""
        return {
            "primary_emotion_match": result1.primary_emotion.emotion == result2.primary_emotion.emotion,
            "sentiment_match": result1.overall_sentiment == result2.overall_sentiment,
            "confidence_diff": abs(result1.primary_emotion.confidence - result2.primary_emotion.confidence),
            "intensity_diff": abs(result1.primary_emotion.intensity - result2.primary_emotion.intensity),
            "emotion_similarity": self._calculate_emotion_similarity(result1, result2),
            "keyword_overlap": len(set(result1.emotional_keywords) & set(result2.emotional_keywords))
        }
    
    def _calculate_emotion_similarity(self, result1: EmotionAnalysisResult, result2: EmotionAnalysisResult) -> float:
        """Calculate similarity between two emotion analysis results."""
        # Create emotion vectors
        emotions = list(EmotionLabel)
        
        vector1 = {}
        vector2 = {}
        
        # Initialize vectors
        for emotion in emotions:
            vector1[emotion] = 0.0
            vector2[emotion] = 0.0
        
        # Fill vectors with scores
        vector1[result1.primary_emotion.emotion] = result1.primary_emotion.confidence
        for secondary in result1.secondary_emotions:
            vector1[secondary.emotion] = secondary.confidence
        
        vector2[result2.primary_emotion.emotion] = result2.primary_emotion.confidence
        for secondary in result2.secondary_emotions:
            vector2[secondary.emotion] = secondary.confidence
        
        # Calculate cosine similarity
        dot_product = sum(vector1[emotion] * vector2[emotion] for emotion in emotions)
        magnitude1 = sum(score ** 2 for score in vector1.values()) ** 0.5
        magnitude2 = sum(score ** 2 for score in vector2.values()) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)