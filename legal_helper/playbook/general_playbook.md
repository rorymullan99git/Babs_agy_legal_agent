# General Legal Playbook - Australian & Queensland Defaults

Standing context for the author of every legal answer and for every
specialist, ahead of any domain pack. This file owns jurisdiction policy,
language policy, source-hierarchy defaults, and the universal sanity-check
rules. Domain-specific positions live under
`legal_helper/domains/<pack>/playbook.md` and come **after** this file when
the corresponding pack is active.

> **Research aid, not legal advice.** Defaults below are general legal
> research orientation for Queensland and Australian law; they do not
> substitute for qualified legal practitioners admitted in the relevant
> jurisdiction.

## 0. Jurisdiction & Source Hierarchy

For each issue settle **which law controls, in which version, at what level**
before researching, then cover every live level. Default jurisdiction is
**Australia (`AU`)**, with **Queensland (`QLD`)** as the default state
jurisdiction unless the facts or user specify another state, territory, or
foreign jurisdiction. A sourced "does not apply / this party is not bound" is
a finding, not a gap.

### Date before text (Point-in-Time Legislation)
Legislation is always cited and applied **as in force on the date of the
operative facts** (or the date asked about), not merely today's consolidation.
State the point-in-time (`as_at`) date explicitly and note whether a later or
pending amendment changes the outcome. Under the *Acts Interpretation Act 1954*
(Qld) s 20 and the *Acts Interpretation Act 1901* (Cth) s 7, substantive
amendments and repeals do not operate retrospectively to divest accrued rights
or liabilities unless a clear contrary intention appears in the statute.

### Australian source hierarchy (in descending order of authority)

1. **Constitution**: *Commonwealth of Australia Constitution Act 1900* (Imp)
   s 9 ('Constitution') and the *Constitution of Queensland 2001* (Qld)
   (subject to the Commonwealth Constitution and the *Australia Act 1986*
   (Cth)). The Commonwealth Constitution is the supreme fundamental law of
   Australia.
2. **Commonwealth statutes**: Valid Acts of the Federal Parliament enacted
   under a head of power (Constitution ss 51, 52, 122), plus subordinate
   Commonwealth legislative instruments (*Legislation Act 2003* (Cth)) within
   their enabling power. Under **Constitution s 109**, when a law of a State
   is inconsistent with a valid law of the Commonwealth, the Commonwealth law
   prevails and the State law is invalid to the extent of the inconsistency
   (direct impossibility of simultaneous obedience, denial of a right, or
   covering the field).
3. **Queensland statutes and subordinate legislation**:
   - **Queensland Acts**: Enacted by the Parliament of Queensland for the
     peace, welfare, and good government of the State (*Constitution of
     Queensland 2001* (Qld); *Australia Act 1986* (Cth) s 2). Note that
     schedule codes such as the *Criminal Code* sit in Schedule 1 to the
     *Criminal Code Act 1899* (Qld) and may be cited as the *Criminal Code*
     pursuant to s 2(2).
   - **Queensland subordinate legislation**: Regulations, rules (including the
     *Uniform Civil Procedure Rules 1999* (Qld)), proclamations, and statutory
     instruments made under an empowering Act (*Statutory Instruments Act 1992*
     (Qld)). Subordinate legislation yields to its empowering Act and to any
     inconsistent primary Act unless expressly authorised.
4. **High Court of Australia (`HCA`)**: Ultimate appellate court for all
   Australian federal, state, and territory law (Constitution s 73). Ratio
   decidendi of the High Court is strictly `binding` on all Australian courts,
   and there is a single unified common law of Australia (*Lipohar v The Queen*
   (1999) 200 CLR 485). Seriously considered dicta of the High Court carry
   special authoritative weight (`seriously_considered_dicta`) and must not be
   departed from by intermediate appellate courts (*Farah Constructions Pty
   Ltd v Say-Dee Pty Ltd* (2007) 230 CLR 89, 151 [134]).
5. **Queensland Court of Appeal (`QCA`)**: The appellate division of the
   Supreme Court of Queensland (and historically the Full Court of the Supreme
   Court of Queensland). Ratio decidendi of the `QCA` is `binding` on single
   judges of the Supreme Court (`QSC`), the District Court (`QDC`), the
   Magistrates Court (`QMC`), and Queensland tribunals (`QCAT`, `QIRC`).
   Decisions of interstate intermediate appellate courts (`NSWCA`, `VSCA`,
   `WASCA`, `SASCA`, `TASFC`, `ACTCA`, `NTCA`) and the Full Court of the
   Federal Court (`FCAFC`) on the common law of Australia or uniform/national
   legislation must be followed unless the court is convinced the decision is
   plainly wrong (`comity_appellate` per *Farah Constructions* (2007) 230 CLR
   89, 151-2 [135]).
6. **Other courts and tribunals**:
   - **Superior trial courts (`QSC`, `FCA`, interstate Supreme Courts)**:
     Decisions of single judges are `persuasive` before coordinate single
     judges (followed as a matter of judicial comity unless convinced wrong)
     and binding on inferior courts within the same hierarchy (`QDC`, `QMC`).
   - **Inferior courts and tribunals (`QDC`, `QMC`, `QCAT`, `QPEC`, `QLC`,
     `ART`/`AAT`)**: Weight-labelled `lower_court_or_tribunal`. Decisions of
     administrative tribunals such as `QCAT` do not create formal common law
     stare decisis, though appellate tribunal panels (`QCAT` Appeal Tribunal)
     promote consistency across tribunal members.
   - **Foreign and comparative courts (UK, NZ, Canada, US, EU, PRC)**:
     Weight-labelled `comparative_persuasive`. Since the *Australia Act 1986*
     (Cth), no UK decision binds Australian courts (*Cook v Cook* (1986) 162
     CLR 376).
7. **Secondary sources**: Extrinsic legislative materials (*Acts
   Interpretation Act 1954* (Qld) s 14B; *Acts Interpretation Act 1901* (Cth)
   s 15AB: explanatory notes, second reading speeches, Queensland Law Reform
   Commission and ALRC reports), legal encyclopaedias (*Halsbury's Laws of
   Australia*, *The Laws of Australia*), peer-reviewed law journals,
   monographs, and benchbooks (e.g. *Queensland Supreme and District Courts
   Criminal Directions Benchbook*). Weight-labelled `secondary`. Secondary
   sources support interpretation and context, never overriding primary
   statute or binding case law.

### Case weight labels (mandatory for every case cited)
Every case cited must carry an explicit court weight label determined by the
court that decided it and the forum applied to:
- `binding`: High Court of Australia (`HCA`), or Queensland Court of Appeal
  (`QCA`) when applied in Queensland courts/tribunals below the Court of
  Appeal.
- `seriously_considered_dicta`: Seriously considered High Court obiter dicta
  (*Farah Constructions* (2007) 230 CLR 89, 151 [134]).
- `comity_appellate`: Full Court of the Federal Court (`FCAFC`) or interstate
  intermediate appellate court (`NSWCA`, `VSCA`, `WASCA`, `SASCA`, `TASFC`,
  `ACTCA`, `NTCA`) on the common law of Australia or uniform/national
  legislation (followed unless plainly wrong).
- `persuasive`: Single judge of the Supreme Court of Queensland (`QSC`),
  Federal Court (`FCA`), or interstate Supreme Court; or ordinary obiter dicta.
- `lower_court_or_tribunal`: District Court (`QDC`), Magistrates Court (`QMC`),
  Queensland Civil and Administrative Tribunal (`QCAT`), Administrative Review
  Tribunal (`ART`), or specialist state tribunals.
- `comparative_persuasive`: Decisions from outside Australia (UK, NZ, Canada,
  US, EU, PRC/China, etc.).

### Conflicting norms - name the rule that resolved each one
- **Constitutional validity and s 109 inconsistency**: Commonwealth
  Constitution > valid Commonwealth Act > State Act (invalid to the extent of
  s 109 inconsistency).
- **Primary vs subordinate legislation**: Empowering Act > regulation / rule
  (*Statutory Instruments Act 1992* (Qld); ultra vires or repugnancy).
- **Within one legislature**: Specific provision prevails over general
  (*generalia specialibus non derogant*), and a later Act impliedly repeals an
  earlier Act only where the two cannot stand together (*leges posteriores
  priores contrarias abrogant*).
- **Statutory interpretation**: Begin with the text, read in context and in
  light of statutory purpose (*Project Blue Sky Inc v Australian Broadcasting
  Authority* (1998) 194 CLR 355, 381 [69]; *Acts Interpretation Act 1954*
  (Qld) s 14A; *Acts Interpretation Act 1901* (Cth) s 15AA), and consider
  human rights compatibility in Queensland (*Human Rights Act 2019* (Qld)
  s 48).

### Treaties
Under Australian dualism, an international treaty does not form part of
domestic Australian law unless incorporated by a valid Commonwealth or State
statute (*Minister for Immigration and Ethnic Affairs v Teoh* (1995) 183 CLR
273). Always name the domestic hook (the implementing Act and section) and any
reservations.

### Choice of law and comparative jurisdictions
Characterise the issue by the law of the forum (*lex fori*: Queensland).
Contractual choice of law governs where bona fide and legal, subject to
mandatory forum statutes (such as the *Australian Consumer Law* in Schedule 2
to the *Competition and Consumer Act 2010* (Cth) s 67). When comparative
jurisdictions are requested (`US`, `UK`, `EU`, `CN` / PRC / China), keep each
jurisdiction separate and state whose law each paragraph applies.

## 1. Language Policy

- **User-facing input/output language follows the user's language.** Default
  language is English (`en`); if the user writes in Chinese, answer in
  Chinese; if in English, answer in English.
- **Internal reasoning, sub-agent tool calls, and the tasks the author
  writes for specialists may use whichever language best fits the
  material** (e.g. English for Australian, US, UK, or EU sources; Chinese when
  reasoning over PRC statutes or cases).
- **Quote primary sources in original language** verbatim, adding a
  parenthetical translation only when the user-facing language differs.

## 2. Citation Standard

Every legal proposition carries its source and a **pinpoint marker** (`s`,
`pt`, `div`, `sch`, `cl`, `para`, `[N]`, page, or uploaded-document anchor
such as `[Doc p. 4, cl 3.2]`). When a pinpoint cannot be verified against a
retrieved source or uploaded document, output `"pinpoint unavailable"` or
label the claim `UNVERIFIED` - never invent an authority, pinpoint, quote, or
date from model memory. A final answer ends with one `## Sources` (or
`## 资料来源`) section and a `## What I could not verify` section when
operating under the grounded analysis contract.

### Citation style
Default style is set in `config.yaml` as `citation_style`. Supported:

- `aglc4` - Australian Guide to Legal Citation (4th ed) default for `AU`.
  Statutes in force as at the relevant date with pinpoint (`s`, `pt`, `div`,
  `sch`, `cl`, `para`); cases by medium neutral citation or authorised report
  with paragraph `[N]` or page pinpoint; uploaded documents by `[Doc p. X, cl Y]`.
- `gb_t_7714` - PRC national standard.
- `bluebook` - US standard.
- `oscola` - UK / EU standard.

The `legal_helper/citations` module formats accordingly.

## 3. Sanity Checks

Before relying on a claim - in a research bundle or a final answer:

1. **Claim-by-claim support.** Each claim ties to a retrieved primary source
   or an uploaded document from the current run, checked deterministically.
   No floating claims and no gap-filling from model memory.
2. **Soften or flag what you could not confirm.** Label unverified claims
   `UNVERIFIED` and write `"pinpoint unavailable"` where no pinpoint was
   confirmed in the retrieved text.
3. **Currency check (date before text).** Cite legislation as in force on the
   operative date (§0), naming the `as_at` date, and flag any provision not
   confirmed in force on that date.

## 3a. Structured Legal Reasoning (IRAC / FIRAC)

Whoever reasons through an issue - author or specialist - works each material
issue as Issue -> Rule -> Application -> Conclusion (or Facts -> Issue -> Rule
-> Application -> Conclusion for fact-heavy matters) before stating a
conclusion.

1. **Facts (FIRAC, for fact-heavy matters).** Material facts extracted from the
   uploaded document or instructions, each anchored to `[Doc p. X, cl Y]` or
   stated assumptions, flagging any internal contradiction.
2. **Issue.** The precise legal question, scoped to the parties, facts, and
   the operative date. Test claims in lifecycle order: arises -> not
   extinguished -> enforceable now -> defences and remedies.
3. **Rule.** The controlling authority found through §0, in the version in
   force on the operative date, pinned to section / schedule / clause /
   paragraph. Name the rule that resolved any conflict of norms; weight-label
   every case by court (`binding`, `seriously_considered_dicta`,
   `comity_appellate`, `persuasive`, `lower_court_or_tribunal`,
   `comparative_persuasive`); cite any treaty with its domestic hook.
4. **Application.** Element by element: element -> the fact that meets it ->
   the evidence anchor for that fact, or `unproven` and who bears the onus of
   proof. One unmet element defeats the claim. Give the strongest
   counter-reading and any adverse authority. If facts contradict each other,
   flag the contradiction and show how each version changes the outcome.
5. **Conclusion.** The supported conclusion, its verifier-derived confidence
   status, residual risk, and what unverified source or missing fact would
   settle any open point.

Verify the **quoted** language of any rule or clause against its source text
(`quote_roundtrip_tool` / `ground_answer_tool` / deterministic claim verifier)
before presenting it as a verbatim quote.

## 6. Universal Risk Defaults

These apply across packs unless a pack overlay supersedes them:

- **Regulatory and statutory carveouts** in confidentiality / NDA clauses:
  carveouts for disclosures required by law, court order, stock exchange
  rules, or regulators (ASIC, ACCC, ATO, OAIC, WorkSafe Queensland, etc.).
- **Australian Consumer Law (ACL)**: Unfair contract terms (ACL pt 2-3) and
  statutory consumer guarantees (ACL pt 3-2 div 1) cannot be excluded by
  contract (ACL s 64); clauses purporting to exclude them risk voidness and
  penalties for misleading representations (ACL ss 18, 29(1)(m)).
- **Privacy**: Check *Privacy Act 1988* (Cth) and the Australian Privacy
  Principles (including APP 8 cross-border disclosure) or *Information Privacy
  Act 2009* (Qld) for Queensland public sector agencies.
- **Legal professional privilege**: Protect dominant-purpose confidential
  communications and documents prepared for legal advice or anticipated
  litigation (*Esso Australia Resources Ltd v Federal Commissioner of
  Taxation* (1999) 201 CLR 49).

## 7. Document Production Defaults

- Every output carries a visible **"Research aid, not legal advice"** banner.
- A generated document also carries the not-legal-advice notice in its
  document properties unless explicitly omitted for a draft filing.
- Redlines are tracked changes (`redline_docx`), not a clean rewrite, and list
  "Must-have / Should-have / Nice-to-have" tiers.
- Risk memos include a severity x likelihood matrix and an explicit
  residual-risk line.
- Multi-jurisdiction memos clearly separate analysis under each jurisdiction
  before any cross-cutting recommendation.
- Every presentation or slide deck is made with `create_deck` (ppt-master)
  with a self-contained brief.
- Process maps and flowcharts: on a slide, `create_deck`; for a document or
  chat picture, `render_flowchart_image`.
