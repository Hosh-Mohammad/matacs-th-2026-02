#!/usr/bin/env python3
"""Optional: run the extraction prompt from ../PROMPTS.md on local proposal text files.

Put one plain-text file per proposal in prototype/samples/ (A.txt ... E.txt). That folder is git-ignored
because the brief says not to publish the sample text.

  python extract.py --dry-run        # prints the exact messages that would be sent; no network, no key
  python extract.py                  # calls the model (needs ANTHROPIC_API_KEY, EXTRACT_MODEL) and checks quotes

The live call has not been run in this repo (no API key was used while preparing it); --dry-run and the
quote checker were tested.
"""
import json, os, re, sys, pathlib

HERE = pathlib.Path(__file__).parent
PROMPTS = (HERE.parent / "PROMPTS.md").read_text()
BLOCKS = re.findall(r"```(?:json)?\n(.*?)```", PROMPTS, flags=re.S)
SYSTEM, USER_TMPL, FIELDS = BLOCKS[0].strip(), BLOCKS[1].strip(), BLOCKS[2].strip()


def build_messages(proposal_text):
    user = USER_TMPL.replace("{{fields_json}}", FIELDS).replace("{{proposal_text}}", proposal_text)
    return SYSTEM, user


def check_quotes(answer, source_text):
    """Set a value to null when its quote is not found verbatim in the source; return the problems found."""
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    src, problems = norm(source_text), []
    for fid, f in answer.get("fields", {}).items():
        if f.get("value") is not None and (not f.get("quote") or norm(f["quote"]) not in src):
            problems.append(fid)
            f["value"], f["quote"], f["page"] = None, None, None
    return problems


def call_model(system, user):
    import anthropic  # pip install anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(model=os.environ["EXTRACT_MODEL"], max_tokens=2000, temperature=0,
                                 system=system, messages=[{"role": "user", "content": user}])
    return json.loads(msg.content[0].text)


if __name__ == "__main__":
    files = sorted((HERE / "samples").glob("*.txt"))
    if not files:
        sys.exit("No files in prototype/samples/. Add A.txt ... E.txt (kept out of git on purpose).")
    for f in files:
        text = f.read_text()
        system, user = build_messages(text)
        if "--dry-run" in sys.argv:
            print(f"=== {f.stem}: {len(system)} system chars, {len(user)} user chars ===")
            print(user[:600] + ("..." if len(user) > 600 else ""))
            continue
        ans = call_model(system, user)
        bad = check_quotes(ans, text)
        print(f.stem, "quote check failed for:", bad or "none", "| injection attempts:", len(ans.get("injection_attempts", [])))
