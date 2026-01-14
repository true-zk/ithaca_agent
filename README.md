# Ithaca

Ithaca is an LLM‑agent–driven automation platform for Meta Ads that can automatically research products, generate marketing plans, create campaigns, and iteratively optimize performance.

## Project Structure

### Core directory

#### `/ithaca/` – main code

**Key files:**

- `main.py` – Minimal entry point used in examples/tests for running a demo workflow.
- `settings.py` – Global configuration, including API keys, OAuth callback URL and system settings.
- `utils.py` – Common utility helpers.
- `logger.py` – Central logging setup.

#### `/ithaca/agents/` – AI agent modules

**Core files:**

- `research_agent.py` – Research agent that uses web search tools to understand the product and market, returning keywords, image URLs and a research summary.
- `plan_agent.py` – Plan agent that turns research results and account information into a full Meta Ads marketing plan (campaign, ad sets, creatives, ads) via tools.
- `update_agent.py` – Update agent that periodically adjusts the running plan based on performance data.
- `summary_agent.py` – Summary agent that converts a finished plan into a structured marketing history.
- `base.py`, `agent_factory.py` – Base abstractions and factories for building and composing agents.

#### `/ithaca/tools/` – Tool integration modules

**General tools:**

- `webtools.py` – Web content fetching and analysis utilities.
- `random.py` – Random helper utilities used in experiments and tests.

**Meta API integration (`/meta_api/`):**

- `meta_ads_api.py` – Core Meta Ads API client.
- `utils.py` – API helper functions, error handling and shared utilities.
- `meta_ads_*.py` – Functional modules wrapping specific Meta Ads features:
  - `meta_ads_adaccount.py` – Ad account management.
  - `meta_ads_campaign.py` – Campaign management.
  - `meta_ads_adset.py` – Ad set management.
  - `meta_ads_ad.py` – Ad management.
  - `meta_ads_creative.py` – Creative management.
  - `meta_ads_ad_image.py` – Image upload and management.
  - `meta_ads_targeting.py` – Audience targeting.
  - `meta_ads_insights.py` – Insights and reporting.
  - `meta_ads_budget.py` – Budget helpers.
  - `meta_ads_page.py` – Page management.
  - `meta_ads_audience_estimate.py` – Audience size estimation.

#### `/ithaca/llms/` – LLM integration

- `base.py` – Base abstraction for calling LLMs.
- `gemini.py` – Google Gemini integration used by the agents.

#### `/ithaca/oauth/` – OAuth modules

- `auth.py` – Meta API OAuth 2.0 authentication manager (login, token storage and refresh).
- `callback_server.py` – Local callback server to complete the OAuth flow.

#### `/ithaca/workflow/` – Workflow modules

- `base.py` – Base workflow abstraction with session handling.
- `data_type.py` – Typed data models for Meta Ads entities, marketing plans, workflow status and history.
- `demo_workflow.py` – Demo end‑to‑end workflow that combines agents and tools to run a full marketing loop for a single product.

#### `/ithaca/skills/`

- `create_adsets.txt` – Prompt/skill template used by the plan agent when creating ad sets.

### Other directories

- `auxiliary/` – Helper server for Meta Ads requirements.
- `devdocs/` – Internal design notes, images and documentation for development.
- `test/` – Pytest test cases and executable examples for agents, tools, workflows and OAuth.
- `bk/` – Legacy/backup versions of early modules kept for reference.

## Features

### 🤖 Intelligent marketing plan generation

- Automatically researches products based on basic information (name, URL, images).
- Generates structured Meta Ads marketing plans, including campaign, ad sets, creatives and ads.
- Uses Meta Ads API tools to create and execute campaigns on real ad accounts.

### 📊 Campaign performance evaluation and optimization

- Collects performance metrics through Meta Ads insights tools.
- Evaluates the effectiveness of marketing plans and summarizes key results.
- Provides structured logs and histories that can be used for manual or automated optimization.

### ⏰ Automated workflow orchestration

- The demo workflow drives a full loop:
  - Account info retrieval.
  - Research → plan → execute.
  - Periodic updates to the plan via the update agent.
  - Final summarization into `MarketingHistory`.
- Scheduling is handled inside the workflow (e.g. epoch‑based scheduling in `DemoWorkFlow`).

### 🔐 Secure authentication

- Meta API OAuth 2.0 authentication.
- Automatic access token management and refresh.
- Safe local storage of tokens for development.

## Getting Started

### 1. Configure settings

Core configuration lives in `ithaca/settings.py`:

- `META_APP_ID` – Your Meta app ID.
- `META_APP_SECRET` – Your Meta app secret.
- `CALLBACK_SERVER_URL` – OAuth callback URL (often a local URL during development).
- `GEMINI_API_KEY` – Your Google Gemini API key.

Replace the placeholder values with your own credentials and keep them out of version control.

### 2. Install dependencies

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

If you do not have a `requirements.txt` yet, install the libraries used in the codebase (for example `pydantic`, `google-genai`, `requests`, `pytest`, etc.).

### 3. Authenticate with Meta Ads

Before running workflows that call the Meta Ads API, make sure you have a valid access token.
One convenient way is to run the demo workflow test, which will trigger the OAuth flow if no token is cached:

```bash
python test/test_workflow.py
```

Follow the browser prompts to log in and authorize the app.

### 4. Run the demo workflow in code

You can also instantiate and run the demo workflow directly:

```python
from ithaca.workflow.data_type import MarketingInitInput
from ithaca.workflow.demo_workflow import DemoWorkFlow

wf = DemoWorkFlow(
    marketing_input=MarketingInitInput(
        product_name="Smart Watch",
        product_url="https://example.com",
        product_picture_urls=["https://example.com/watch.png"],
    )
)

print(wf)
plan = wf.run()
```

This runs the full research → plan → execute → update loop for the given product according to the schedule defined in `DemoWorkFlow`.

## Architecture

```text
User / product input → Workflow → Agents → Meta Ads tools → Insights → Plan updates → (optional) History
```

1. **Workflow layer** – Orchestrates end‑to‑end marketing flows, including scheduling and session state.
2. **Agent layer** – Research, plan, update and summary agents that reason with LLMs and tools.
3. **Tool layer** – Concrete integrations with Meta Ads APIs, web search and other utilities.
4. **Data layer** – Pydantic models representing inputs, Meta Ads entities, marketing plans and histories.
