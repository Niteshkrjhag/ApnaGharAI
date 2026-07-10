from models import CalculationRequest, AgentDebateResult, MathEngineResult

def run_math_engine(request: CalculationRequest, debate: AgentDebateResult) -> MathEngineResult:
    base = request.projectBaseline
    logistics = request.logisticsAndGeography

    # Step 1: Initial Load Penalty (P_initial)
    # L_dist * Fuel Rate
    logistics_cost = logistics.lastMileDistanceKm * debate.fuelRatePerKm
    
    # W_risk * C_delay
    weather_cost = logistics.monsoonDisruptionMonths * debate.dailyIdleLaborCost * 30 # Approx 30 days per month of delay

    # Monopoly_Material_Share * C_base * Premium_Rate
    monopoly_cost = debate.monopolyMaterialShare * base.currentBaseCost * debate.monopolyPremiumRate

    # If DIY Labor circuit breaker is hit, we assume weather_cost (labor delay) is heavily mitigated
    if request.siteAndMarketFriction.isDIYLabor:
        weather_cost = 0

    # If On-Site Sourcing circuit breaker is hit, logistics cost is nullified
    if request.siteAndMarketFriction.onSiteResourceSourcing:
        logistics_cost = 0

    p_initial = logistics_cost + weather_cost + monopoly_cost

    # Step 2: Location-Adjusted Base (C_adj)
    c_adj = base.currentBaseCost + p_initial

    # Step 3: 5-Year Escalation (E)
    # E = C_adj * (1 + Regional_CCI)^n
    n = base.timelineYears
    e = c_adj * ((1 + debate.regionalCCIInflation) ** n)

    # Step 4: Final Target Fund (F_target)
    # F_target = E + Current_Event_Buffer
    current_event_buffer = debate.currentEventBufferCost
    
    # Circuit Breaker: Indigenous Materials
    if request.siteAndMarketFriction.primaryMaterialType == "MUD_BAMBOO":
        current_event_buffer = 0  # Global steel/cement spikes ignored

    f_target = e + current_event_buffer

    # Step 5: Sunk-Capital Monthly Savings Goal (S_monthly)
    months = n * 12
    s_monthly = (f_target / months) * (1 + debate.harvestVolatilityBuffer) if months > 0 else 0

    return MathEngineResult(
        initialLoadPenalty=round(p_initial, 2),
        adjustedBase=round(c_adj, 2),
        escalatedCost=round(e, 2),
        finalTargetFund=round(f_target, 2),
        monthlySavingsTarget=round(s_monthly, 2)
    )
