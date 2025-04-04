# SS3_Echo: Tenant GPT Chat + Incident Summary

This superstructure enables tenants to report incidents via a GPT-powered interface.

## How to Run
```bash
pip install -r requirements.txt
streamlit run ss3_echo_app.py
```

## Entry Point
Call `run_echo()` from your Streamlit router.

## Output
Creates JSON incident summaries in `/incidents/` matching schema/incident_schema.json