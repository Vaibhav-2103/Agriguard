import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from rapidfuzz import fuzz
import httpx

from backend.config import settings

logger = logging.getLogger("agriguard.chatbot")


# Quick suggestion chips
DEFAULT_QUICK_CHIPS = [
    "How do I treat this?",
    "Organic option?",
    "Will it spread?",
    "How long to recover?",
    "Is it safe to harvest?"
]

# Multilingual intent pattern definitions (English, Hindi transliteration + Devanagari, Punjabi transliteration + Gurmukhi)
INTENT_PATTERNS = {
    "what_is_this": [
        r"\b(what is this|which disease|identify|kya rog hai|kya bimari hai|rog kya hai|bimari kaun si hai|bimaari|disease name|ki bimari hai|ki rog hai)\b",
        r"(क्या रोग है|कौन सी बीमारी है|रोग का नाम|ਕੀ ਬਿਮਾਰੀ ਹੈ)"
    ],
    "symptoms": [
        r"\b(symptom|symptoms|lakshan|sign|signs|pechan|nishan|kive pata lagge|looks like)\b",
        r"(लक्षण|पहचान|ਨਿਸ਼ਾਨ|ਲੱਛਣ)"
    ],
    "causes": [
        r"\b(cause|causes|why did this happen|kyun hua|karan|reason|karan kya hai|kive hoya)\b",
        r"(कारण|क्यों हुआ|ਕਿਉਂ ਹੋਇਆ)"
    ],
    "how_it_spreads": [
        r"\b(how does it spread|spread|failta|phailta|transmission|hawa se|paani se|failega|kive failda)\b",
        r"(कैसे फैलता है|फैलता|ਕਿਵੇਂ ਫੈਲਦਾ)"
    ],
    "treatment": [
        r"\b(treatment|treat|cure|control|spray|medicine|dawa|davai|upchar|ilaj|roktham|ki spray kariye|kiven theek kariye)\b",
        r"\b(high severity|low severity|medium severity|for high|for low|for medium)\b",
        r"(इलाज|उपचार|दवाई|स्प्रे|रोकथाम|ਕਿਵੇਂ ਠੀਕ ਕਰੀਏ|ਦਵਾਈ)"
    ],
    "organic_alternative": [
        r"\b(organic|natural|home remedy|neem|desi ilaj|gharelu upchar|jaivik|qudrat|bina chemical)\b",
        r"(जैविक|नीम|देसी इलाज|घरेलू उपचार|ਜੈਵਿਕ|ਕੁਦਰਤੀ)"
    ],
    "chemical_safety": [
        r"\b(chemical|fungicide|pesticide|safety|keetnashak|dawai precaution|side effect|ppe|kitnashak)\b",
        r"(कीटनाशक|फफूंदनाशक|सुरक्षा|ਕੀਟਨਾਸ਼ਕ)"
    ],
    "fertilizer": [
        r"\b(fertilizer|nutrition|khad|khaad|urea|potash|npk|poshan|diet|khurak)\b",
        r"(खाद|उर्वरक|पोषण|ਖਾਦ)"
    ],
    "prevention": [
        r"\b(prevention|prevent|avoid|bachav|savdhani|rok|aage na ho|kive rokiye)\b",
        r"(बचाव|सावधानी|ਰੋਕਥਾਮ|ਬਚਾਓ)"
    ],
    "recovery_time": [
        r"\b(recovery|how long|how many days|kitne din|theek hone me kitna samay|kab tak theek|time to cure|kine din)\b",
        r"(कितने दिन|ठीक होने में समय|ਕਿੰਨੇ ਦਿਨ)"
    ],
    "spread_to_other_plants": [
        r"\b(other plants|neighboring|dusre paudhe|doosre khet|bagal wale|baki fasal|fail jayega|bakiya nu vi)\b",
        r"(दूसरे पौधों|बाकी फसल|ਦੂਜੇ ਪੌਦੇ)"
    ],
    "can_I_harvest": [
        r"\b(harvest|can i eat|safe to eat|consume|kha sakte hain|tod sakte hain|katayi|mandi|mandee)\b",
        r"(खा सकते हैं|कटाई|ਤੋੜ ਸਕਦੇ ਹਾਂ)"
    ],
    "when_to_see_expert": [
        r"\b(expert|doctor|scientist|krishi vigyan|kvk|officer|sahab|adhikari|dikhana chahiye)\b",
        r"(कृषि वैज्ञानिक|विशेषज्ञ|अधिकारी|ਮਾਹਿਰ)"
    ],
    "greeting": [
        r"^(hello|hi|hey|namaste|pranam|kisan bhai|sasrikal|sat sri akal|good morning|good evening)\b",
        r"(नमस्ते|प्रणाम|सत श्री अकाल|ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ|ਹੈਲੋ)"
    ],
    "thanks": [
        r"\b(thanks|thank you|shukriya|dhanyawad|dhanvaad|mehrbani|thx)\b",
        r"(धन्यवाद|शुक्रिया|ਧੰਨਵਾਦ)"
    ]
}



class AgriBotEngine:
    """Local, grounded AgriBot engine combining fuzzy pattern matching, TF-IDF, and optional Ollama adapter."""

    def __init__(self):
        self._vectorizer = None

    def _get_vectorizer(self):
        if self._vectorizer is None:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            except ImportError:
                self._vectorizer = False
        return self._vectorizer

    def detect_language(self, text: str) -> str:
        """Detects if user is asking in Hindi, Punjabi, or English."""
        # Devanagari script: 0900-097F
        if re.search(r"[\u0900-\u097F]", text):
            return "hi"
        # Gurmukhi script: 0A00-0A7F
        if re.search(r"[\u0A00-\u0A7F]", text):
            return "pa"
        # Transliterated Hindi/Punjabi keywords
        hi_pa_keywords = ["kya", "kyun", "ilaj", "karan", "bimari", "rog", "dawa", "davai", "khet", "paudhe", "fasal", "ki", "kive", "hovega", "theek"]
        words = text.lower().split()
        if any(w in hi_pa_keywords for w in words):
            return "hi_latin"
        return "en"

    def match_intent(self, text: str, faq_list: Optional[List[Dict[str, Any]]] = None) -> Tuple[str, float]:
        """
        Determines the intent from text via regex patterns, fuzzy match, and FAQ cosine similarity.
        Returns: (intent_name, confidence_score)
        """
        cleaned_text = text.lower().strip()

        # 1. Direct Regex / Keyword Matching
        for intent, patterns in INTENT_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, cleaned_text, re.IGNORECASE):
                    return intent, 0.95

        # 2. Fuzzy Matching against Canonical Intent Phrases
        best_intent = "unknown"
        best_score = 0.0

        for intent, patterns in INTENT_PATTERNS.items():
            for pat in patterns:
                # Strip regex symbols to get clean exemplar phrases
                clean_phrase = re.sub(r"[\\^$*+?.()|[\]{}]", " ", pat).strip()
                for phrase in clean_phrase.split():
                    if len(phrase) >= 5:
                        score = fuzz.token_set_ratio(phrase, cleaned_text)
                        if score > best_score:
                            best_score = score
                            best_intent = intent

        if best_score >= 85.0:
            return best_intent, round(best_score / 100.0, 2)

        # 3. TF-IDF matching against Disease FAQs if available
        if faq_list:
            vec = self._get_vectorizer()
            if vec:
                try:
                    from sklearn.metrics.pairwise import cosine_similarity
                    faq_corpus = [f"{item['q']} {' '.join(item.get('keywords', []))}" for item in faq_list]
                    tfidf_mat = vec.fit_transform(faq_corpus + [cleaned_text])
                    sims = cosine_similarity(tfidf_mat[-1:], tfidf_mat[:-1])[0]
                    max_sim_idx = sims.argmax()
                    max_sim = float(sims[max_sim_idx])

                    if max_sim >= 0.35:
                        matched_q = faq_list[max_sim_idx]['q'].lower()
                        if "treat" in matched_q or "spray" in matched_q:
                            return "treatment", max_sim
                        if "organic" in matched_q:
                            return "organic_alternative", max_sim
                        if "spread" in matched_q:
                            return "spread_to_other_plants", max_sim
                        if "harvest" in matched_q:
                            return "can_I_harvest", max_sim
                        if "recovery" in matched_q:
                            return "recovery_time", max_sim
                        if "disease" in matched_q or "what" in matched_q:
                            return "what_is_this", max_sim
                except Exception as e:
                    logger.debug(f"TF-IDF matching fallback: {e}")


        return "unknown", 0.0

    def generate_response(
        self,
        intent: str,
        insight: Optional[Dict[str, Any]],
        severity: Optional[str] = "Medium",
        language: str = "en",
        recent_history: Optional[List[Dict[str, str]]] = None,
        user_message: str = ""
    ) -> str:
        """
        Synthesizes grounded advice based on the detected intent and disease knowledge entry.
        Never invents facts. Reminds users of product labels on chemical recommendations.
        """
        sev = severity if severity in ["Low", "Medium", "High"] else "Medium"

        # Check if user explicitly mentioned severity in current query
        query_lower = user_message.lower() if user_message else ""
        if "high" in query_lower:
            sev = "High"
        elif "low" in query_lower:
            sev = "Low"
        elif "medium" in query_lower:
            sev = "Medium"
        elif recent_history:
            # Check previous turns
            last_user_msg = recent_history[-1].get("content", "").lower()
            if "high" in last_user_msg:
                sev = "High"
            elif "low" in last_user_msg:
                sev = "Low"
            elif "medium" in last_user_msg:
                sev = "Medium"


        crop = insight.get("crop", "crop") if insight else "crop"
        disease = insight.get("disease_name", "the detected condition") if insight else "the condition"
        is_healthy = insight.get("disease_type") == "healthy" if insight else False

        # Greeting & Thanks
        if intent == "greeting":
            if language in ["hi", "hi_latin"]:
                return f"नमस्ते किसान भाई! मैं AgriBot हूँ। आपकी {crop} की फसल और {disease} के समाधान में मैं आपकी क्या सहायता कर सकता हूँ?"
            elif language == "pa":
                return f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਕਿਸਾਨ ਵੀਰ ਜੀ! ਮੈਂ AgriBot ਹਾਂ। ਤੁਹਾਡੀ {crop} ਦੀ ਫ਼ਸਲ ਲਈ ਮੈਂ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?"
            return f"Hello! I am AgriBot, your personal farm health assistant. How can I help you manage your {crop}?"

        if intent == "thanks":
            if language in ["hi", "hi_latin"]:
                return "आपका स्वागत है किसान भाई! अपनी फसल का ध्यान रखें और कोई भी संशय हो तो अवश्य पूछें।"
            elif language == "pa":
                return "ਜੀ ਆਇਆਂ ਨੂੰ! ਆਪਣੀ ਫ਼ਸਲ ਦਾ ਖ਼ਿਆਲ ਰੱਖੋ।"
            return "You are very welcome! Healthy crops lead to abundant harvests. Feel free to ask anytime."

        # If no disease insight is attached (general chat)
        if not insight:
            return (
                "I am here to help you identify and manage crop diseases. "
                "Please scan or upload a clear photo of your crop leaf first, "
                "or ask me general questions about crop disease prevention."
            )

        # Grounded responses based on Knowledge Base Entry
        if intent == "what_is_this":
            if is_healthy:
                return f"Great news! Your {crop} appears healthy with no visible signs of infection or severe pest damage. Maintain regular watering and soil nutrition."
            return (
                f"Your {crop} has been diagnosed with **{disease}** ({insight.get('scientific_name', '')}). "
                f"{insight.get('summary', '')}"
            )

        if intent == "symptoms":
            s_list = insight.get("symptoms", [])
            s_text = " • " + "\n • ".join(s_list) if s_list else "Foliar discoloration and spots."
            return f"Key symptoms of **{disease}** on {crop} include:\n{s_text}"

        if intent == "causes" or intent == "how_it_spreads":
            c_list = insight.get("causes_and_spread", [])
            c_text = " • " + "\n • ".join(c_list) if c_list else "High humidity, overhead water splash, and spores."
            return f"Causes and spread factors for **{disease}**:\n{c_text}"

        if intent == "treatment":
            if is_healthy:
                return f"No curative treatment is needed because your {crop} is healthy. Keep soil well-drained and scout weekly."
            t_plan = insight.get("treatment_by_severity", {}).get(sev, {})
            immediate = t_plan.get("immediate_actions", [])
            chem = t_plan.get("chemical_options", [])
            
            resp = [f"**Action Plan for {sev} Severity ({disease} on {crop}):**"]
            if immediate:
                resp.append("\n**Immediate cultural steps:**")
                for a in immediate:
                    resp.append(f" • {a}")
            if chem:
                resp.append("\n**Recommended Active Ingredients:**")
                for c in chem:
                    resp.append(f" • **{c['active_ingredient']}**: {c['note']}")
            resp.append(
                "\n⚠️ **Safety Reminder:** Always read the product label for exact application timing, wear personal protective equipment (gloves, mask), and follow your district agriculture department advice."
            )
            return "\n".join(resp)

        if intent == "organic_alternative":
            if is_healthy:
                return f"For healthy {crop}, organic maintenance includes well-rotted farmyard manure, compost tea, and mulching."
            t_plan = insight.get("treatment_by_severity", {}).get(sev, {})
            organic = t_plan.get("organic_options", [])
            if not organic:
                organic = insight.get("treatment_by_severity", {}).get("Low", {}).get("organic_options", [])
            resp = [f"**Organic & Biological Solutions for {disease}:**"]
            for o in organic:
                resp.append(f" • {o}")
            resp.append("\nEnsure infected leaves are destroyed safely and prune in dry weather.")
            return "\n".join(resp)

        if intent == "chemical_safety":
            return (
                "**Chemical Application & Safety Protocol:**\n"
                "1. **Protective Gear:** Always wear chemical-resistant gloves, eye goggles, and a respiratory mask.\n"
                "2. **Spray Timing:** Spray during calm early morning or late evening hours. Never spray against the wind or during hot midday sun.\n"
                "3. **Pollinator Protection:** Avoid spraying flowers when honeybees are foraging.\n"
                "4. **Pre-Harvest Interval (PHI):** Check the container label for the mandatory waiting period between spraying and harvest."
            )

        if intent == "fertilizer":
            f_list = insight.get("fertilizer_and_nutrition", [])
            f_text = " • " + "\n • ".join(f_list) if f_list else "Maintain balanced N-P-K."
            return f"**Fertilizer & Soil Nutrition Advice for {crop}:**\n{f_text}"

        if intent == "prevention":
            p_list = insight.get("precautions_and_prevention", [])
            p_text = " • " + "\n • ".join(p_list) if p_list else "Sanitize tools and practice crop rotation."
            return f"**Prevention & Field Hygiene:**\n{p_text}"

        if intent == "recovery_time":
            return f"**Recovery Outlook:** {insight.get('recovery_outlook', 'Moderate recovery expected in 10-14 days.')}"

        if intent == "spread_to_other_plants":
            if is_healthy:
                return f"Your {crop} is healthy, so there is no disease pathogen to spread to other plants."
            return (
                f"**Spread Risk:** Yes, pathogens causing {disease} can spread rapidly to nearby plants through rain splashes, wind currents, and contaminated hands or shears. "
                "Disinfect your pruning shears with alcohol between plants and avoid overhead watering."
            )

        if intent == "can_I_harvest":
            if is_healthy:
                return f"Yes, you can harvest ripe produce from your healthy {crop} normally."
            return (
                f"Uninfected parts of {crop} can be harvested and consumed after thorough washing. "
                "However, if any synthetic chemical fungicide or pesticide was recently applied, you **MUST observe the Pre-Harvest Interval (PHI)** on the chemical bottle label before picking."
            )

        if intent == "when_to_see_expert":
            return f"**Expert Guidance:** {insight.get('when_to_consult_expert', 'Consult your local Krishi Vigyan Kendra or extension officer if disease exceeds 30% of the canopy.')}"

        # Unknown intent: Honest fallback without hallucination
        closest_advice = insight.get("summary", "")
        return (
            f"I cannot fully answer that specific question with certainty. "
            f"Regarding **{disease}** on **{crop}**: {closest_advice}\n\n"
            f"For specialized diagnosis or chemical formulations, please show sample leaves to your local Agriculture Extension Officer or Krishi Vigyan Kendra (KVK)."
        )

    async def get_reply(
        self,
        user_message: str,
        insight: Optional[Dict[str, Any]] = None,
        severity: Optional[str] = "Medium",
        recent_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, str, List[str]]:
        """
        Orchestrates answering: tries Ollama if configured, otherwise uses local rules engine.
        Returns: (reply_text, detected_intent, quick_chips)
        """
        language = self.detect_language(user_message)
        faq_list = insight.get("faq", []) if insight else []
        intent, conf = self.match_intent(user_message, faq_list=faq_list)

        # Optional Ollama Adapter
        if settings.CHATBOT_BACKEND == "ollama":
            try:
                system_prompt = (
                    f"You are AgriBot, an agricultural crop doctor. Ground your answer strictly on this data:\n"
                    f"Crop: {insight.get('crop') if insight else 'Unknown'}\n"
                    f"Disease: {insight.get('disease_name') if insight else 'Unknown'}\n"
                    f"Severity: {severity}\n"
                    f"Details: {json.dumps(insight) if insight else 'None'}\n"
                    f"Answer in simple, clear sentences. Never invent chemical brand names or dosages."
                )
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.post(
                        f"{settings.OLLAMA_BASE_URL}/api/generate",
                        json={
                            "model": settings.OLLAMA_MODEL,
                            "prompt": f"{system_prompt}\nUser: {user_message}\nAgriBot:",
                            "stream": False
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        reply = data.get("response", "").strip()
                        if reply:
                            return reply, intent, DEFAULT_QUICK_CHIPS
            except Exception as e:
                logger.warning(f"Ollama backend unavailable, falling back to local rule engine: {e}")

        # Local Rules / Retrieval Engine
        reply = self.generate_response(
            intent=intent,
            insight=insight,
            severity=severity,
            language=language,
            recent_history=recent_history,
            user_message=user_message
        )
        return reply, intent, DEFAULT_QUICK_CHIPS



bot_engine = AgriBotEngine()
