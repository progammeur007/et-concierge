import os
import re
import json
import logging
import networkx as nx
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ET_Concierge")

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


def _extract_json(text: str) -> dict:
    """
    Robustly pull the first JSON object out of an LLM response,
    regardless of whether it's wrapped in markdown fences or not.
    """
    # Try to find a JSON block inside ```json ... ``` or ``` ... ```
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return json.loads(fence.group(1))
    # Fallback: find first { ... } in the raw string
    bare = re.search(r"\{.*\}", text, re.DOTALL)
    if bare:
        return json.loads(bare.group(0))
    raise ValueError(f"No JSON object found in LLM response: {text[:200]}")


def _sanitize_for_tts(text: str) -> str:
    """
    Strip markdown formatting so TTS doesn't read out
    asterisks, hashes, backticks, and bullet dashes.
    """
    text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text)   # bold/italic
    text = re.sub(r"`{1,3}(.+?)`{1,3}", r"\1", text)      # code spans
    text = re.sub(r"#+\s*", "", text)                       # headings
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)  # bullets
    text = re.sub(r"\n{2,}", ". ", text)                    # paragraph breaks
    text = re.sub(r"\n", " ", text)
    return text.strip()


def _trim_history(history: list, max_turns: int = 6) -> list:
    """
    Keep only the last N user+model turn pairs so the context window
    doesn't balloon. Each turn = 2 items (user + model).
    """
    max_items = max_turns * 2
    if len(history) > max_items:
        logger.info(f"Trimming chat history from {len(history)} to {max_items} items")
        return history[-max_items:]
    return history


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class ETVoiceController:

    # Keywords → persona mapping for local (zero-LLM) intent routing.
    # This uses your intent_routing table from the JSON but runs instantly
    # without an API call for the most common phrases.
    KEYWORD_PERSONA_MAP = {
        "invest safely":        "Conservative Investor",
        "fixed income":         "Conservative Investor",
        "stable return":        "Conservative Investor",
        "emergency fund":       "Emergency Fund Builder",
        "trade":                "Active Trader",
        "trading":              "Active Trader",
        "stock market live":    "Active Trader",
        "day trader":           "Day Trader",
        "f&o":                  "F&O Trader",
        "options":              "F&O Trader",
        "research":             "Serious Researcher",
        "stock report":         "Serious Researcher",
        "long term":            "Long-term Investor",
        "ceo":                  "CEOs",
        "founder":              "Founder",
        "scale my business":    "CEOs",
        "leadership":           "CEOs",
        "hr":                   "HR Professionals",
        "human resource":       "HR Professionals",
        "marketing":            "Marketing Heads",
        "cmo":                  "CMOs",
        "student":              "Student",
        "ai camp":              "Student",
        "credit card":          "Frequent Traveler",
        "lounge":               "Frequent Traveler",
        "travel":               "Frequent Traveler",
        "negotiation":          "Sales Heads",
        "event":                "Founder",
        "summit":               "Industrialist",
        "masterclass":          "Working Professional",
        "learn":                "Working Professional",
    }

    def __init__(self, json_path: str):
        if not API_KEY:
            raise ValueError("GEMINI_API_KEY missing from .env file.")

        with open(json_path, 'r') as f:
            self.data = json.load(f)

        self.G = nx.MultiDiGraph()
        self._build_graph()

        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        # We manage history ourselves so we can trim it
        self._history: list = []

    # ------------------------------------------------------------------
    # Graph construction — seeds ALL entity types, not just products
    # ------------------------------------------------------------------

    def _build_graph(self):
        logger.info("Building knowledge graph...")

        # Products
        for item in self.data.get('products', []):
            self._seed_entity(item, 'Product')

        # Events
        for item in self.data.get('events', []):
            self._seed_entity(item, 'Event')

        # Masterclasses
        for item in self.data.get('masterclasses', []):
            self._seed_entity(item, 'Masterclass')

        # Partner services
        for item in self.data.get('partner_services', []):
            self._seed_entity(item, 'Partner')

        # Cross-sell edges from the cross_sell_graph index
        for source_id, targets in self.data.get('cross_sell_graph', {}).items():
            for target_id in targets:
                if self.G.has_node(source_id) and self.G.has_node(target_id):
                    self.G.add_edge(source_id, target_id, label='CROSS_SELL', weight=2)

        # Intent routing edges
        for intent_obj in self.data.get('intent_routing', []):
            intent_node = f"intent::{intent_obj['user_intent']}"
            self.G.add_node(intent_node, type='Intent', attr=intent_obj)
            for prod_id in intent_obj.get('recommended_products', []):
                if self.G.has_node(prod_id):
                    self.G.add_edge(intent_node, prod_id, label='ROUTES_TO', weight=5)

        logger.info(
            f"Graph ready — {self.G.number_of_nodes()} nodes, "
            f"{self.G.number_of_edges()} edges"
        )

    def _seed_entity(self, item: dict, entity_type: str):
        entity_id = item.get('id') or item.get('name', '').replace(' ', '_').lower()
        self.G.add_node(entity_id, type=entity_type, attr=item)

        # Persona → entity edges (high weight = strong signal)
        for persona in item.get('target_persona', []):
            persona_node = f"persona::{persona}"
            if not self.G.has_node(persona_node):
                self.G.add_node(persona_node, type='Persona')
            self.G.add_edge(persona_node, entity_id, label='IDEAL_FOR', weight=3)

        # FAQ nodes linked to entity
        for faq in item.get('faq', []):
            faq_node = f"faq::{entity_id}::{faq['q'][:40]}"
            self.G.add_node(faq_node, type='FAQ', attr=faq)
            self.G.add_edge(entity_id, faq_node, label='HAS_FAQ', weight=1)

    # ------------------------------------------------------------------
    # Intent resolution — local first, LLM fallback
    # ------------------------------------------------------------------

    def _local_persona_match(self, user_input: str) -> Optional[str]:
        """
        Check the keyword map before spending an LLM call.
        Returns persona string or None.
        """
        lower = user_input.lower()
        for keyword, persona in self.KEYWORD_PERSONA_MAP.items():
            if keyword in lower:
                logger.info(f"Local match: '{keyword}' → {persona}")
                return persona
        return None

    def _llm_persona_extract(self, user_input: str) -> dict:
        """
        Fallback: ask the LLM to classify when keywords don't match.
        Uses a strict JSON schema in the prompt to prevent parse failures.
        """
        prompt = (
            "You are a classifier. Given the user message below, return ONLY a "
            "valid JSON object with exactly these two keys:\n"
            '  "persona": one of [HNI, Active Trader, Conservative Investor, '
            'CEOs, HR Professionals, Marketing Heads, Student, Frequent Traveler, '
            'Sales Heads, Working Professional, Long-term Investor, General]\n'
            '  "goal": a short phrase describing what they want\n\n'
            "No explanation, no markdown, no extra keys.\n\n"
            f'User message: "{user_input}"'
        )
        try:
            result = self.model.generate_content(prompt).text
            return _extract_json(result)
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"LLM persona extraction failed: {e}. Using General fallback.")
            return {"persona": "General", "goal": user_input}

    # ------------------------------------------------------------------
    # Graph retrieval — 2-hop with cross-sells and FAQs
    # ------------------------------------------------------------------

    def _get_context(self, persona: str, user_input: str) -> dict:
        """
        Returns a context bundle with:
          - primary products/events matching the persona
          - cross-sell suggestions (2nd hop)
          - relevant FAQs (from attached FAQ nodes)
        """
        persona_node = f"persona::{persona}"
        primary_entities = []
        cross_sells = []
        faqs = []

        if self.G.has_node(persona_node):
            for entity_id in self.G.neighbors(persona_node):
                node_data = self.G.nodes[entity_id]
                if node_data.get('type') in ('Product', 'Event', 'Masterclass', 'Partner'):
                    entity_attr = node_data.get('attr', {})
                    primary_entities.append(entity_attr)

                    # 2nd hop: cross-sells
                    for cross_id in self.G.neighbors(entity_id):
                        cross_node = self.G.nodes[cross_id]
                        if cross_node.get('type') in ('Product', 'Event', 'Masterclass', 'Partner'):
                            cs_attr = cross_node.get('attr', {})
                            if cs_attr not in cross_sells and cs_attr not in primary_entities:
                                cross_sells.append(cs_attr)

                    # FAQs attached to this entity
                    for faq_id in self.G.neighbors(entity_id):
                        faq_node = self.G.nodes[faq_id]
                        if faq_node.get('type') == 'FAQ':
                            faq_attr = faq_node.get('attr', {})
                            # Only include FAQ if question is relevant to user input
                            if any(word in user_input.lower() for word in faq_attr.get('q', '').lower().split()):
                                faqs.append(faq_attr)

        # Fallback if persona matched nothing in graph
        if not primary_entities:
            logger.warning(f"No graph match for persona '{persona}'. Using top products.")
            primary_entities = [
                self.G.nodes[n].get('attr', {})
                for n in list(self.G.nodes)
                if self.G.nodes[n].get('type') == 'Product'
            ][:3]

        logger.info(
            f"Context: {len(primary_entities)} primary, "
            f"{len(cross_sells)} cross-sells, {len(faqs)} FAQs"
        )
        return {
            "primary": primary_entities[:3],     # cap to avoid prompt bloat
            "cross_sells": cross_sells[:2],
            "faqs": faqs[:2],
        }

    # ------------------------------------------------------------------
    # Final response generation
    # ------------------------------------------------------------------

    def _build_final_prompt(self, user_input: str, context: dict) -> str:
        return f"""You are Priya, a warm and knowledgeable ET (Economic Times) voice assistant.
You are speaking out loud — the user will HEAR your response, not read it.

STRICT RULES FOR VOICE:
- Use plain spoken English only. No bullet points, no asterisks, no markdown, no hyphens as bullets.
- Keep the response under 80 words. Voice responses must be concise.
- Speak in natural sentences, like a helpful advisor on a phone call.
- Always mention one specific number (price, return percentage, or feature count) to sound credible.
- End with a single soft follow-up question to continue the conversation.

CONTEXT FROM ET'S KNOWLEDGE BASE:
Primary recommendations: {json.dumps(context['primary'], indent=None)}
Cross-sell options: {json.dumps(context['cross_sells'], indent=None)}
Relevant FAQs: {json.dumps(context['faqs'], indent=None)}

USER SAID: "{user_input}"

Respond now as Priya, following all voice rules above:"""

    # ------------------------------------------------------------------
    # Main entry point — called after STT gives you text
    # ------------------------------------------------------------------

    def process_request(self, user_input: str) -> str:
        """
        Full pipeline: intent → graph → LLM → TTS-safe text.
        Returns clean spoken text ready for your TTS engine.
        """
        logger.info(f"Processing: '{user_input}'")

        # Phase 1: Resolve persona (local keyword first, LLM fallback)
        persona = self._local_persona_match(user_input)
        if persona is None:
            logger.info("No local keyword match — calling LLM for classification")
            profile = self._llm_persona_extract(user_input)
            persona = profile.get('persona', 'General')

        logger.info(f"Persona resolved: {persona}")

        # Phase 2: Graph retrieval (2-hop)
        context = self._get_context(persona, user_input)

        # Phase 3: LLM response with trimmed history
        self._history = _trim_history(self._history, max_turns=6)

        prompt = self._build_final_prompt(user_input, context)

        # Build the request with trimmed history as context
        messages = self._history + [{"role": "user", "parts": [prompt]}]

        try:
            response = self.model.generate_content(messages)
            raw_text = response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return "I'm sorry, I'm having trouble connecting right now. Please try again in a moment."

        # Phase 4: Sanitize for TTS
        spoken_text = _sanitize_for_tts(raw_text)
        logger.info(f"Response ({len(spoken_text)} chars): {spoken_text[:80]}...")

        # Update history with the clean spoken version
        self._history.append({"role": "user", "parts": [user_input]})
        self._history.append({"role": "model", "parts": [spoken_text]})

        return spoken_text

    def reset_session(self):
        """Call this between independent user sessions."""
        self._history = []
        logger.info("Session reset.")
    
        


# ---------------------------------------------------------------------------
# Entry point for testing without full STT/TTS stack
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    controller = ETVoiceController("et_data.json")

    test_queries = [
        "I want to invest safely with good returns",
        "I'm a CEO and want to scale my business",
        "what masterclasses do you have for HR professionals",
        "tell me about the credit card benefits",
        "I'm a student interested in AI",
    ]

    for q in test_queries:
        print(f"\nQ: {q}")
        print(f"A: {controller.process_request(q)}")
        print("-" * 60)

