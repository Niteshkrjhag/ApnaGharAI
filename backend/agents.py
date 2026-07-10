"""
True Multi-Agent Debate (MAD) system for Apna Ghar Hoga.

Architecture:
  Phase 1 — 3 parallel agents (asyncio.gather):
    - MacroAgent:   Global/national commodity shocks  → proposedEventBuffer, monopolyPremiumRate
    - RegionalAgent: State-level logistics & CCI      → fuelRate, laborCost, inflation
    - MicroAgent:   Hyper-local + circuit breakers    → monopolyShare, harvestBuffer, vetoes

  Phase 2 — JudgeAgent:
    - Receives all 3 proposals
    - Applies Micro vetoes
    - Writes the final calibrated JSON + plain-English Markdown transcript
"""

import os
import json
import asyncio
import requests
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun
from models import (
    CalculationRequest, AgentDebateResult,
    MacroAgentProposal, RegionalAgentProposal, MicroAgentProposal
)

# ── Search Tool ──
search_tool = DuckDuckGoSearchRun()

def _search_safe(query: str) -> str:
    try:
        return search_tool.run(query)
    except Exception:
        return "Search unavailable — use standard regional estimates."

# ── Ollama Config ──
raw_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
clean_base_url = raw_base_url.rstrip("/")
if clean_base_url.endswith("/v1"):
    clean_base_url = clean_base_url[:-3]
OLLAMA_MODEL = "gpt-oss:120b"


def _ollama_sync(system_prompt: str, user_prompt: str) -> dict:
    """Blocking Ollama call. Returns a parsed dict."""
    api_key = os.getenv("OLLAMA_API_KEY", "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
    }
    resp = requests.post(f"{clean_base_url}/api/chat", headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    content = resp.json()["message"]["content"]
    if content.strip().startswith("```"):
        content = content.strip().lstrip("`").lstrip("json").strip().rstrip("`").strip()
    return json.loads(content)


def _openrouter_sync(system_prompt: str, user_prompt: str) -> dict:
    """Blocking OpenRouter call. Returns a parsed dict."""
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY", "dummy"),
        model="meta-llama/llama-3.1-8b-instruct:free",
        temperature=0,
    )
    resp = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    content = resp.content.strip()
    if content.startswith("```"):
        content = content.lstrip("`").lstrip("json").strip().rstrip("`").strip()
    return json.loads(content)


async def _llm(system_prompt: str, user_prompt: str) -> dict:
    """Async LLM call: Ollama → OpenRouter fallback."""
    def _try_ollama():
        result = _ollama_sync(system_prompt, user_prompt)
        # Reject if all numeric values are zero (parsing failure)
        numeric_vals = [v for v in result.values() if isinstance(v, (int, float))]
        if numeric_vals and all(v == 0.0 for v in numeric_vals):
            raise ValueError("Ollama returned all-zero numeric values")
        return result

    try:
        return await asyncio.to_thread(_try_ollama)
    except Exception:
        pass  # Fall through to OpenRouter

    return await asyncio.to_thread(_openrouter_sync, system_prompt, user_prompt)


# ────────────────────────────────────────────────────────────
#  REALITY CLAMPS  (LLMs sometimes confuse units/scale)
#  These enforce hard physical limits from real-world knowledge.
# ────────────────────────────────────────────────────────────

def _clamp_macro(d: dict) -> dict:
    """Event buffer: ₹10k–₹10L. Premium rate: 10%–35%."""
    buf = float(d.get("proposedEventBuffer", 100000))
    # AI sometimes returns in thousands or lakhs — normalise
    if buf < 1_000:        buf *= 1_000      # likely returned in thousands
    if buf > 1_000_000:   buf  = 200_000    # cap at ₹10L; beyond is hallucination
    d["proposedEventBuffer"] = round(buf, 2)

    prem = float(d.get("proposedMonopolyPremiumRate", 0.20))
    if prem > 1:           prem /= 100       # AI returned 20 instead of 0.20
    d["proposedMonopolyPremiumRate"] = max(0.10, min(0.35, prem))
    return d


def _clamp_regional(d: dict) -> dict:
    """Fuel: ₹8–₹120/km. Labor: ₹250–₹5000/day. Inflation: 3%–20%."""
    fuel = float(d.get("proposedFuelRatePerKm", 30))
    if fuel < 1:           fuel *= 100       # returned as fraction
    if fuel > 500:         fuel /= 10        # returned in paise or 10x
    d["proposedFuelRatePerKm"] = max(8.0, min(120.0, round(fuel, 2)))

    labor = float(d.get("proposedDailyIdleLaborCost", 500))
    if labor > 50_000:     labor /= 100      # returned in paise or 100x
    if labor > 50_000:     labor  = 600      # still bad — hard reset
    d["proposedDailyIdleLaborCost"] = max(250.0, min(5_000.0, round(labor, 2)))

    infl = float(d.get("proposedRegionalInflation", 0.07))
    if infl > 1:           infl /= 100       # AI returned 7 instead of 0.07
    d["proposedRegionalInflation"] = max(0.03, min(0.20, round(infl, 4)))
    return d


def _clamp_micro(d: dict) -> dict:
    """Monopoly share: AI determines (0 to 1). Harvest buffer: AI determines (0 to 1)."""
    share = float(d.get("proposedMonopolyShare", 0.50))
    if share > 1:          share /= 100      # returned as 62 not 0.62
    # Dynamic fix: allow wide range, but prevent extreme hallucination (0.30 to 0.85)
    d["proposedMonopolyShare"] = max(0.30, min(0.85, round(share, 3)))

    harv = float(d.get("proposedHarvestBuffer", 0))
    if harv > 1:           harv /= 100
    # Dynamic fix: cap at 40% volatility to prevent budget destruction
    d["proposedHarvestBuffer"] = max(0.0, min(0.40, round(harv, 3)))
    return d


# ════════════════════════════════════════════════════════════
#  AGENT 1: MACRO-SHOCK ANALYST
# ════════════════════════════════════════════════════════════
async def run_macro_agent(location: str, currency: str, material: str) -> MacroAgentProposal:
    """
    Focus: Global & national commodity shocks.
    Proposes: currentEventBufferCost, monopolyPremiumRate
    """
    # Run 2 targeted searches in parallel
    steel_data, oil_data = await asyncio.gather(
        asyncio.to_thread(_search_safe, "Current steel and cement price trends forecast India"),
        asyncio.to_thread(_search_safe, "Crude oil price forecast impact on India economy"),
    )

    system = f"""You are the Macro-Shock Analyst for a home construction cost estimator.
Analyze GLOBAL and NATIONAL economic conditions affecting building material costs in India.

Live Market Data:
Steel/Cement Market: {steel_data}
Oil & Diesel Market: {oil_data}

Project: Building in {location} using {material}.
Currency: {currency}

Based on ONLY the data above, propose realistic buffers.

Return ONLY a JSON object:
{{
  "proposedEventBuffer": <flat one-time buffer in {currency} for current commodity shocks, e.g. 150000>,
  "proposedMonopolyPremiumRate": <decimal 0.15 to 0.25, markup due to supplier concentration>,
  "reasoning": "<2 sentences: what global trends justify your numbers>"
}}"""

    raw = await _llm(system, "Propose your buffers based on the data.")
    raw = _clamp_macro(raw)
    return MacroAgentProposal(**raw)


# ════════════════════════════════════════════════════════════
#  AGENT 2: REGIONAL LOGISTICS SPECIALIST
# ════════════════════════════════════════════════════════════
async def run_regional_agent(
    location: str, currency: str, last_mile_km: float, monsoon_months: int
) -> RegionalAgentProposal:
    """
    Focus: State-level logistics, weather disruptions, labor rates.
    Proposes: fuelRatePerKm, dailyIdleLaborCost, regionalCCIInflation
    """
    fuel_data, cci_data, weather_data = await asyncio.gather(
        asyncio.to_thread(_search_safe, f"What is the current diesel price and truck transport rate in {location}, India?"),
        asyncio.to_thread(_search_safe, f"Current inflation rate and construction cost index in {location}, India"),
        asyncio.to_thread(_search_safe, f"Average daily wage for construction labor in {location}, India"),
    )

    system = f"""You are the Regional Logistics Specialist for a home construction cost estimator.
Analyze STATE-LEVEL conditions in {location}, India.

Live Data:
Fuel/Transport Costs: {fuel_data}
Construction Inflation (CCI): {cci_data}
Monsoon & Weather Impact: {weather_data}

Context: Site is {last_mile_km} km from highway. Monsoon disrupts {monsoon_months} months/year.
Currency: {currency}

Return ONLY a JSON object:
{{
  "proposedFuelRatePerKm": <cost in {currency} per km for a loaded material truck in this state>,
  "proposedDailyIdleLaborCost": <daily wage in {currency} paid to idle workers during rain stoppages>,
  "proposedRegionalInflation": <annual construction inflation as decimal e.g. 0.07 for 7%>,
  "reasoning": "<2 sentences: which regional factors set these numbers>"
}}"""

    raw = await _llm(system, "Propose your regional logistics values.")
    raw = _clamp_regional(raw)
    return RegionalAgentProposal(**raw)


# ════════════════════════════════════════════════════════════
#  AGENT 3: VILLAGE MICRO-ANALYST
# ════════════════════════════════════════════════════════════
async def run_micro_agent(
    location: str, currency: str, income_type: str, local_suppliers: int,
    material: str, is_diy: bool, on_site_sourcing: bool,
    communal_risk: str, savings_vehicle: str,
) -> MicroAgentProposal:
    """
    Focus: Hyper-local market realities + applying circuit breaker vetoes.
    Proposes: monopolyShare, harvestBuffer, and boolean vetoes.
    """
    monopoly_data, harvest_data = await asyncio.gather(
        asyncio.to_thread(_search_safe, f"Rural building material supply challenges in {location}, India"),
        asyncio.to_thread(_search_safe, f"Major agricultural harvest seasons and rural income cycles in {location}, India"),
    )

    system = f"""You are the Village Micro-Analyst for a home construction cost estimator.
Analyze HYPER-LOCAL conditions and apply CIRCUIT BREAKER VETOES.

Live Data:
Local Supplier Competition: {monopoly_data}
Harvest/Income Cycles: {harvest_data}

Project context:
- Location: {location}
- Income: {income_type} | Suppliers nearby: {local_suppliers}
- Material: {material}
- Family doing own labor (DIY): {is_diy}
- Sourcing materials from own land: {on_site_sourcing}
- Community financial obligations: {communal_risk} risk
- Savings method: {savings_vehicle}
Currency: {currency}

MANDATORY CIRCUIT BREAKER RULES:
1. If material is MUD_BAMBOO → vetoEventBuffer = true (no steel/cement shock applies)
2. If is_diy is true → vetoLaborCost = true (family absorbs delay)
3. If on_site_sourcing is true → vetoLogistics = true (no trucking for sand/soil)
4. Analyze the searched data and intelligently assign `proposedHarvestBuffer` as a decimal between 0.0 and 1.0 based on how severe the agricultural harvest income volatility is in this region. (Hint: >0.30 is extremely severe).
5. Analyze local supplier competition data. Assign `proposedMonopolyShare` as a decimal between 0.0 and 1.0 reflecting how much pricing power local monopolies hold. (Hint: >0.80 implies a near-total cartel).

Return ONLY a JSON object:
{{
  "proposedMonopolyShare": <decimal 0.0 to 1.0 based on your honest analysis of the data>,
  "proposedHarvestBuffer": <decimal 0.0 to 1.0 based on your honest analysis of the data>,
  "vetoEventBuffer": <true or false>,
  "vetoLaborCost": <true or false>,
  "vetoLogistics": <true or false>,
  "reasoning": "<2 sentences: which local conditions and vetoes you applied>"
}}"""

    raw = await _llm(system, "Analyze local conditions and apply circuit breakers.")
    raw = _clamp_micro(raw)
    return MicroAgentProposal(**raw)


# ════════════════════════════════════════════════════════════
#  AGENT 4: JUDGE AGENT (SYNTHESIZER)
# ════════════════════════════════════════════════════════════
async def run_judge_agent(
    macro: MacroAgentProposal,
    regional: RegionalAgentProposal,
    micro: MicroAgentProposal,
    request: CalculationRequest,
) -> AgentDebateResult:
    """
    The Judge receives all 3 proposals, applies vetoes, and produces
    the final calibrated output with a plain-English Markdown transcript.
    """
    currency = request.projectBaseline.baseCurrency

    system = f"""You are the Judge Agent for Apna Ghar Hoga.
Three specialist analysts have each submitted their proposals. Synthesize them into the final agreed values.

━━━ MACRO AGENT (Global Trends) ━━━
Proposed Event Buffer: {currency} {macro.proposedEventBuffer:,.0f}
Proposed Monopoly Premium: {macro.proposedMonopolyPremiumRate * 100:.0f}%
Their Reasoning: {macro.reasoning}

━━━ REGIONAL AGENT (State Logistics) ━━━
Proposed Fuel Rate: {currency} {regional.proposedFuelRatePerKm}/km
Proposed Daily Labor Cost: {currency} {regional.proposedDailyIdleLaborCost}/day
Proposed Annual Inflation: {regional.proposedRegionalInflation * 100:.1f}%
Their Reasoning: {regional.reasoning}

━━━ MICRO AGENT (Village Reality) ━━━
Proposed Monopoly Share: {micro.proposedMonopolyShare * 100:.0f}%
Harvest Volatility Buffer: {micro.proposedHarvestBuffer}
VETO Event Buffer: {micro.vetoEventBuffer}
VETO Labor Cost: {micro.vetoLaborCost}
VETO Logistics: {micro.vetoLogistics}
Their Reasoning: {micro.reasoning}

YOUR RULES:
1. Accept Regional Agent's fuel rate, labor cost, and inflation (they have the local data).
2. Accept Macro Agent's monopoly premium rate.
3. Accept Micro Agent's monopoly share and harvest buffer.
4. If vetoEventBuffer=true → set currentEventBufferCost to 0 (override Macro Agent).
5. If vetoLaborCost=true → set dailyIdleLaborCost to 0 (override Regional Agent).
6. Write the debateTranscript as friendly Markdown. Show the real tension between agents:
   "The global market expert warned about X, but the village expert pointed out Y, so we decided Z."
   Use ## heading + bullet points. Write for a homeowner with no finance background.

Return ONLY a JSON object:
{{
  "fuelRatePerKm": <from Regional Agent>,
  "dailyIdleLaborCost": <Regional Agent value, OR 0 if vetoLaborCost>,
  "monopolyMaterialShare": <from Micro Agent>,
  "monopolyPremiumRate": <from Macro Agent>,
  "regionalCCIInflation": <from Regional Agent>,
  "currentEventBufferCost": <Macro Agent value, OR 0 if vetoEventBuffer>,
  "harvestVolatilityBuffer": <from Micro Agent>,
  "debateTranscript": "<Markdown string showing the agent debate and final decision>"
}}"""

    raw = await _llm(system, "Synthesize all proposals and produce the final JSON.")

    # ── Final safety clamp (last line of defence) ──────────────────────
    fuel = float(raw.get("fuelRatePerKm", 30))
    if fuel > 1:    fuel = max(8.0,  min(120.0, fuel if fuel < 500 else fuel / 10))
    raw["fuelRatePerKm"] = round(fuel, 2)

    labor = float(raw.get("dailyIdleLaborCost", 500))
    if labor > 50_000: labor = min(5_000, labor / 100)
    raw["dailyIdleLaborCost"] = max(0.0, min(5_000.0, round(labor, 2)))

    infl = float(raw.get("regionalCCIInflation", 0.07))
    if infl > 1:    infl /= 100
    raw["regionalCCIInflation"] = max(0.03, min(0.20, round(infl, 4)))

    buf = float(raw.get("currentEventBufferCost", 100_000))
    if buf > 1_000_000: buf = 200_000
    raw["currentEventBufferCost"] = max(0.0, round(buf, 2))

    mshare = float(raw.get("monopolyMaterialShare", 0.50))
    if mshare > 1:  mshare /= 100
    raw["monopolyMaterialShare"] = max(0.30, min(0.85, round(mshare, 3)))

    mprem = float(raw.get("monopolyPremiumRate", 0.20))
    if mprem > 1:   mprem /= 100
    raw["monopolyPremiumRate"] = max(0.10, min(0.35, round(mprem, 3)))

    harv = float(raw.get("harvestVolatilityBuffer", 0))
    if harv > 1:    harv /= 100
    raw["harvestVolatilityBuffer"] = max(0.0, min(0.40, round(harv, 3)))
    # ────────────────────────────────────────────────────────────────────

    return AgentDebateResult(**raw)


# ════════════════════════════════════════════════════════════
#  ORCHESTRATION ENTRY POINT
# ════════════════════════════════════════════════════════════
async def run_multi_agent_debate(request: CalculationRequest) -> AgentDebateResult:
    """
    True parallel Multi-Agent Debate:

    Phase 1 — All 3 agents run simultaneously (asyncio.gather).
               Each agent does its own focused web searches in parallel too.

    Phase 2 — JudgeAgent synthesizes all proposals, applies vetoes,
               and writes a transparent Markdown transcript.
    """
    location = request.logisticsAndGeography.stateOrProvince
    currency = request.projectBaseline.baseCurrency
    material = request.siteAndMarketFriction.primaryMaterialType

    # ── Phase 1: 3 agents in parallel ──────────────────────
    macro_proposal, regional_proposal, micro_proposal = await asyncio.gather(
        run_macro_agent(location, currency, material),
        run_regional_agent(
            location, currency,
            request.logisticsAndGeography.lastMileDistanceKm,
            request.logisticsAndGeography.monsoonDisruptionMonths,
        ),
        run_micro_agent(
            location, currency,
            request.householdEconomics.incomeStructureType,
            request.siteAndMarketFriction.localSupplierCount,
            material,
            request.siteAndMarketFriction.isDIYLabor,
            request.siteAndMarketFriction.onSiteResourceSourcing,
            request.householdEconomics.communalDependencyRisk,
            request.householdEconomics.savingsVehicleType,
        ),
    )

    # ── Phase 2: Judge synthesizes ─────────────────────────
    return await run_judge_agent(
        macro_proposal, regional_proposal, micro_proposal, request
    )
