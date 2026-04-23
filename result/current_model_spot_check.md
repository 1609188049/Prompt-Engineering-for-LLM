# Current Model Spot Check

## Scope

This file records a small qualitative prompt test performed manually in this session using the current assistant model and the repository prompt styles from `prompts.py`.

Important limitations:

- This is a manual spot check, not an automated API run.
- The summaries below are not part of the scored BERTScore benchmark.
- The shell environment in this workspace does not currently expose `OPENAI_API_KEY`, so the repository's `openai` backend could not be executed programmatically.

## Article 1

Title: `Ukraine's strike on a brand-new missile carrier could force Russian shipbuilders further away from the war, UK intel says`

Reference summary:

> Ukraine's attack on the Askold missile carrier may prompt Russia's shipbuilders to move even further away from the fighting, the UK MOD said.

Prompt-mode outputs:

- `zero-shot`: Ukraine struck the Askold missile carrier at the Zaliv shipyard in Crimea, according to Ukrainian and UK sources. The UK Ministry of Defence said the attack may push Russia to move shipbuilding farther from the front line. That relocation could delay delivery of new naval vessels.
- `few-shot`: Ukraine damaged the Askold missile carrier in Crimea. UK defence officials said the strike could force Russia to relocate shipbuilding activity farther from the battlefield. The likely effect would be slower delivery of new warships.
- `cot`: The main event was a Ukrainian strike on the Askold, a new Russian corvette under construction in Crimea. Key actors were Ukrainian forces, the UK Ministry of Defence, and Russian naval shipbuilders. The most important outcome is that Russia may have to move production farther from the war zone, delaying future vessel deployment.

Observation:

- `few-shot` produced the cleanest compact summary.
- `cot` was coherent, but a little more analytical than needed for a short news abstract.

## Article 2

Title: `All Blacks want answers on referee calls in World Cup final`

Reference summary:

> New Zealand has asked global governing body World Rugby to explain some of the officiating during their World Cup final defeat to South Africa, outgoing coach Ian Foster said.

Prompt-mode outputs:

- `zero-shot`: New Zealand has asked World Rugby to explain several officiating decisions from its 12-11 World Cup final loss to South Africa. The disputed moments included Sam Cane's red card, Siya Kolisi's yellow card, and the disallowed Aaron Smith try. Outgoing coach Ian Foster said the team had already submitted questions for review.
- `few-shot`: New Zealand asked World Rugby to review controversial officiating in the World Cup final defeat to South Africa. The concerns centered on Sam Cane's red card, Siya Kolisi's yellow card, and the cancellation of Aaron Smith's try. Ian Foster said the All Blacks had already filed their questions.
- `cot`: The main event was New Zealand's formal request for an explanation of officiating decisions in the World Cup final. The key disputed calls were Sam Cane's red card, Siya Kolisi's yellow card, and a disallowed Aaron Smith try. The outcome is that World Rugby now faces pressure to clarify how those decisions were made.

Observation:

- All three modes were strong.
- `cot` slightly over-emphasized implications, while `few-shot` stayed closest to the desired news-summary tone.

## Article 3

Title: `Haiti: Where aid delivery depends on talking to 300 gangs`

Reference summary:

> The Red Cross describes how it delivers health care and aid in Haiti, where gangs hold sway.

Prompt-mode outputs:

- `zero-shot`: The Red Cross says it must maintain dialogue with hundreds of gangs to deliver aid in Haiti. With about 80% of Port-au-Prince under gang control, violence has shut health facilities and trapped residents in their neighborhoods. The organization says local acceptance is essential for reaching people with health care and humanitarian support.
- `few-shot`: The Red Cross says humanitarian work in Haiti now depends on continuous talks with hundreds of gangs. Gang control across most of Port-au-Prince has disrupted clinics, travel, and basic services. Aid workers say acceptance on the ground is necessary to keep health care and relief moving.
- `cot`: The main issue is that extreme gang violence has made normal aid delivery impossible in Haiti. The key actors are the Red Cross, armed groups controlling much of Port-au-Prince, and civilians cut off from health services. The practical outcome is that humanitarian access now depends on sustained negotiation with gangs.

Observation:

- `zero-shot` and `few-shot` both fit the article well.
- `few-shot` felt slightly smoother and more publishable; `cot` was again more explanatory than strictly necessary.

## Takeaway

This small manual check suggests a different pattern from the mock BERTScore benchmark:

- the current assistant model handled all three prompt styles competently
- `few-shot` often gave the most polished short summaries
- `cot` was useful when factual structure mattered, but it tended to sound more analytical than concise

In other words, the qualitative current-model behavior looks stronger than the mock benchmark implies. That gap is expected because the mock backend is largely extractive and the scored benchmark uses `description` as a proxy reference rather than a gold summary target.
