import json, logging
from contractor_metrics import build_scorecard
from utils.gpt_call import call_gpt_model

def suggest_best_contractor(job_dict: dict,
                             contractors: list,
                             jobs_path="logs/jobs.json",
                             feedback_path="logs/feedback.json") -> str:
    contractor_profiles = []
    for cid in contractors:
        profile = build_scorecard(cid, jobs_path, feedback_path)
        profile["email"] = cid
        contractor_profiles.append(profile)

    system_prompt = '''
    You are an assignment coordinator for a maintenance company.
    
    Given a job and a list of contractors (with ratings, jobs completed, and feedback),
    choose the best match.
    
    Output ONLY: { "chosen_contractor": "email@example.com" }
    '''

    gpt_input = {
        "job": job_dict,
        "contractors": contractor_profiles
    }

    prompt = system_prompt + "\n\n" + json.dumps(gpt_input)
    try:
        response = call_gpt_model(prompt)
        parsed = json.loads(response)
        return parsed.get("chosen_contractor")
    except Exception as e:
        logging.error(f"GPT contractor selection failed: {e}")
        if not isinstance(parsed, dict) or "chosen_contractor" not in parsed:
            logging.warning("GPT returned invalid contractor suggestion format.")
        return None
