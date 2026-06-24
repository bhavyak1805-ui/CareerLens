import { useState, useEffect } from "react";

const APP_ID = "de9d9ffd";
const APP_KEY = "fe0dfad323224ae4fd989408bc94e51c";

const DATA = {
  domains: ["IT", "Mechanical", "Civil", "EEE"],
  industries: {
    IT: ["Software Development", "Cloud Computing", "Cyber Security"],
    Mechanical: ["Automobile", "Manufacturing", "Robotics"],
    Civil: ["Construction", "Infrastructure", "Real Estate"],
    EEE: ["Power Systems", "Electrical Automation", "Electronics"],
  },
  skills: {
    "Software Development": ["Python", "JavaScript", "React"],
    "Cloud Computing": ["AWS", "Azure", "Docker"],
    "Cyber Security": ["Networking", "Ethical Hacking", "SIEM"],
    Automobile: ["CAD", "SolidWorks", "Matlab"],
    Manufacturing: ["Production", "Lean", "Six Sigma"],
    Robotics: ["Automation", "ROS", "Arduino"],
    Construction: ["AutoCAD", "Revit", "BIM"],
    Infrastructure: ["Project Management", "GIS", "SAP"],
    "Real Estate": ["Site Planning", "Valuation", "RERA"],
    "Power Systems": ["Circuit Design", "ETAP", "SCADA"],
    "Electrical Automation": ["PLC", "MATLAB", "VHDL"],
    Electronics: ["Embedded Systems", "PCB Design", "FPGA"],
  },
  companies: {
    "Software Development|Python": { name: "Infosys", pkg: 8 },
    "Cloud Computing|AWS": { name: "Amazon", pkg: 10 },
    "Cyber Security|Networking": { name: "Cisco", pkg: 9 },
    "Automobile|CAD": { name: "Tata Motors", pkg: 7 },
    "Manufacturing|Production": { name: "L&T", pkg: 6 },
    "Robotics|Automation": { name: "Bosch", pkg: 8 },
    "Construction|AutoCAD": { name: "DLF", pkg: 6 },
    "Infrastructure|Project Management": { name: "Shapoorji Pallonji", pkg: 7 },
    "Real Estate|Site Planning": { name: "Godrej Properties", pkg: 5 },
    "Power Systems|Circuit Design": { name: "ABB", pkg: 8 },
    "Electrical Automation|PLC": { name: "Siemens", pkg: 9 },
    "Electronics|Embedded Systems": { name: "Intel", pkg: 10 },
  },
};

function predictCompany(industry, skill) {
  const key = `${industry}|${skill}`;
  return DATA.companies[key] || { name: "TCS / Wipro", pkg: 7 };
}

function SkillTag({ label, onRemove }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      background: "var(--color-background-info)", color: "var(--color-text-info)",
      fontSize: 13, padding: "3px 10px", borderRadius: 20,
      border: "0.5px solid var(--color-border-info)"
    }}>
      {label}
      <button onClick={onRemove} style={{
        background: "none", border: "none", cursor: "pointer",
        color: "var(--color-text-info)", padding: 0, lineHeight: 1, fontSize: 14
      }}>×</button>
    </span>
  );
}

function JobCard({ job }) {
  const salary = job.salary_min && job.salary_max
    ? `₹${Math.round(job.salary_min / 100000)}L – ₹${Math.round(job.salary_max / 100000)}L`
    : null;
  return (
    <div style={{
      background: "var(--color-background-primary)",
      border: "0.5px solid var(--color-border-tertiary)",
      borderRadius: "var(--border-radius-lg)", padding: "1rem 1.25rem", marginBottom: 10
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
        <div style={{ flex: 1 }}>
          <p style={{ fontWeight: 500, fontSize: 15, margin: "0 0 3px", color: "var(--color-text-primary)" }}>
            {job.title}
          </p>
          <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: 0 }}>
            {job.company?.display_name}
          </p>
        </div>
        {salary && (
          <span style={{
            fontSize: 12, padding: "3px 10px", borderRadius: 20, whiteSpace: "nowrap",
            background: "var(--color-background-success)", color: "var(--color-text-success)",
            border: "0.5px solid var(--color-border-success)"
          }}>{salary}</span>
        )}
      </div>
      <div style={{ display: "flex", gap: 12, margin: "8px 0", flexWrap: "wrap" }}>
        <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
          <i className="ti ti-map-pin" style={{ fontSize: 13, verticalAlign: -1 }} aria-hidden="true" /> {job.location?.display_name}
        </span>
        <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
          <i className="ti ti-calendar" style={{ fontSize: 13, verticalAlign: -1 }} aria-hidden="true" /> {job.created?.slice(0, 10)}
        </span>
      </div>
      <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 10px", lineHeight: 1.6 }}>
        {job.description?.slice(0, 220)}...
      </p>
      <a href={job.redirect_url} target="_blank" rel="noreferrer" style={{
        fontSize: 13, color: "var(--color-text-info)", textDecoration: "none",
        display: "inline-flex", alignItems: "center", gap: 4
      }}>
        Apply now <i className="ti ti-external-link" style={{ fontSize: 13 }} aria-hidden="true" />
      </a>
    </div>
  );
}

export default function SmartJobFinder() {
  const [step, setStep] = useState(1);
  const [domain, setDomain] = useState("");
  const [industry, setIndustry] = useState("");
  const [skills, setSkills] = useState([]);
  const [skillInput, setSkillInput] = useState("");
  const [pkg, setPkg] = useState(7);
  const [prediction, setPrediction] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [location, setLocation] = useState("india");
  const [jobCount, setJobCount] = useState(10);
  const [searched, setSearched] = useState(false);

  const suggestedSkills = industry ? (DATA.skills[industry] || []) : [];

  function addSkill(s) {
    const trimmed = s.trim();
    if (trimmed && !skills.includes(trimmed)) setSkills([...skills, trimmed]);
    setSkillInput("");
  }

  function handlePredict() {
    const p = predictCompany(industry, skills[0] || "");
    setPrediction(p);
    setStep(3);
  }

  async function searchJobs(queryOverride) {
    const query = queryOverride || `${skills[0] || industry} ${domain}`;
    setLoading(true); setError(""); setSearched(true);
    try {
      const url = new URL("https://api.adzuna.com/v1/api/jobs/in/search/1");
      url.searchParams.set("app_id", APP_ID);
      url.searchParams.set("app_key", APP_KEY);
      url.searchParams.set("what", query);
      url.searchParams.set("where", location);
      url.searchParams.set("results_per_page", jobCount);
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error(`API error ${res.status}`);
      const data = await res.json();
      setJobs(data.results || []);
    } catch (e) {
      setError("Could not fetch jobs. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const canProceed1 = domain && industry;
  const canProceed2 = skills.length > 0;

  return (
    <div style={{ padding: "1rem 0", fontFamily: "var(--font-sans)" }}>
      <h2 className="sr-only">Smart Job Finder — Student Help Desk</h2>

      {/* Header */}
      <div style={{ marginBottom: "1.5rem" }}>
        <p style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.08em", color: "var(--color-text-secondary)", margin: "0 0 4px", textTransform: "uppercase" }}>
          Student Help Desk
        </p>
        <h2 style={{ fontSize: 22, fontWeight: 500, margin: "0 0 6px", color: "var(--color-text-primary)" }}>
          Smart Job Finder
        </h2>
        <p style={{ fontSize: 14, color: "var(--color-text-secondary)", margin: 0 }}>
          Profile your domain and skills, get a company prediction, then discover real openings.
        </p>
      </div>

      {/* Step indicators */}
      <div style={{ display: "flex", gap: 8, marginBottom: "1.5rem" }}>
        {["Profile", "Skills", "Explore"].map((label, i) => {
          const n = i + 1;
          const active = step === n;
          const done = step > n;
          return (
            <button key={n} onClick={() => done || active ? setStep(n) : null}
              style={{
                display: "flex", alignItems: "center", gap: 6, padding: "5px 12px",
                borderRadius: "var(--border-radius-md)", fontSize: 13, fontWeight: active ? 500 : 400,
                cursor: done ? "pointer" : "default",
                background: active ? "var(--color-background-info)" : "var(--color-background-secondary)",
                color: active ? "var(--color-text-info)" : "var(--color-text-secondary)",
                border: active ? "0.5px solid var(--color-border-info)" : "0.5px solid var(--color-border-tertiary)"
              }}>
              <span style={{
                width: 18, height: 18, borderRadius: "50%", display: "inline-flex",
                alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 500,
                background: done ? "var(--color-background-success)" : active ? "var(--color-text-info)" : "var(--color-border-secondary)",
                color: done ? "var(--color-text-success)" : active ? "var(--color-background-primary)" : "var(--color-text-tertiary)"
              }}>{done ? "✓" : n}</span>
              {label}
            </button>
          );
        })}
      </div>

      {/* Step 1: Domain & Industry */}
      {step === 1 && (
        <div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
            <div>
              <label style={{ fontSize: 13, color: "var(--color-text-secondary)", display: "block", marginBottom: 6 }}>Domain</label>
              <select value={domain} onChange={e => { setDomain(e.target.value); setIndustry(""); setSkills([]); }}
                style={{ width: "100%" }}>
                <option value="">Select domain</option>
                {DATA.domains.map(d => <option key={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: 13, color: "var(--color-text-secondary)", display: "block", marginBottom: 6 }}>Industry type</label>
              <select value={industry} onChange={e => { setIndustry(e.target.value); setSkills([]); }}
                style={{ width: "100%" }} disabled={!domain}>
                <option value="">Select industry</option>
                {domain && DATA.industries[domain]?.map(i => <option key={i}>{i}</option>)}
              </select>
            </div>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 13, color: "var(--color-text-secondary)", display: "block", marginBottom: 6 }}>
              Expected package — <strong>{pkg} LPA</strong>
            </label>
            <input type="range" min={3} max={20} step={1} value={pkg}
              onChange={e => setPkg(Number(e.target.value))} style={{ width: "100%" }} />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--color-text-tertiary)" }}>
              <span>3 LPA</span><span>20 LPA</span>
            </div>
          </div>
          <button onClick={() => setStep(2)} disabled={!canProceed1}
            style={{ padding: "8px 20px", fontSize: 14 }}>
            Next — Add skills <i className="ti ti-arrow-right" aria-hidden="true" />
          </button>
        </div>
      )}

      {/* Step 2: Skills */}
      {step === 2 && (
        <div>
          <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 10px" }}>
            Add skills relevant to your profile. Tap a suggestion or type your own.
          </p>
          <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
            <input value={skillInput} onChange={e => setSkillInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && skillInput && addSkill(skillInput)}
              placeholder="Type a skill and press Enter"
              style={{ flex: 1 }} />
            <button onClick={() => skillInput && addSkill(skillInput)}
              style={{ padding: "8px 14px", fontSize: 14 }}>
              <i className="ti ti-plus" aria-hidden="true" /> Add
            </button>
          </div>

          {suggestedSkills.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <p style={{ fontSize: 12, color: "var(--color-text-tertiary)", margin: "0 0 6px" }}>Suggested for {industry}:</p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {suggestedSkills.filter(s => !skills.includes(s)).map(s => (
                  <button key={s} onClick={() => addSkill(s)}
                    style={{
                      fontSize: 12, padding: "3px 10px", borderRadius: 20,
                      background: "var(--color-background-secondary)",
                      border: "0.5px solid var(--color-border-secondary)",
                      color: "var(--color-text-secondary)", cursor: "pointer"
                    }}>+ {s}</button>
                ))}
              </div>
            </div>
          )}

          {skills.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
              {skills.map(s => <SkillTag key={s} label={s} onRemove={() => setSkills(skills.filter(x => x !== s))} />)}
            </div>
          )}

          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => setStep(1)} style={{ padding: "8px 16px", fontSize: 14 }}>
              <i className="ti ti-arrow-left" aria-hidden="true" /> Back
            </button>
            <button onClick={handlePredict} disabled={!canProceed2} style={{ padding: "8px 20px", fontSize: 14 }}>
              Predict & explore <i className="ti ti-arrow-right" aria-hidden="true" />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Prediction + Job Search */}
      {step === 3 && prediction && (
        <div>
          {/* Prediction card */}
          <div style={{
            background: "var(--color-background-secondary)", borderRadius: "var(--border-radius-lg)",
            padding: "1rem 1.25rem", marginBottom: "1.5rem",
            border: "0.5px solid var(--color-border-tertiary)"
          }}>
            <p style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.08em", color: "var(--color-text-tertiary)", margin: "0 0 8px", textTransform: "uppercase" }}>
              ML prediction
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
              <div>
                <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 2px" }}>Best-match company</p>
                <p style={{ fontSize: 20, fontWeight: 500, margin: 0, color: "var(--color-text-primary)" }}>
                  <i className="ti ti-building" style={{ fontSize: 18, verticalAlign: -2, marginRight: 6 }} aria-hidden="true" />
                  {prediction.name}
                </p>
              </div>
              <div>
                <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 2px" }}>Avg. package</p>
                <p style={{ fontSize: 20, fontWeight: 500, margin: 0, color: "var(--color-text-success)" }}>
                  ₹{prediction.pkg}L / yr
                </p>
              </div>
              <div style={{ flex: 1, minWidth: 140 }}>
                <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 4px" }}>Your profile</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {[domain, industry, ...skills].map(t => (
                    <span key={t} style={{
                      fontSize: 11, padding: "2px 8px", borderRadius: 20,
                      background: "var(--color-background-primary)",
                      border: "0.5px solid var(--color-border-tertiary)",
                      color: "var(--color-text-secondary)"
                    }}>{t}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Job search controls */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: 10, alignItems: "flex-end", marginBottom: 12 }}>
            <div>
              <label style={{ fontSize: 13, color: "var(--color-text-secondary)", display: "block", marginBottom: 6 }}>
                Search query
              </label>
              <input defaultValue={`${skills[0] || industry}`} id="job-query"
                placeholder="e.g. Python developer" style={{ width: "100%" }} />
            </div>
            <div>
              <label style={{ fontSize: 13, color: "var(--color-text-secondary)", display: "block", marginBottom: 6 }}>
                Location
              </label>
              <input value={location} onChange={e => setLocation(e.target.value)}
                placeholder="india" style={{ width: "100%" }} />
            </div>
            <div>
              <label style={{ fontSize: 13, color: "var(--color-text-secondary)", display: "block", marginBottom: 6 }}>
                Results
              </label>
              <select value={jobCount} onChange={e => setJobCount(Number(e.target.value))}>
                {[5, 10, 20, 30].map(n => <option key={n}>{n}</option>)}
              </select>
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, marginBottom: "1.5rem" }}>
            <button onClick={() => {
              const q = document.getElementById("job-query")?.value || `${skills[0]} ${domain}`;
              searchJobs(q);
            }} style={{ padding: "8px 20px", fontSize: 14 }}>
              <i className="ti ti-search" aria-hidden="true" /> Search live jobs
            </button>
            <button onClick={() => searchJobs(`${prediction.name} ${skills[0] || industry}`)}
              style={{ padding: "8px 16px", fontSize: 14 }}>
              <i className="ti ti-building" aria-hidden="true" /> Jobs at {prediction.name}
            </button>
            <button onClick={() => setStep(2)} style={{ padding: "8px 14px", fontSize: 14 }}>
              <i className="ti ti-edit" aria-hidden="true" /> Edit
            </button>
          </div>

          {/* Results */}
          {loading && (
            <div style={{ textAlign: "center", padding: "2rem", color: "var(--color-text-secondary)", fontSize: 14 }}>
              <i className="ti ti-loader" style={{ fontSize: 20 }} aria-hidden="true" /> Fetching jobs from Adzuna...
            </div>
          )}
          {error && (
            <div style={{
              padding: "10px 14px", borderRadius: "var(--border-radius-md)", fontSize: 13,
              background: "var(--color-background-danger)", color: "var(--color-text-danger)",
              border: "0.5px solid var(--color-border-danger)", marginBottom: 12
            }}>
              <i className="ti ti-alert-circle" aria-hidden="true" /> {error}
            </div>
          )}
          {!loading && searched && jobs.length === 0 && !error && (
            <p style={{ color: "var(--color-text-secondary)", fontSize: 14 }}>No jobs found. Try a different query or location.</p>
          )}
          {!loading && jobs.length > 0 && (
            <div>
              <p style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 10 }}>
                <i className="ti ti-check" aria-hidden="true" /> {jobs.length} jobs found
              </p>
              {jobs.map((job, i) => <JobCard key={job.id || i} job={job} />)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
