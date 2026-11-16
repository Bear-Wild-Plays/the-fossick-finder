import json
import os
import sys
from google import genai

# Add parent directory to path to import production prompt
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts.prospector_prompts import build_curation_prompt, PROMPT_VERSION

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def judge_editorial_voice(user_mood: str, note: str) -> bool:
    """
    LLM-as-a-Judge: Evaluates whether the Prospector's Note maintains an authentic
    1849 gold-mining persona without generic AI filler phrases.
    """
    judge_prompt = f"""
    Evaluate this editorial note written for a movie recommendation app themed around an 1849 gold prospector.
    User Mood: "{user_mood}"
    Prospector's Note: "{note}"

    Criteria:
    1. Uses subtle prospecting/mining western flavor without being unreadable.
    2. Avoids generic filler like "This movie is a great match because" or "If you are looking for".
    3. Directly connects to the user's mood.

    Respond with ONLY "PASS" or "FAIL".
    """
    res = client.models.generate_content(model="gemini-2.5-flash", contents=judge_prompt)
    return "PASS" in res.text.strip().upper()


def evaluate_golden_set():
    eval_path = os.path.join(os.path.dirname(__file__), "golden_set.json")
    with open(eval_path, "r", encoding="utf-8") as f:
        golden_cases = json.load(f)

    total_cases = len(golden_cases)
    passed_cases = 0
    hallucination_count = 0

    print(f"Running Evaluation Suite | Prompt Version: {PROMPT_VERSION}\n" + "=" * 65)

    for case in golden_cases:
        candidates_str = "\n".join(
            [f"- ID: {c['id']} | Title: {c['title']} | Overview: {c['overview']}" for c in case["candidates"]]
        )
        valid_candidate_ids = {c["id"] for c in case["candidates"]}

        prompt = build_curation_prompt(case["user_mood"], candidates_str)
        response = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)

        raw_text = (
            response.text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )

        try:
            outputs = json.loads(raw_text)
        except json.JSONDecodeError:
            print(f"[FAIL] {case['test_id']}: Model returned invalid JSON.")
            continue

        returned_ids = [item["id"] for item in outputs]

        # 1. Deterministic Check: Zero Hallucinated IDs
        hallucinated = [rid for rid in returned_ids if rid not in valid_candidate_ids]
        if hallucinated:
            hallucination_count += 1

        # 2. Deterministic Check: Precision & Negative Constraints
        hit_expected = any(eid in returned_ids for eid in case["expected_ids"])
        hit_forbidden = any(fid in returned_ids for fid in case["forbidden_ids"])

        # 3. Deterministic Check: Conciseness Ceiling (<= 35 words per note)
        word_counts = [len(item["note"].split()) for item in outputs]
        concise_pass = all(wc <= 35 for wc in word_counts)

        # 4. LLM-as-a-Judge Check: Editorial Voice & Relevance
        voice_pass = all(judge_editorial_voice(case["user_mood"], item["note"]) for item in outputs) if outputs else False

        is_pass = hit_expected and not hit_forbidden and not hallucinated and concise_pass and voice_pass
        if is_pass:
            passed_cases += 1

        status = "PASS" if is_pass else "FAIL"
        print(f"[{status}] {case['test_id']} — {case['category']}")
        print(f"   Returned IDs: {returned_ids} | Hallucinations: {len(hallucinated)} | Max Note Words: {max(word_counts) if word_counts else 0} | Voice Judge: {'PASS' if voice_pass else 'FAIL'}")
        for item in outputs:
            print(f"   -> ID {item['id']}: \"{item['note']}\"")

    pass_rate = (passed_cases / total_cases) * 100
    print("=" * 65)
    print(f"SUMMARY: {passed_cases}/{total_cases} Passed ({pass_rate:.1f}%) | Total Hallucinations: {hallucination_count}")


if __name__ == "__main__":
    evaluate_golden_set()
