"""Simple keyword-based local search engine for NovaMart policy documents.

Uses only the Python standard library to find text excerpts from local
Markdown policy documents without external dependencies or AI integration.

IMPORTANT ARCHITECTURAL NOTE ON LIMITATIONS:
Keyword overlap measures only lexical token matches. It DOES NOT verify whether
an excerpt semantically answers a user's question, nor does it guarantee factual
applicability. For instance, a query asking about a bicycle warranty will match
warranty exclusions because the words 'standard', 'warranty', and 'cover' overlap,
even though the policy text only applies to electronics and appliances and never
establishes whether bicycle coverage exists.
"""

from pathlib import Path
import re
from typing import Dict, List, Optional, Set

# Common English grammatical stop words and the project brand token.
STOP_WORDS: Set[str] = {
    "a", "about", "an", "and", "are", "as", "at", "be", "by", "can", "could",
    "did", "do", "does", "for", "from", "had", "has", "have", "how", "i",
    "if", "in", "is", "it", "many", "me", "my", "no", "not", "of", "on", "or",
    "our", "should", "so", "some", "that", "the", "their", "there", "they",
    "this", "to", "was", "we", "what", "when", "where", "which", "who",
    "will", "with", "would", "you", "your",
    # Brand token: prevents the company name from acting as false evidence
    "novamart",
}

# Default directory where policy Markdown files are located.
DEFAULT_POLICIES_DIR = Path(__file__).resolve().parent.parent / "data" / "policies"


def normalize_token(word: str) -> str:
    """Beginner-friendly stemmer to group common singular and plural word forms.
    
    Examples:
    - 'days' -> 'day'
    - 'items' -> 'item'
    - 'warranties' -> 'warranty'
    - 'returns' -> 'return'
    """
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("es") and len(word) > 3 and not word.endswith(("ees", "oes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith(("ss", "us", "is")) and len(word) > 2:
        return word[:-1]
    return word


def tokenize(text: str) -> List[str]:
    """Extract lowercase words, filter out stop words, and normalize plurals."""
    raw_words = re.findall(r"\b[a-z0-9]{2,}\b", text.lower())
    return [normalize_token(w) for w in raw_words if w not in STOP_WORDS]


def extract_keywords(text: str) -> Set[str]:
    """Tokenize text into a unique set of non-stop words."""
    return set(tokenize(text))


class PolicyChunk:
    """Represents a coherent section of a policy document."""

    def __init__(self, source_file: str, doc_title: str, section_title: str, content: str):
        self.source_file = source_file
        self.doc_title = doc_title
        self.section_title = section_title
        self.content = content.strip()
        # Searchable vocabulary is scoped to section title and section body.
        # Notice: doc_title is excluded from searchable terms so that terms in the
        # file title (like 'Return Policy') do not artificially leak into every section.
        self.searchable_terms = set(tokenize(f"{section_title} {content}"))
        self.title_terms = set(tokenize(section_title))
        # Normalized root of the filename (e.g. 'returns.md' -> 'return')
        self.file_keyword = normalize_token(source_file.replace(".md", ""))

    def evaluate_relevance(self, query_keywords: Set[str]) -> Optional[Dict[str, object]]:
        """Evaluate chunk relevance against query keywords.
        
        NOTE: This only checks keyword presence. It cannot evaluate whether the
        matched text truly answers the user's intent.
        
        Returns None if:
        - For single-keyword queries: 0 terms match.
        - For multi-keyword queries: fewer than 2 terms match.
        """
        matched = query_keywords.intersection(self.searchable_terms)
        required_matches = 1 if len(query_keywords) == 1 else 2

        if len(matched) < required_matches:
            return None

        # Base score is number of matched distinct keywords.
        score = len(matched) * 10

        # Title match bonus gives priority to sections whose heading directly addresses the query.
        title_matches = query_keywords.intersection(self.title_terms)
        score += len(title_matches) * 15

        # Document topic bonus if the filename itself matches a query keyword.
        if self.file_keyword in query_keywords:
            score += 5

        return {
            "score": score,
            "match_count": len(matched),
            "matched_terms": sorted(list(matched)),
            "title_matched": sorted(list(title_matches))
        }


def load_policy_chunks(policies_dir: Optional[Path] = None) -> List[PolicyChunk]:
    """Read all markdown policy files and split them into section chunks."""
    target_dir = policies_dir or DEFAULT_POLICIES_DIR
    chunks: List[PolicyChunk] = []

    if not target_dir.exists():
        return chunks

    for file_path in sorted(target_dir.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        sections = re.split(r"(?m)^##\s+", text)

        doc_title = sections[0].split("\n")[0].replace("#", "").strip()

        for raw_section in sections[1:]:
            lines = raw_section.strip().split("\n")
            section_title = lines[0].strip()
            section_body = "\n".join(lines[1:]).strip()

            if section_body:
                chunks.append(
                    PolicyChunk(
                        source_file=file_path.name,
                        doc_title=doc_title,
                        section_title=section_title,
                        content=section_body,
                    )
                )

    return chunks


def search_policies(
    query: str,
    top_k: int = 2,
    policies_dir: Optional[Path] = None
) -> List[Dict[str, object]]:
    """Search policy documents for excerpts relevant to the query.
    
    LIMITATION NOTICE:
    A returned excerpt indicates keyword overlap, NOT verified comprehension.
    The function does not determine whether the excerpt actually establishes the
    answer to the question.
    
    Returns an empty list if:
    - The query has no meaningful keywords after filtering stop words.
    - No document sections meet the minimum relevance criteria.
    - No evidence is found in the local knowledge base.
    """
    keywords = extract_keywords(query)
    if not keywords:
        return []

    chunks = load_policy_chunks(policies_dir)
    scored_results: List[Dict[str, object]] = []

    for chunk in chunks:
        relevance = chunk.evaluate_relevance(keywords)
        if relevance is not None:
            scored_results.append({
                "source": chunk.source_file,
                "section": f"{chunk.doc_title} -> {chunk.section_title}",
                "excerpt": chunk.content,
                "score": int(relevance["score"]),
                "match_count": int(relevance["match_count"]),
                "matched_terms": relevance["matched_terms"]
            })

    if not scored_results:
        return []

    # Keep only the candidate excerpts that match the highest number of distinct
    # query keywords. This avoids returning excerpts that only share a weaker subset.
    max_matches = max(item["match_count"] for item in scored_results)
    best_match_candidates = [
        item for item in scored_results if item["match_count"] == max_matches
    ]

    # Sort remaining candidates by overall score (highest relevance first).
    best_match_candidates.sort(key=lambda item: item["score"], reverse=True)

    return best_match_candidates[:top_k]


def run_demo() -> None:
    """Execute demonstration queries showcasing search behavior and limitations."""
    print("=" * 75)
    print("NovaMart Assistant - Local Policy Search Demo")
    print("=" * 75)

    test_cases = [
        {
            "category": "1. Specific Answerable Question (Return Time Window)",
            "query": "How many days do I have to return an item?",
            "top_k": 1,
            "note": "Shows only the 'Return Window' excerpt containing the return deadline (excludes 'Exchange Eligibility')."
        },
        {
            "category": "2. Specific Answerable Question (Payment Methods)",
            "query": "Can I pay using Apple Pay or credit cards?",
            "top_k": 1,
            "note": "Expects the excerpt discussing accepted checkout payment options."
        },
        {
            "category": "3. Keyword Overlap That Does NOT Establish an Answer (Bicycle Warranty)",
            "query": "Does the standard warranty cover a damaged bicycle?",
            "top_k": 1,
            "note": "Crucial limitation example: keywords 'standard', 'warranty', and 'cover' match Warranty Exclusions, but the excerpt addresses electronics and appliances, leaving bicycle coverage unestablished."
        },
        {
            "category": "4. Completely Unrelated Question (No Evidence)",
            "query": "Does NovaMart sell rocket tickets to Mars?",
            "top_k": 2,
            "note": "Expects 0 results (empty list) because no matching evidence exists."
        }
    ]

    for case in test_cases:
        query = case["query"]
        top_k = case.get("top_k", 2)
        print(f"\n[{case['category']}]")
        print(f"Query: \"{query}\"")
        print(f"Case Context: {case['note']}")

        results = search_policies(query, top_k=top_k)

        if results:
            print(f"Status: Found {len(results)} excerpt(s):")
            for idx, res in enumerate(results, 1):
                print(f"  Result {idx}:")
                print(f"    - Source: {res['source']}")
                print(f"    - Section: {res['section']}")
                print(f"    - Matched Keywords: {res['matched_terms']}")
                print(f"    - Relevance Score: {res['score']}")
                print(f"    - Excerpt: {res['excerpt'][:170]}...")
            if "NOT Establish an Answer" in case["category"]:
                print("  [Limitation Reminder]: Keyword overlap found matching terms ('cover', 'standard', 'warranty'),")
                print("  but the excerpt does NOT establish whether bicycles are covered. Keyword search matches words, not semantic answers.")
        else:
            print("Status: No relevant evidence found. Returned 0 results.")


if __name__ == "__main__":
    run_demo()
