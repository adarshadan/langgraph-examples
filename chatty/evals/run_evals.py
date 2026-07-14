import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import backend
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

judge_llm = ChatGroq(model=os.getenv('GROQ_MODEL'), api_key=os.getenv('GROQ_API_KEY'), temperature=0)

def get_response(user_input: str) -> str:
    result = backend.chat_session({'messages': [HumanMessage(user_input)]})
    return result['messages'][0].content

def llm_judge(response: str, criteria: str) -> tuple[bool, str]:
    prompt = (
        f"Response to evaluate:\n{response}\n\n"
        f"Criteria: {criteria}\n\n"
        "Does the response meet the criteria? Reply with exactly 'PASS' or 'FAIL' "
        "on the first line, then a one-sentence reason on the second line."
    )
    result = judge_llm.invoke(prompt).content.strip()
    lines = result.splitlines()
    verdict = lines[0].strip().upper()
    reason = lines[1] if len(lines) > 1 else ''
    return verdict == 'PASS', reason

def run():
    with open(os.path.join(os.path.dirname(__file__), 'golden_dataset.json')) as f:
        cases = json.load(f)

    failures = []
    for case in cases:
        response = get_response(case['input'])
        check = case['check']

        if check == 'must_mention':
            passed = case['expected'].lower() in response.lower()
            reason = 'expected text found' if passed else f"'{case['expected']}' not found in response"
        elif check == 'must_not_mention':
            passed = case['expected'].lower() not in response.lower()
            reason = 'as expected, not mentioned' if passed else f"unexpectedly mentioned '{case['expected']}'"
        elif check == 'llm_judge':
            passed, reason = llm_judge(response, case['criteria'])
        else:
            raise ValueError(f"Unknown check type: {check}")

        status = 'PASS' if passed else 'FAIL'
        print(f"[{status}] {case['id']}: {reason}")
        if not passed:
            failures.append(case['id'])

    print(f"\n{len(cases) - len(failures)}/{len(cases)} passed")
    if failures:
        print(f"Failed: {failures}")
        sys.exit(1)

if __name__ == '__main__':
    run()