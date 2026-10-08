import pytest
from backend.services.chatbot import bot_engine

@pytest.mark.asyncio
async def test_chatbot_intent_detection():
    # Greeting
    intent, _ = bot_engine.match_intent("Hello AgriBot!")
    assert intent == "greeting"

    # Hindi Greeting
    intent_hi, _ = bot_engine.match_intent("नमस्ते भाई")
    assert intent_hi == "greeting"

    # Symptoms
    intent_sym, _ = bot_engine.match_intent("What are the symptoms of this blight?")
    assert intent_sym == "symptoms"

    # Treatment in Hindi transliteration
    intent_ilaj, _ = bot_engine.match_intent("iska ilaj aur upchar kya hai?")
    assert intent_ilaj == "treatment"

    # Organic
    intent_org, _ = bot_engine.match_intent("Can I use neem oil or organic remedy?")
    assert intent_org == "organic_alternative"

    # Spread
    intent_sp, _ = bot_engine.match_intent("Will this spread to other crops?")
    assert intent_sp in ["how_it_spreads", "spread_to_other_plants"]

    # Unknown
    intent_unk, _ = bot_engine.match_intent("What is the stock price of Apple?")
    assert intent_unk == "unknown"

@pytest.mark.asyncio
async def test_chatbot_grounded_response_with_disclaimer():
    dummy_insight = {
        "crop": "Tomato",
        "disease_name": "Early blight",
        "scientific_name": "Alternaria solani",
        "disease_type": "fungal",
        "summary": "Early blight is a fungal infection.",
        "symptoms": ["Concentric dark rings on leaves."],
        "causes_and_spread": ["Splashing rain and high humidity."],
        "treatment_by_severity": {
            "Medium": {
                "immediate_actions": ["Prune affected leaves."],
                "organic_options": ["Apply neem oil."],
                "chemical_options": [
                    {
                        "active_ingredient": "Chlorothalonil",
                        "note": "Broad-spectrum contact fungicide.",
                        "caution": "Wear protective gear."
                    }
                ]
            }
        },
        "recovery_outlook": "10-14 days with proper pruning.",
        "when_to_consult_expert": "Consult KVK if spreading rapidly."
    }

    reply, intent, chips = await bot_engine.get_reply("How do I treat this?", dummy_insight, severity="Medium")
    assert intent == "treatment"
    assert "Chlorothalonil" in reply
    # Must include safety reminder
    assert "Safety Reminder" in reply
    assert len(chips) > 0

@pytest.mark.asyncio
async def test_chatbot_unknown_fallback():
    # 1. General chat with no leaf scanned yet
    reply_gen, _, _ = await bot_engine.get_reply("Tell me the weather tomorrow", None)
    assert "crop" in reply_gen.lower() or "photo" in reply_gen.lower()

    # 2. Grounded chat on a disease with unknown question
    dummy_insight = {
        "crop": "Tomato",
        "disease_name": "Early blight",
        "summary": "Early blight is a fungal infection.",
        "symptoms": ["Concentric dark rings."],
        "causes_and_spread": ["Rain splash."]
    }
    reply_dis, _, _ = await bot_engine.get_reply("What is the stock price of crude oil?", dummy_insight)
    assert "cannot fully answer" in reply_dis.lower() or "krishi vigyan kendra" in reply_dis.lower()

