from pydantic import BaseModel, Field
from typing import Optional

class ProjectBaseline(BaseModel):
    baseCurrency: str = Field(..., description="Currency code, e.g., INR")
    currentBaseCost: float = Field(..., description="Estimated current cost to build")
    timelineYears: int = Field(..., description="Years until build")
    targetSavingsMonthly: float = Field(..., description="Current monthly savings capacity")

class LogisticsAndGeography(BaseModel):
    stateOrProvince: str = Field(..., description="State or Region")
    lastMileDistanceKm: float = Field(..., description="Distance from main highway")
    monsoonDisruptionMonths: int = Field(..., description="Months of weather disruption per year")

class SiteAndMarketFriction(BaseModel):
    hasSecureOnSiteStorage: bool = Field(..., description="True if secure storage is available")
    localSupplierCount: int = Field(..., description="Number of local suppliers within radius")
    primaryMaterialType: str = Field("CONCRETE_STEEL", description="CONCRETE_STEEL, BRICK_MORTAR, MUD_BAMBOO, PREFAB_STEEL")
    isDIYLabor: bool = Field(False, description="True if family is doing the labor")
    onSiteResourceSourcing: bool = Field(False, description="True if sourcing materials on-site (soil/sand)")

class HouseholdEconomics(BaseModel):
    incomeStructureType: str = Field(..., description="SALARIED, HARVEST_DEPENDENT, or INFORMAL_WAGES")
    communalDependencyRisk: str = Field(..., description="LOW, MEDIUM, or HIGH")
    savingsVehicleType: str = Field(..., description="CASH_AT_HOME, GOLD, BANK, POST_OFFICE")

class CalculationRequest(BaseModel):
    projectBaseline: ProjectBaseline
    logisticsAndGeography: LogisticsAndGeography
    siteAndMarketFriction: SiteAndMarketFriction
    householdEconomics: HouseholdEconomics

class AgentDebateResult(BaseModel):
    fuelRatePerKm: float
    dailyIdleLaborCost: float
    monopolyMaterialShare: float
    monopolyPremiumRate: float
    regionalCCIInflation: float
    currentEventBufferCost: float
    harvestVolatilityBuffer: float
    debateTranscript: str

class MathEngineResult(BaseModel):
    initialLoadPenalty: float
    adjustedBase: float
    escalatedCost: float
    finalTargetFund: float
    monthlySavingsTarget: float

class CalculationResponse(BaseModel):
    debate_summary: str
    calculation: MathEngineResult

# ── Sub-Agent Proposal Models (True Multi-Agent Debate) ──

class MacroAgentProposal(BaseModel):
    """Proposal from the Macro-Shock Analyst (global/national trends)."""
    proposedEventBuffer: float
    proposedMonopolyPremiumRate: float
    reasoning: str

class RegionalAgentProposal(BaseModel):
    """Proposal from the Regional Logistics Specialist (state-level data)."""
    proposedFuelRatePerKm: float
    proposedDailyIdleLaborCost: float
    proposedRegionalInflation: float
    reasoning: str

class MicroAgentProposal(BaseModel):
    """Proposal from the Village Micro-Analyst (hyper-local + circuit breakers)."""
    proposedMonopolyShare: float
    proposedHarvestBuffer: float
    vetoEventBuffer: bool
    vetoLaborCost: bool
    vetoLogistics: bool
    reasoning: str
