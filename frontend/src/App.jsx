import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

const LOADING_MESSAGES = [
  'Macro Agent — scanning global material prices...',
  'Regional Agent — reading fuel & inflation for your state...',
  'Village Agent — mapping your local market conditions...',
  'Judge Agent — resolving conflicts across all three proposals...',
  'Writing your personalised budget summary...',
]

// ─── Progress bar ──────────────────────────────────────────────
function ProgressBar({ step }) {
  const pct = step === 1 ? 10 : step === 2 ? 55 : 100
  return (
    <div className="progress-track">
      <div className="progress-fill" style={{ width: `${pct}%` }} />
    </div>
  )
}

// ─── Material tile with visual metaphor ───────────────────────
function MaterialTile({ icon, name, tag, selected, onClick }) {
  return (
    <button
      type="button"
      className={`mat-tile${selected ? ' mat-tile--on' : ''}`}
      onClick={onClick}
    >
      <span className="mat-icon" aria-hidden="true">{icon}</span>
      <span className="mat-name">{name}</span>
      <span className="mat-tag">{tag}</span>
    </button>
  )
}

// ─── Generic choice pill ───────────────────────────────────────
function Pill({ label, sub, selected, onClick }) {
  return (
    <button
      type="button"
      className={`pill${selected ? ' pill--on' : ''}`}
      onClick={onClick}
    >
      <span className="pill-label">{label}</span>
      {sub && <span className="pill-sub">{sub}</span>}
    </button>
  )
}

// ─── Toggle row ────────────────────────────────────────────────
function ToggleRow({ label, hint, checked, onClick }) {
  return (
    <button type="button" className={`toggle-row${checked ? ' toggle-row--on' : ''}`} onClick={onClick}>
      <div className="toggle-text">
        <span className="toggle-label">{label}</span>
        <span className="toggle-hint">{hint}</span>
      </div>
      <div className={`toggle-knob${checked ? ' toggle-knob--on' : ''}`}>
        <div className="toggle-thumb" />
      </div>
    </button>
  )
}

// ─── App ───────────────────────────────────────────────────────
function App() {
  const [step, setStep]               = useState(0)
  const [loading, setLoading]         = useState(false)
  const [loadingMsg, setLoadingMsg]   = useState(LOADING_MESSAGES[0])
  const [error, setError]             = useState(null)
  const [result, setResult]           = useState(null)
  const [assumptions, setAssumptions] = useState(null)

  const [formData, setFormData] = useState({
    baseCurrency: 'INR',
    currentBaseCost: 1500000,
    timelineYears: 3,
    targetSavingsMonthly: 15000,
    stateOrProvince: 'Maharashtra',
    lastMileDistanceKm: 15,
    monsoonDisruptionMonths: 3,
    hasSecureOnSiteStorage: false,
    localSupplierCount: 2,
    primaryMaterialType: 'CONCRETE_STEEL',
    isDIYLabor: false,
    onSiteResourceSourcing: false,
    incomeStructureType: 'SALARIED',
    communalDependencyRisk: 'LOW',
    savingsVehicleType: 'BANK',
  })

  const pick   = (name, value) => setFormData(p => ({ ...p, [name]: value }))
  const toggle = (name)        => setFormData(p => ({ ...p, [name]: !p[name] }))

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(p => ({
      ...p,
      [name]: type === 'checkbox' ? checked
            : type === 'number'   ? Number(value)
            : value
    }))
  }

  const handleAssumptionChange = (e) => {
    const { name, value } = e.target
    setAssumptions(p => ({ ...p, [name]: Number(value) }))
  }

  const getPayload = () => ({
    projectBaseline: {
      baseCurrency:         formData.baseCurrency,
      currentBaseCost:      formData.currentBaseCost,
      timelineYears:        formData.timelineYears,
      targetSavingsMonthly: formData.targetSavingsMonthly,
    },
    logisticsAndGeography: {
      stateOrProvince:         formData.stateOrProvince,
      lastMileDistanceKm:      formData.lastMileDistanceKm,
      monsoonDisruptionMonths: formData.monsoonDisruptionMonths,
    },
    siteAndMarketFriction: {
      hasSecureOnSiteStorage: formData.hasSecureOnSiteStorage,
      localSupplierCount:     formData.localSupplierCount,
      primaryMaterialType:    formData.primaryMaterialType,
      isDIYLabor:             formData.isDIYLabor,
      onSiteResourceSourcing: formData.onSiteResourceSourcing,
    },
    householdEconomics: {
      incomeStructureType:    formData.incomeStructureType,
      communalDependencyRisk: formData.communalDependencyRisk,
      savingsVehicleType:     formData.savingsVehicleType,
    },
  })

  const startLoadingMessages = () => {
    let i = 0
    const iv = setInterval(() => {
      i = (i + 1) % LOADING_MESSAGES.length
      setLoadingMsg(LOADING_MESSAGES[i])
    }, 4000)
    return iv
  }

  const handleAnalyze = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setLoadingMsg(LOADING_MESSAGES[0])
    const iv = startLoadingMessages()
    try {
      const res = await fetch('https://apnagharai.onrender.com/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(getPayload()),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'AI analysis failed. Please try again.')
      }
      const data = await res.json()
      setAssumptions(data)
      setStep(2)
    } catch (err) {
      setError(err.message.includes('fetch')
        ? 'Cannot reach the backend. Is it running on port 8000?'
        : err.message)
    } finally {
      clearInterval(iv)
      setLoading(false)
    }
  }

  const handleCalculateFinal = async () => {
    setLoading(true)
    setError(null)
    setLoadingMsg('Running the math engine on your budget...')
    try {
      const res = await fetch('https://apnagharai.onrender.com/api/calculate_final', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request: getPayload(), debate: assumptions }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Calculation failed. Please try again.')
      }
      const data = await res.json()
      setResult(data)
      setStep(3)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fmt        = (n) => Math.round(n).toLocaleString('en-IN')
  const cur        = formData.baseCurrency
  const savingsGap = result ? result.monthlySavingsTarget - formData.targetSavingsMonthly : 0

  // ─── Shared top bar ────────────────────────────────────────
  const TopBar = () => (
    <header className="topbar">
      <button
        className="topbar-back"
        onClick={() => { if (step > 1) setStep(step - 1); else setStep(0) }}
        aria-label="Go back"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
          <path d="M11 4L6 9l5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Back
      </button>
      <span className="topbar-title">ApnaGharAI</span>
      <span className="topbar-step">Step {step} of 3</span>
      <ProgressBar step={step} />
    </header>
  )

  // ══════════════════════════════════════════════════════════════
  // STEP 0 — HERO (Glassmorphism full-bleed)
  // ══════════════════════════════════════════════════════════════
  if (step === 0) {
    return (
      <div className="hero">
        <main className="hero-content">
          <h1 className="hero-headline">ApnaGharAI</h1>
          <h2 className="hero-tagline">
            Smart Estimation for Tomorrow's Construction.
          </h2>
          <p className="hero-body">
            Don't just dream of your future home. Plan it with mathematical certainty.
            Our AI agents search live market data to compute the exact cost
            of building in rural India — before you break ground.
          </p>
          <button className="hero-cta" onClick={() => setStep(1)}>
            Start My Blueprint
            <svg width="18" height="18" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          <p className="hero-footnote">Takes about 30 seconds · Powered by live market data</p>
        </main>
      </div>
    )
  }

  // ══════════════════════════════════════════════════════════════
  // APP SHELL WRAPPER (For Steps 1-3)
  // ══════════════════════════════════════════════════════════════
  const renderAppShell = (content) => (
    <div className="app-container">
      <div className="glass-modal">
        <TopBar />
        {content}
      </div>
    </div>
  )

  // ══════════════════════════════════════════════════════════════
  // STEP 1 — FORM
  // ══════════════════════════════════════════════════════════════
  if (step === 1) {
    return renderAppShell(
      <form onSubmit={handleAnalyze} className="form-shell">

        {/* ── LEFT PANEL ── */}
        <aside className="form-left">
          <p className="form-left-kicker">Project Blueprint</p>
          <h2 className="form-left-headline">
            Design your<br />financial foundation.
          </h2>
          <p className="form-left-body">
            Our AI uses these details to calibrate your true cost based on market realities.
          </p>

          <div className="form-group-block">
            <p className="form-group-label">Where &amp; when?</p>
            <div className="inp-wrap">
              <label htmlFor="state" className="inp-label">State or Region</label>
              <input
                id="state" type="text" name="stateOrProvince"
                value={formData.stateOrProvince} onChange={handleChange}
                placeholder="e.g. Maharashtra, Bihar"
                className="inp" required
              />
            </div>
            <div className="inp-row">
              <div className="inp-wrap">
                <label htmlFor="years" className="inp-label">Build in how many years?</label>
                <input
                  id="years" type="number" name="timelineYears"
                  value={formData.timelineYears} onChange={handleChange}
                  min="1" max="20" className="inp" required
                />
              </div>
              <div className="inp-wrap">
                <label htmlFor="monsoon" className="inp-label">Rainy months per year</label>
                <input
                  id="monsoon" type="number" name="monsoonDisruptionMonths"
                  value={formData.monsoonDisruptionMonths} onChange={handleChange}
                  min="0" max="6" className="inp"
                />
              </div>
            </div>
          </div>

          <div className="form-group-block">
            <p className="form-group-label">Your budget picture</p>
            <div className="inp-wrap">
              <label htmlFor="cost" className="inp-label">What would this home cost to build today? ({cur})</label>
              <input
                id="cost" type="number" name="currentBaseCost"
                value={formData.currentBaseCost} onChange={handleChange}
                step="50000" min="100000" className="inp" required
              />
            </div>
            <div className="inp-row">
              <div className="inp-wrap">
                <label htmlFor="savings" className="inp-label">You can save per month ({cur})</label>
                <input
                  id="savings" type="number" name="targetSavingsMonthly"
                  value={formData.targetSavingsMonthly} onChange={handleChange}
                  min="1000" className="inp"
                />
              </div>
              <div className="inp-wrap">
                <label htmlFor="suppliers" className="inp-label">Nearby material shops</label>
                <input
                  id="suppliers" type="number" name="localSupplierCount"
                  value={formData.localSupplierCount} onChange={handleChange}
                  min="0" max="10" className="inp"
                />
              </div>
            </div>
            <div className="inp-wrap">
              <label htmlFor="highway" className="inp-label">Km from nearest highway / town</label>
              <input
                id="highway" type="number" name="lastMileDistanceKm"
                value={formData.lastMileDistanceKm} onChange={handleChange}
                min="0" max="500" className="inp"
              />
            </div>
          </div>

          {/* CTA */}
          <div className="form-left-cta">
            {loading && (
              <p className="form-status">
                <span className="spinner" aria-hidden="true" /> {loadingMsg}
              </p>
            )}
            {error && <p className="form-error">{error}</p>}
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Analysing your project…' : 'Analyse with AI →'}
            </button>
            <p className="form-hint">3 agents run in parallel · Usually takes ~30 seconds</p>
          </div>
        </aside>

        {/* ── RIGHT PANEL ── */}
        <main className="form-right">

          <section className="choice-section">
            <div className="choice-section-head">
              <p className="choice-label">My home will be built from</p>
              <p className="choice-sub">This determines material cost, durability risk, and supply chain complexity.</p>
            </div>
            <div className="mat-grid">
              <MaterialTile icon="🏢" name="Concrete & Steel"  tag="Most durable · High cost"      selected={formData.primaryMaterialType === 'CONCRETE_STEEL'}  onClick={() => pick('primaryMaterialType', 'CONCRETE_STEEL')} />
              <MaterialTile icon="🧱" name="Brick & Mortar"    tag="Proven · Moderate cost"         selected={formData.primaryMaterialType === 'BRICK_MORTAR'}    onClick={() => pick('primaryMaterialType', 'BRICK_MORTAR')} />
              <MaterialTile icon="🌿" name="Mud & Bamboo"      tag="Eco-friendly · Lowest cost"     selected={formData.primaryMaterialType === 'MUD_BAMBOO'}      onClick={() => pick('primaryMaterialType', 'MUD_BAMBOO')} />
              <MaterialTile icon="🏗️" name="Prefabricated"    tag="Factory-built · Fastest"        selected={formData.primaryMaterialType === 'PREFAB_STEEL'}    onClick={() => pick('primaryMaterialType', 'PREFAB_STEEL')} />
            </div>
          </section>

          <div className="section-divider" />

          <div className="choice-row-2">
            <section className="choice-section">
              <div className="choice-section-head">
                <p className="choice-label">How my family earns</p>
                <p className="choice-sub">Determines cash-flow risk and harvest-cycle buffers.</p>
              </div>
              <div className="pill-stack">
                <Pill label="Fixed Salary"    sub="Steady monthly income"      selected={formData.incomeStructureType === 'SALARIED'}          onClick={() => pick('incomeStructureType', 'SALARIED')} />
                <Pill label="Farming Income"  sub="Comes in seasonal harvests" selected={formData.incomeStructureType === 'HARVEST_DEPENDENT'}  onClick={() => pick('incomeStructureType', 'HARVEST_DEPENDENT')} />
                <Pill label="Daily Wages"     sub="Variable day-to-day"        selected={formData.incomeStructureType === 'INFORMAL_WAGES'}     onClick={() => pick('incomeStructureType', 'INFORMAL_WAGES')} />
              </div>
            </section>

            <section className="choice-section">
              <div className="choice-section-head">
                <p className="choice-label">Community responsibility</p>
                <p className="choice-sub">How likely are unexpected family obligations to draw from savings?</p>
              </div>
              <div className="pill-stack">
                <Pill label="Low"    sub="Independent finances"       selected={formData.communalDependencyRisk === 'LOW'}    onClick={() => pick('communalDependencyRisk', 'LOW')} />
                <Pill label="Medium" sub="Some extended family calls"  selected={formData.communalDependencyRisk === 'MEDIUM'} onClick={() => pick('communalDependencyRisk', 'MEDIUM')} />
                <Pill label="High"   sub="Many dependants"            selected={formData.communalDependencyRisk === 'HIGH'}   onClick={() => pick('communalDependencyRisk', 'HIGH')} />
              </div>
            </section>
          </div>

          <div className="section-divider" />

          <div className="choice-row-2">
            <section className="choice-section">
              <div className="choice-section-head">
                <p className="choice-label">Where I keep my savings</p>
                <p className="choice-sub">Affects liquidity risk and theft vulnerability.</p>
              </div>
              <div className="pill-grid-2">
                <Pill label="Bank Account"  sub="Safest"          selected={formData.savingsVehicleType === 'BANK'}         onClick={() => pick('savingsVehicleType', 'BANK')} />
                <Pill label="Post Office"   sub="Govt. scheme"    selected={formData.savingsVehicleType === 'POST_OFFICE'}  onClick={() => pick('savingsVehicleType', 'POST_OFFICE')} />
                <Pill label="Gold"          sub="Traditional"     selected={formData.savingsVehicleType === 'GOLD'}         onClick={() => pick('savingsVehicleType', 'GOLD')} />
                <Pill label="Cash at Home"  sub="Highest risk"    selected={formData.savingsVehicleType === 'CASH_AT_HOME'} onClick={() => pick('savingsVehicleType', 'CASH_AT_HOME')} />
              </div>
            </section>

            <section className="choice-section">
              <div className="choice-section-head">
                <p className="choice-label">Advantages that lower your cost</p>
                <p className="choice-sub">Every checked advantage reduces your final budget estimate.</p>
              </div>
              <div className="toggle-stack">
                <ToggleRow
                  label="Family will build it themselves"
                  hint="Saves the full contractor labour cost"
                  checked={formData.isDIYLabor}
                  onClick={() => toggle('isDIYLabor')}
                />
                <ToggleRow
                  label="Sand &amp; soil sourced from own land"
                  hint="Eliminates raw material transport cost"
                  checked={formData.onSiteResourceSourcing}
                  onClick={() => toggle('onSiteResourceSourcing')}
                />
                <ToggleRow
                  label="Secure storage available on the plot"
                  hint="Prevents cement &amp; material theft / rain damage"
                  checked={formData.hasSecureOnSiteStorage}
                  onClick={() => toggle('hasSecureOnSiteStorage')}
                />
              </div>
            </section>
          </div>
        </main>
      </form>
    )
  }

  // ══════════════════════════════════════════════════════════════
  // STEP 2 — AI REVIEW
  // ══════════════════════════════════════════════════════════════
  if (step === 2 && assumptions) {
    return renderAppShell(
      <div className="review-layout">
        <div className="verdict-pane">
          <div className="verdict-header">
            <p className="choice-label">Judge Agent's Analysis</p>
            <p className="verdict-sub">
              Three AI agents searched live data and debated. This is their consensus.
            </p>
          </div>
          <div className="verdict-scroll">
            <div className="prose">
              <ReactMarkdown>{assumptions.debateTranscript}</ReactMarkdown>
            </div>
          </div>
        </div>

        <div className="calibrate-pane">
          <div>
            <p className="choice-label">Calibrate the Inputs</p>
            <p className="calibrate-sub">
              The AI set these from live data. Edit any value where your local experience differs.
            </p>
            <div className="buffer-list">
              {[
                { label: 'Transport cost per km',    name: 'fuelRatePerKm',          step: '0.5',   hint: 'Cost (₹) to truck materials 1 km' },
                { label: "Workers' idle daily cost", name: 'dailyIdleLaborCost',     step: '50',    hint: 'Wage per idle worker-day during rain' },
                { label: 'Annual price inflation',   name: 'regionalCCIInflation',   step: '0.01',  hint: '0.07 = 7% yearly rise' },
                { label: 'Emergency reserve',        name: 'currentEventBufferCost', step: '10000', hint: 'One-time buffer for price spikes' },
              ].map(({ label, name, step: stepVal, hint }) => (
                <div key={name} className="buffer-row">
                  <div className="buffer-meta">
                    <span className="buffer-label">{label}</span>
                    <span className="buffer-hint">{hint}</span>
                  </div>
                  <input
                    type="number" step={stepVal} name={name}
                    value={assumptions[name]} onChange={handleAssumptionChange}
                    className="buffer-input"
                  />
                </div>
              ))}
            </div>
          </div>
          <div className="calibrate-actions">
            {loading && <p className="status-line"><span className="spinner" /> {loadingMsg}</p>}
            {error && step === 2 && <p className="error-line">{error}</p>}
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button type="button" className="cta cta--outline" onClick={() => setStep(1)}>← Back</button>
              <button className="cta" onClick={handleCalculateFinal} disabled={loading} style={{ flex: 1 }}>
                {loading ? 'Calculating…' : 'Calculate My Budget'}
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ══════════════════════════════════════════════════════════════
  // STEP 3 — RESULTS
  // ══════════════════════════════════════════════════════════════
  if (step === 3 && result) {
    return renderAppShell(
      <div className="results">
        <section className="results-hero">
          <p className="form-group-label" style={{ color: 'var(--text-3)'}}>Total cost to build your home</p>
          <p className="results-number">{cur}&nbsp;{fmt(result.finalTargetFund)}</p>
          <p className="results-context">
            By your target date in {formData.timelineYears} year{formData.timelineYears > 1 ? 's' : ''} ·{' '}
            {formData.stateOrProvince}
          </p>
          <div className="results-divider" />
          <p className="form-group-label" style={{ color: 'var(--text-3)'}}>Monthly savings required</p>
          <p className="results-monthly">{cur}&nbsp;{fmt(result.monthlySavingsTarget)}</p>
          <p className="results-monthly-sub">Every month for {formData.timelineYears * 12} months</p>
          {savingsGap > 0 ? (
            <div className="results-gap gap--warn">
              <strong>You are currently saving {cur} {fmt(formData.targetSavingsMonthly)} / month.</strong><br />
              You need {cur} {fmt(savingsGap)} more per month to stay on track.
            </div>
          ) : (
            <div className="results-gap gap--ok">
              <strong>You are on track.</strong><br />
              Your savings of {cur} {fmt(formData.targetSavingsMonthly)} / month covers the requirement.
            </div>
          )}
        </section>

        <section className="results-breakdown">
          <p className="form-group-label" style={{ color: 'var(--text-3)', marginBottom: '1.5rem' }}>How we got there</p>
          <table className="breakdown">
            <tbody>
              <tr>
                <td>Home cost today</td>
                <td>{cur} {fmt(formData.currentBaseCost)}</td>
                <td />
              </tr>
              <tr>
                <td>+ Transport &amp; supply mark-up</td>
                <td>+ {cur} {fmt(result.initialLoadPenalty)}</td>
                <td className="note">Distance · Monopoly suppliers · Rain delays</td>
              </tr>
              <tr className="row--accent">
                <td>= Adjusted starting cost</td>
                <td>{cur} {fmt(result.adjustedBase)}</td>
                <td />
              </tr>
              <tr>
                <td>→ After {formData.timelineYears}-yr inflation</td>
                <td>{cur} {fmt(result.escalatedCost)}</td>
                <td className="note">Prices rise every year</td>
              </tr>
              <tr>
                <td>+ Emergency safety net</td>
                <td>+ {cur} {fmt(assumptions.currentEventBufferCost)}</td>
                <td className="note">Held aside for sudden price spikes</td>
              </tr>
              <tr className="row--total">
                <td>Total fund required</td>
                <td>{cur} {fmt(result.finalTargetFund)}</td>
                <td />
              </tr>
            </tbody>
          </table>
          <button
            className="btn-primary"
            style={{ marginTop: '3.5rem', width: '100%', maxWidth: '320px', background: 'var(--glass-panel)', border: '1px solid var(--glass-border)', color: '#fff', boxShadow: 'none' }}
            onClick={() => { setStep(0); setResult(null); setAssumptions(null) }}
          >
            Start a new estimate
          </button>
        </section>
      </div>
    )
  }

  return null
}

export default App
