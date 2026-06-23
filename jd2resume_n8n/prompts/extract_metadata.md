Extract the following from the job description below. Return only valid JSON, no explanation.

Fields:
- company: the hiring company name (string)
- role: the job title being hired for (string)
- seniority: one of "junior", "mid", "senior", "staff", "lead"
- archetype: one of "startup", "faang", "enterprise", "consulting"

Determine archetype from context clues: startup = small/fast/owns full stack; faang = scale/rigor/precision metrics; enterprise = stakeholder mgmt/governance/process; consulting = client impact/executive presence.

Return format:
{
  "company": "...",
  "role": "...",
  "seniority": "...",
  "archetype": "..."
}
