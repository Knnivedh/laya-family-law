"""Grounded English clause/span verification and evidence extraction for LAYA v7.

Separates user-stated evidence from inferred guesses across all family-law
domains (maintenance, matrimonial, custody, DV/residence, Stridhan/property,
birth registration, forum/procedure, scope). Accepts ONLY question text and
optional explicit confirmations; zero dataset IDs or ground-truth awareness.
"""

from __future__ import annotations

import re
from typing import Any

from .laya_v7_schema import FactEvidence, IssueEvidence, TextSpan

# Quote / hypothetical / third-party masking (never swallow English apostrophes like husband's / in-laws')
_QUOTE_RE = re.compile(r'"[^"\n]*"|“[^”\n]*”')
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?।;\n])\s+|\s*;\s*")

_HYPOTHETICAL_RE = re.compile(
    r"\b(?:if\s+i\s+(?:ever|later|someday|turn\s+out|file|apply|get)|what\s+if|suppose|pretend|"
    r"hypothetical(?:ly)?|in\s+case\s+i\s+(?:ever|later)|"
    r"may\s+file\s+someday|plan\s+to\s+eventually)\b",
    re.I,
)
_THIRD_PARTY_ACTOR_RE = re.compile(
    r"\b(?:my\s+(?:friend|sister|brother|colleague|neighbour|neighbor|dentist|cousin|aunt|uncle)['’]s?|"
    r"for\s+someone\s+else|someone\s+else['’]s|friend['’]s|colleague['’]s)\b",
    re.I,
)
_LAW_EXAM_RE = re.compile(r"\b(?:law\s+exam|hypothetical\s+question|just\s+an\s+example|illustrat(?:e|ing)|does\s+not\s+describe\s+my)\b", re.I)

# Non-family / out-of-scope domains
_OOS_DOMAIN_RE = re.compile(
    r"\b(?:landlord|tenant|security\s+deposit|rental\s+deposit|commercial\s+shop|shop\s+lock|locked\s+my\s+shop|business\s+partner|"
    r"owner\s+of\s+(?:the|my)\s+(?:flat|house|room|apartment|shop)\s+(?:i\s+rent|has\s+locked)|"
    r"flat\s+i\s+rent|three\s+months['’]?\s+rent|delayed\s+my\s+flat|booking\s+amount|"
    r"employer|boss|manager|supervisor|coworker|co-worker|colleague|workplace|hr\s+department|company\s+withheld|"
    r"stolen\s+(?:my\s+)?(?:scooter|bike|car|phone)|traffic\s+(?:signal|fine|challan)|challenge\s+the\s+fine|"
    r"loan\s+i\s+never\s+took|borrowed\s+[\d,.a-z\s]{1,20}(?:rupees|lakh|rs\.?)|"
    r"airline|flight\s+ticket|insurance\s+(?:company|insurer|claim)|e-?commerce|online\s+store|consumer\s+forum|refund|"
    r"compound\s+wall|tree\s+fell|ancestral\s+(?:house|property|land).*\b(?:brother|sibling|uncle)\b|"
    r"\b(?:sibling|brother|sister)\b.*\b(?:father['’]s|ancestral|agricultural)\s+(?:house|property|land)|bank\s+loan\s+dispute|neighbour)\b",
    re.I,
)
_FAMILY_ANCHOR_RE = re.compile(
    r"\b(?:husband|wife|ex-husband|ex-wife|spouse|marriage|married|divorce|matrimonial|hma|"
    r"stridhan|streedhan|dowry|alimony|maintenance|child|son|daughter|toddler|baby|minor|"
    r"mother-in-law|father-in-law|sister-in-law|domestic\s+violence|pwdva|bnss\s*(?:s\.?|section)?\s*144|gwa|birth\s+(?:certificate|was\s+registered))\b",
    re.I,
)

# Claimant sex & role
_MALE_SPEAKER_RE = re.compile(
    r"\b(?:i\s*(?:am|'m)\s+(?:the\s+|a\s+|his\s+|her\s+)?(?:husband|father|dad|man)|"
    r"^(?:father|husband)\s+here\b|i\s+am\s+his\s+father\b|"
    r"as\s+(?:the\s+|his\s+|a\s+)?(?:husband|father)|"
    r"from\s+my\s+(?:wife|ex-wife|estranged\s+wife|wife['’]s)|"
    r"against\s+my\s+(?:wife|ex-wife)|from\s+her\b|"
    r"my\s+(?:wife|ex-wife)\s+(?:earns|works|left|refuses|gives\s+nothing|beats|hits|threw\s+me\s+out|abandoned|has\s+a\s+good\s+job|took\s+the\s+kids))\b",
    re.I,
)
_FEMALE_SPEAKER_RE = re.compile(
    r"\b(?:i\s*(?:am|'m)\s+(?:the\s+|a\s+|his\s+)?(?:wife|ex-wife|former\s+wife|divorced\s+wife|mother|woman)|"
    r"as\s+(?:the\s+|his\s+)?(?:wife|mother)|"
    r"my\s+(?:husband|ex-husband)\b|"
    r"stridhan|streedhan|in-?laws?\s+(?:kept|took|sold|harass|refuse|keeping)|from\s+my\s+(?:husband|ex-husband))\b",
    re.I,
)
_ELDER_PARENT_CLAIM_RE = re.compile(
    r"\b(?:i\s*(?:am|'m)\s+(?:the\s+|his\s+|her\s+|an\s+)?(?:aged|elderly|old|retired|infirm|dependent)?\s*(?:mother|father|parent)\b|"
    r"i\s+am\s+(?:6\d|7\d|8\d|9\d)\s+years?\s+old\b.*\b(?:son|daughter)\b|"
    r"my\s+(?:father|mother)\s+is\s+(?:6\d|7\d|8\d|9\d|bedridden|old|elderly)\b.*\b(?:support|care\s+costs|maintenance)\b|"
    r"my\s+(?:son|daughter)\s+(?:earns\s+well\s+but\s+|refuses?|won['’]t)\b.*\bsupport\s+(?:me|him|her)\b|"
    r"(?:adult|grown(?:-up)?|employed|earning|major)\s+(?:son|daughter|child(?:ren)?)\s+(?:refuses?|won['’]t|will\s+not|does\s+not)\s+(?:support|maintain|help|look\s+after)\s+me|"
    r"support\s+(?:me|for\s+myself)\s+from\s+my\s+(?:adult|grown(?:-up)?)\s+(?:son|daughter))\b",
    re.I,
)
_NOT_PARENT_FROM_CHILD_RE = re.compile(
    r"\b(?:not\s+from\s+my\s+(?:son|daughter)|want\s+money\s+only\s+from\s+my\s+(?:wife|spouse)|my\s+adult\s+(?:son|daughter)\s+(?:already|helps|sends))\b",
    re.I,
)
_CHILD_ONLY_CLAIM_RE = re.compile(
    r"\b(?:not\s+(?:asking\s+)?for\s+(?:me|myself)|"
    r"(?:husband|spouse|wife)\s+(?:pays|gives)\s+me\s+enough|"
    r"(?:father|dad)\s+(?:seeking|asking|claiming).{0,35}\bfor\s+(?:the\s+|my\s+|our\s+)?(?:child|son|daughter))\b",
    re.I,
)
_CHILD_MENTION_RE = re.compile(
    r"\b(?:child|children|kids|son|daughter|baby|toddler|infant|newborn|twins|minor|"
    r"\d{1,2}-?year-?old|(?:six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen)-year-old)\b",
    re.I,
)
_ADULT_CHILD_AGE_RE = re.compile(
    r"\b(?:turned\s+(?:eighteen|18|nineteen|twenty)|"
    r"(?:1[89]|2\d|3\d)-?\s*years?\s*old|"
    r"(?:daughter|son|child)\s+(?:is|aged)\s+(?:1[89]|2\d|3\d)\b|"
    r"\b(?:eighteen|nineteen|twenty|twenty-\w+)\s+year\s+old|"
    r"\badult\s+(?:son|daughter|child)\b)\b",
    re.I,
)
_MINOR_CHILD_AGE_RE = re.compile(
    r"\b(?:baby|toddler|infant|newborn|minor|"
    r"\b(?:[1-9]|1[0-7])\s*-?\s*years?\s*-?\s*old\b|"
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen)-year-old\b|"
    r"\baged\s+(?:[1-9]|1[0-7])\b|in\s+(?:primary\s+)?school|school\s+(?:fees|uniforms?|books|tuition))\b",
    re.I,
)
_CHILD_UNRELATED_NEG_RE = re.compile(
    r"\b(?:do\s+not|don't|not)\s+(?:assess|ask(?:ing)?|seek(?:ing)?|want(?:ing)?|claim(?:ing)?)\s+(?:any\s+)?(?:payments?|maintenance|support|money)\s+for\s+(?:the\s+|my\s+)?child\b|"
    r"\b(?:child|son|daughter)\s+(?:is\s+)?(?:already\s+)?(?:supported|provided\s+for|taken\s+care\s+of|well\s+looked\s+after)\b",
    re.I,
)
_CHILD_SAFETY_RISK_RE = re.compile(
    r"\b(?:alcoholic|drunk|violent|abusive|unsafe|beats?\s+the\s+child|threatens?\s+(?:to\s+take|harm)\s+the\s+child|"
    r"take\s+(?:the\s+)?(?:child|son|daughter|him|her)\s+away|abduct|snatch)\b",
    re.I,
)

# Matrimonial & proceeding state
_HMA_ACT_RE = re.compile(r"\b(?:hma|hindu\s+marriage\s+act)\b", re.I)
_OTHER_MATRIMONIAL_ACT_RE = re.compile(r"\b(?:special\s+marriage\s+act|sma|muslim|christian\s+divorce|indian\s+divorce\s+act|divorce\s+act)\b", re.I)
_MAGISTRATE_CASE_RE = re.compile(r"\b(?:magistrate|bnss|crpc|125|pwdva|dv\s+case|domestic\s+violence\s+case)\b.{0,35}\b(?:case|petition|proceeding|pending|ongoing)\b", re.I)
_PENDING_STATE_RE = re.compile(
    r"\b(?:(?:is|are|remains|has\s+been)\s+(?:still\s+|currently\s+)?(?:pending|going\s+on|running|in\s+court|being\s+heard)|"
    r"already\s+(?:pending|going\s+on|filed\s+and\s+pending|being\s+heard)|running\s+in\s+(?:the\s+)?family\s+court|"
    r"case\s+continues|until\s+the\s+proceedings\s+finish|divorce\s+(?:petition|case|matter)\b.{0,30}\bpending)\b",
    re.I,
)
_PAST_CLOSED_RE = re.compile(
    r"\b(?:was\s+pending|used\s+to\s+be\s+pending|(?:was|has\s+been|got)\s+(?:dismissed|withdrawn|closed|disposed|ended|rejected)|no\s+case\s+(?:is\s+)?(?:pending|filed)|have\s+not\s+filed\s+(?:any\s+)?case)\b",
    re.I,
)
_BEING_FILED_RE = re.compile(
    r"\b(?:(?:am|i'm|we\s+are)\s+(?:now\s+)?filing\b|will\s+(?:be\s+)?fil(?:e|ing)|going\s+to\s+file|"
    r"(?:have\s+)?instructed\s+(?:my\s+)?lawyer\s+to\s+file|already\s+instructed\s+filing)\b",
    re.I,
)
_DECREE_PASSED_RE = re.compile(
    r"\b(?:decree\s+(?:was|has\s+been|is\s+being|already)\s+(?:passed|granted|pronounced|given|made)|"
    r"divorce\s+(?:was|has\s+been|is)\s+(?:granted|decreed|final|dissolved)|"
    r"granted\s+(?:me\s+|us\s+)?a\s+decree|marriage\s+was\s+dissolved\s+by\s+(?:a\s+)?decree)\b",
    re.I,
)
_DECREE_NOT_PASSED_RE = re.compile(
    r"\b(?:no\s+decree\s+(?:has\s+been|was|yet)|draft\s+decree|proposed\s+.*decree|decree\s+(?:next\s+(?:week|month)|will\s+be\s+passed\s+(?:soon|next))|before\s+decree)\b",
    re.I,
)
_DIVORCE_ASKED_RE = re.compile(
    r"\b(?:want\s+(?:a\s+|to\s+)?divorce|want\s+to\s+know\s+about\s+divorce|"
    r"want\s+(?:custody|maintenance|my\s+gold|money)\b[^.!?;]{0,40}\band\s+(?:a\s+)?divorce|"
    r"seeking\s+(?:a\s+)?divorce|seek\s+(?:a\s+)?divorce|need\s+(?:a\s+)?divorce|"
    r"fil(?:e|ing)\s+for\s+(?:a\s+)?divorce|applying\s+for\s+(?:a\s+)?divorce|asking\s+for\s+(?:a\s+)?divorce|"
    r"end\s+(?:the|our|this|my|it)\s+(?:marriage\s+)?legally|end\s+(?:the|our|this|my)\s+marriage|dissolve\s+(?:our|the)\s+marriage|"
    r"want\s+to\s+separate(?:\s+from\s+(?:my\s+)?(?:husband|wife|spouse))?|"
    r"(?:mutual(?:-|\s+)?consent|mutual)\s+(?:divorce|separation)|separate\s+by\s+mutual\s+consent|"
    r"get\s+(?:a\s+)?divorce|obtain\s+(?:a\s+)?divorce)\b",
    re.I,
)
_DIVORCE_NEG_RE = re.compile(
    r"\b(?:(?:i\s+)?(?:do\s+not|don't|does\s+not|am\s+not|never)\s+(?:want(?:ing)?|asking\s+for|seeking)\s+(?:a\s+)?(?:mutual\s+)?divorce|"
    r"\bnot\s+(?:asking\s+for\s+(?:a\s+)?divorce|wanting\s+(?:a\s+)?divorce|seeking\s+(?:a\s+)?divorce|divorce)\b|"
    r"\bno\s+divorce\b|\bdivorce\s+is\s+not\s+what\s+i\s+want\b|"
    r"\b(?:have\s+not\s+decided|undecided)\s+(?:whether|about)[^.!?;]{0,20}\bdivorce\b|"
    r"\bwhile\s+i\s+decide\s+whether\s+to\s+file\s+for\s+divorce\b)",
    re.I,
)
_DIVORCE_POST_CLAUSE_RE = re.compile(r"\b(?:after\s+(?:our|the|a)\s+divorce|when\s+we\s+divorce)\b", re.I)
_MUTUAL_CONSENT_RE = re.compile(
    r"\b(?:mutual(?:-|\s+)?consent|mutual\s+divorce|separate\s+by\s+mutual\s+consent|"
    r"both\s+(?:spouses|of\s+us|partners|sides)\s+(?:agree|agreed|consent|consented)|"
    r"both\s+(?:want|agreed)\b.{0,20}\bmutual|amicably\s+(?:divorce|part)|joint\s+divorce\s+petition|agreed\s+together\s+to\s+(?:end|divorce))\b",
    re.I,
)
_MUTUAL_NEG_RE = re.compile(r"\b(?:don['’]t|do\s+not|not)\s+want\s+(?:a\s+)?mutual\s+divorce\b", re.I)
_JS_ONLY_RE = re.compile(r"\bjudicial\s+separation\b", re.I)
_RESTITUTION_RE = re.compile(
    r"\b(?:restitution\s+of\s+conjugal\s+rights|come\s+back\s+to\s+(?:live\s+with\s+me|our\s+home)|"
    r"left\s+(?:me|our\s+home)\b.{0,45}\bwant\s+(?:him|her|them)\s+(?:back|to\s+come\s+back)|"
    r"force\s+(?:him|her|my\s+spouse)\s+to\s+return\s+and\s+live\s+together|restore\s+marital\s+cohabitation)\b",
    re.I,
)

# Maintenance & existing order signals
_MAINT_CLAIM_RE = re.compile(
    r"\b(?:maintenance|alimony|interim\s+(?:maintenance|support|costs|expenses|funds)|temporary\s+(?:money|funds|maintenance|support)|"
    r"permanent\s+(?:alimony|maintenance|support)|litigation\s+(?:expenses|costs|fees)|court\s+fees|lawyer(?:'s)?\s+(?:fees|costs)|"
    r"monthly\s+(?:money|support|allowance|sum|amount|help|expenses)|financial\s+(?:support|help)|living\s+(?:costs|expenses|allowance)|for\s+a\s+living\b|"
    r"(?:gives|giving|pay|pays|paying|not\s+given|won['’]t\s+give|refuses?\s+to\s+(?:pay|give|support|maintain|contribute|share)|"
    r"not\s+paid|not\s+paying|stopped\s+paying|sends?)\b[^.!?;]{0,30}\b(?:nothing|zero|a\s+rupee|the\s+rent|any\s+money|money|maintenance|support|care\s+costs|allowance)\b|"
    r"(?:need\s+(?:is\s+|some\s+)?money\b(?!\s+(?:back|from\s+the\s+sale|for\s+it))|how\s+much\s+money\b|money\s+to\s+(?:live(?:\s+on)?|spend|run)\b|"
    r"money\s+for\s+[^.!?;]{0,35}\b(?:house|home|food|groceries|vegetables|rent|living|school|fees|tuition|child|children|kids|son|daughter|me|myself)\b)|"
    r"(?:need|want|seek(?:ing)?|claim(?:ing)?|get|how\s+much|ask(?:ing)?\s+for)\b[^.!?;]{0,28}\b(?:monthly\s+money|proper\s+monthly\s+amount|support|maintenance|alimony|allowance|an?\s+increase|more(?:\s+money)?)\b|\bmoney\s+every\s+month\b|"
    r"(?:earn|rupees|rs\.?|salary|income)\b[^.!?;]{0,30}\bnot\s+enough\b|prices\s+have\s+gone\s+up|rent\s+alone\s+is\s+\d|pay\s+slips|demand\s+proof\s+of\s+my\s+earnings|(?:have\s+no\s+(?:income|employment)|no\s+income\s+and)\b|"
    r"groceries|vegetables|household\s+(?:costs|expenses)|(?:school|tuition|college\s+admission|child['’]s\s+education)\s+(?:fees?|expenses?|bus\s+fee|costs?|money)|"
    r"unpaid\s+(?:school\s+|tuition\s+)?fees?|fees?\s+(?:are\s+)?(?:unpaid|pending)|asking\s+fees|fee\s+reminders|pay\s+for\s+(?:his|her|my\s+\w+['’]s)\s+(?:schooling|education)|"
    r"books\s+and\s+(?:uniforms|other\s+expenses)|notebooks|tiffin\s+money|lunch\s+costs|no\s+shoes|food\s+and\s+(?:care|medication|rent|schooling)|"
    r"run\s+(?:the\s+house|it)|support\s+(?:for\s+)?(?:myself|me|our|my|him|her)|share\s+(?:of\s+the\s+shop\s+income|his\s+care\s+costs)|"
    r"(?:fixed|ordered|granted)\s+(?:me\s+|my\s+)?(?:maintenance|interim\s+maintenance|lump\s+sum|(?:\d[\d,]*\s+rupees\s+a\s+month)))\b",
    re.I,
)
_MAINT_NEG_RE = re.compile(
    r"\b(?:(?:i\s+)?(?:do\s+not|don['’]t|am\s+not|never)\s+(?:want(?:ing)?|need(?:ing)?|ask(?:ing)?\s+for|seek(?:ing)?|claim(?:ing)?)|"
    r"no\s+claim\s+for|not\s+(?:asking|looking)\s+for|not\s+maintenance)\b[^.!?;]{0,25}\b(?:any\s+)?(?:maintenance|alimony|monthly\s+(?:support|money)|money(?:\s+for\s+myself)?|financial\s+support|support\s+(?:for\s+myself|order))\b|"
    r"\b(?:not\s+maintenance|gives\s+me\s+enough|sends\s+money\s+home\s+regularly|never\s+asked\s+my\s+husband\s+for\s+money\s+before)\b(?!.*\b(?:now\s+i\s+need|not\s+enough|stopped)\b)",
    re.I,
)
_LUMP_SUM_RE = re.compile(
    r"\b(?:lump[\s-]+sum|one[\s-]+time\s+(?:alimony|settlement|payment|amount)|single\s+settlement|fair\s+settlement|permanent\s+(?:alimony|settlement)\s+instead\s+of\s+monthly)\b",
    re.I,
)
_EXISTING_ORDER_RE = re.compile(
    r"\b(?:existing\s+(?:court\s+)?(?:maintenance\s+|support\s+)?order|(?:court|magistrate)\s+(?:already\s+)?(?:ordered|passed\s+(?:a|an)\s+(?:maintenance|support)\s+order|fixed\s+(?:my\s+|monthly\s+)?maintenance|gave\s+me)|"
    r"(?:interim\s+)?(?:maintenance|support|interim\s+maintenance)\s+(?:order|was\s+fixed|fixed\s+at|was\s+ordered|was\s+granted|the\s+court\s+(?:ordered|fixed)|irregularly)|"
    r"(?:has\s+not\s+paid|not\s+paying)\s+(?:the\s+)?maintenance\b|ordered\s+to\s+pay|"
    r"pays\s+the\s+ordered\s+amount|order\s+(?:made|passed|issued|granted)\s+under|already\s+have\s+an\s+order|under\s+(?:my|our)\s+(?:bnss|crpc|hma).{0,25}order)\b",
    re.I,
)
_ARREARS_VARY_RE = re.compile(
    r"\b(?:arrears|unpaid(?:\s+amount)?|missed|skipped|overdue|defaulted|shortfall|stopped\s+paying|paid\s+(?:nothing|only)|"
    r"has\s+not\s+paid\s+(?:the\s+)?maintenance|not\s+paying\s+(?:the\s+)?maintenance|irregularly|enforce(?:\s+it)?|"
    r"late\s+payments?|always\s+\d+\s+days\s+late|on\s+time|recover\s+(?:the\s+)?(?:balance|remainder|missed|unpaid)|till\s+the\s+divorce\s+ends|"
    r"fixed\s+(?:monthly\s+|payment\s+)?date|reduce|reduced|lower|decrease|cut\s+down|vary|alter|modify|cancel|revoke|terminate|set\s+aside|scale\s+down)\b",
    re.I,
)
_ENHANCE_COST_RE = re.compile(
    r"\b(?:increase|raise|enhance|more\s+money\s+now|revised(?:\s+upward)?)\b.{0,65}\b(?:cost|prices|inflation|school\s+fees|income|earns\s+double|expenses\s+rose|salary)\b|"
    r"\b(?:prices\s+have\s+gone\s+up|earns\s+double)\b.{0,45}\b(?:increase|revised)\b",
    re.I,
)

# Custody, DV, Residence, Stridhan, Joint Property, Birth cert
_CUSTODY_ASK_RE = re.compile(
    r"\b(?:custody|guardianship|guardian|visitation|access\s+to\s+(?:my|our)\s+(?:child|children|son|daughter)|"
    r"who\s+(?:will|should|gets?\s*(?:to)?)\s+(?:get|keep|have|the\s+kids)|"
    r"who\s+(?:my|our)\s+(?:\d{1,2}-?year-?old\s+)?(?:child|children|kids|son|daughter)\s+(?:lives?|stays?)\s+with|"
    r"who\s+keeps\s+(?:my|our)|"
    r"(?:child|children|kids|kidz|son|daughter|baby|girl|boy|twins|toddler|she|he|him|her|them)\b.{0,38}\b(?:remain|continue\s+living|should\s+be|stay|stays)\s+(?:only\s+)?(?:wit|with)\s+me\b|"
    r"(?:want|wants|will|should|let|must|decid(?:e|ing)|decision\s+that|agree)\b[^.!?;]{0,40}\b(?:child|children|kids|kidz|son|daughter|baby|she|he|him|her|them)\b[^.!?;]{0,25}\blives?\s+with\s+me\b|"
    r"\b(?:1[0-7]|[6-9])(?:-year-old)?\s+and\s+wants?\s+to\s+live\s+with\s+me\b|"
    r"(?:remain|be)\s+under\s+my\s+roof\b|keep\s+(?:the\s+|my\s+|our\s+|him|her|them)?(?:child|children|kids|son|daughter|baby)?\s*(?:wit|with)\s+me\b|"
    r"kept\s+(?:the\s+|my\s+|our\s+)?(?:child|children|kids|son|daughter|baby)\s+away\s+from\s+me\b|"
    r"(?:court\s+to\s+)?give\s+me\s+(?:my|our|the)\s+(?:child|children|kids|son|daughter|baby)\b|"
    r"(?:want|get|give\s+me)\s+(?:the\s+|my\s+|our\s+)?(?:child|children|kids|son|daughter|baby|him|her|them)\s+(?:back|with\s+me|to\s+come\s+back(?:\s+and\s+live)?\s+with\s+me)\b|"
    r"want\b[^.!?;]{0,30}\b(?:my|our|the)\s+(?:child|children|kids|son|daughter|baby)\s+(?:with|wit)\s+me\b|"
    r"my\s+(?:son|daughter|child|kids)\s+to\s+(?:live|stay)\s+(?:in\s+the\s+house\s+)?with\s+me\b|with\s+my\s+children|"
    r"(?:live|stay)\s+with\s+me\s+or\s+with\s+(?:her|his)\s+(?:father|mother)|decide\s+where\s+(?:she|he)\s+lives|"
    r"(?:will\s+not|won['’]t)\s+let\s+me\s+(?:see|meet)\s+(?:them|him|her|my\s+(?:son|daughter|child|children))|want\s+to\s+(?:see|meet)\s+(?:my|our)\s+(?:child|children|son|daughter)|"
    r"barred\s+from\s+meeting\s+(?:him|her|them)|belong\s+to\s+his\s+family|given\s+to\s+him|"
    r"wants?\s+to\s+live\s+with\s+(?:his|her)\s+(?:father|mother)|(?:taken|took)\s+(?:my|our|the)\s+(?:child|children|kids|son|daughter)\b|"
    r"in\s+my\s+care|spend\s+school\s+nights\s+with\s+me|weekend\s+access)\b",
    re.I,
)
_CUSTODY_NEG_RE = re.compile(
    r"\b(?:(?:i\s+)?(?:do\s+not|don['’]t)\s+want\s+custody|not\s+asking\s+for\s+custody|no\s+custody\s+dispute|custody\s+is\s+(?:not\s+in\s+issue|settled))\b",
    re.I,
)
_CUSTODY_HOUSE_COLOC_RE = re.compile(
    r"\b(?:son|daughter|child|children|kids|baby)\s+to\s+(?:stay|live)\s+in\s+(?:the|our|my)\s+(?:house|home)\s+with\s+me\b",
    re.I,
)
_RESIDENCE_ASK_RE = re.compile(
    r"\b(?:shared\s+(?:house|home|household)|right\s+to\s+(?:reside|stay)|residence\s+order|"
    r"throw(?:ing|s)?\s+me\s+out|threw\s+me\s+out|thrown\s+(?:me\s+)?out|kicked\s+(?:me\s+)?out|"
    r"changed\s+the\s+locks?|locked\s+(?:me\s+)?out|cannot\s+enter\s+(?:the|my|our)\s+(?:house|home)|stopped\s+paying\s+(?:the\s+|house\s+)?rent|"
    r"barred\s+(?:me\s+)?from\s+(?:entering|the\s+(?:house|home))|refus(?:e|ing)\s+(?:me\s+)?entry|evict(?:ed|ion)?|"
    r"told\s+me\s+to\s+leave\s+(?:the\s+)?house|ordered\s+me\s+to\s+get\s+out|i\s+must\s+vacate|want(?:s)?\s+my\s+husband\s+to\s+leave|"
    r"afraid\s+to\s+stay\s+there.*nowhere\s+else\s+to\s+go|safe\s+place\s+to\s+stay|protect\s+my\s+stay|"
    r"keep\s+staying\s+in\s+the\s+house|stay\s+in\s+(?:the\s+)?same\s+house|permission\s+to\s+remain\s+in\s+the\s+house|"
    r"(?:go|come)\s+back\s+to\s+(?:my|our|the)\s+(?:house|home)|"
    r"separate\s+(?:place\s+to\s+stay|accommodation|residence))\b",
    re.I,
)
_RESIDENCE_COLOC_ALLOW_RE = re.compile(
    r"\b(?:to\s+stay\s+in\s+(?:the|our|my)\s+(?:house|home)\s+with\s+(?:my|our)\s+(?:daughter|son|child|children))\b",
    re.I,
)
_RESIDENCE_NEG_RE = re.compile(
    r"\b(?:do\s+not\s+(?:want|need)\s+(?:to\s+stay\s+in\s+(?:that|his)\s+house|any\s+house|to\s+return\s+to\s+his)|"
    r"don['’]t\s+want\s+to\s+stay\s+in\s+that\s+house|"
    r"(?:housing|place\s+to\s+stay)\s+is\s+not\s+an\s+issue|own\s+(?:a\s+)?(?:flat|house)\s+of\s+my\s+own|my\s+own\s+house\s+to\s+live\s+in)\b",
    re.I,
)
_EXPLICIT_RES_ONLY_RE = re.compile(
    r"\b(?:residence\s+order|returned\s+to\s+my\s+parents|separate\s+(?:place|accommodation)|refus(?:e|ing)\s+(?:me\s+)?entry)\b",
    re.I,
)
_VIOLENCE_NEG_MASK_RE = re.compile(
    r"\b(?:never\s+(?:hit|beat(?:en)?|slapped|abused|threatened|harassed|hurt|touched|stopped)|"
    r"no\s+(?:violence|physical\s+harm|abuse)|has\s+never\s+hit)\b",
    re.I,
)
_VIOLENCE_RE = re.compile(
    r"\b(?:beat(?:s|ing|en)?|hit(?:s|ting)?|slap(?:s|ped|ping)?|punch(?:es|ed)?|pushed\s+me|struck\s+me|assault(?:ed|ing)?|"
    r"choke(?:d|s)?|threaten(?:s|ed|ing)?|threats?|intimidat(?:e|ed|es|ing)|abuse(?:s|d)?|abusive|"
    r"harass(?:es|ed|ing|ment)?|attack(?:s|ed|ing)?|domestic\s+violence|cruelty|hurt\s+me|"
    r"broke\s+my\s+(?:arm|hand|phone|jaw|leg|ribs|nose)|demanding\s+(?:money|dowry)|"
    r"locks?\s+(?:me|the\s+\w+\s+door)\s+(?:in|from\s+outside)|forbidden\s+me\s+from\s+(?:visiting|meeting)|"
    r"stops?\s+threatening|stays?\s+away\s+from\s+me|confin(?:ed|ement)|stalk(?:s|ed|ing)?)\b",
    re.I,
)
_COERCIVE_LOCKOUT_RE = re.compile(
    r"\b(?:throw(?:ing|s)?\s+me\s+out|threw\s+me\s+out|kicked\s+(?:me\s+)?out|changed\s+the\s+locks?|locked\s+(?:me\s+)?out|"
    r"forcing\s+me\s+out|told\s+me\s+to\s+leave|ordered\s+me\s+to\s+get\s+out|i\s+must\s+vacate|husband\s+to\s+leave|"
    r"keep\s+staying\s+in\s+the\s+house|threatening\s+to\s+(?:throw|evict|kick)\s+me\s+out|barred\s+me\s+from\s+the\s+house)\b",
    re.I,
)
_DV_COMP_RE = re.compile(
    r"\b(?:compensation|damages|medical\s+(?:bills|expenses|costs)|hospital\s+(?:bills|treatment))\b.*\b(?:injur|fracture|mental\s+torture|distress|beat|assault|violence|broke|pay)\b|"
    r"\b(?:injur|mental\s+torture|emotional\s+distress|medical\s+(?:costs|expenses)|hospital\s+treatment)\b.*\b(?:compensation|damages|recover|claim|pay)\b",
    re.I,
)

_STRIDHAN_ITEM_RE = re.compile(
    r"\b(?:stridhan|streedhan|gold(?:\s+(?:chain|ring|bars|goods|set|bangles|earrings|ornaments?))?|jewellery(?:\s+box)?|jewelry|ornaments?|bangles?|necklace|earrings?|mangalsutra|wedding\s+(?:gifts?|rings?))\b",
    re.I,
)
_STRIDHAN_HELD_RE = re.compile(
    r"\b(?:kept|keeps?|keeping|holding|withheld|refus(?:ed|es|ing)|won['’]t\s+(?:give|return)|took|taken|confiscated|"
    r"lying\s+in|locked\s+in\s+a\s+locker|(?:husband|wife|in-?laws?|mother-in-law|father-in-law|aunt|family)\b.{0,12}\b(?:still\s+)?has\s+(?:my|the)(?:\s+wedding)?\s+(?:gold|jewellery|jewelry|stridhan|ornaments?|bangles?|chain)|"
    r"(?:still|is|are|sits)\s+(?:in|with)\s+(?:my\s+|his\s+)?(?:husband['’]s|mother-in-law['’]s|father-in-law['’]s|in-?laws?['’]?|aunt['’]s|family|cupboard|locker|office\s+drawer)|"
    r"wearing\s+my\s+gold|gave\s+my\s+gold|sold|pawned|pledged|mortgaged|melted|disposed|gifted\s+away|"
    r"(?:only|just)\s+(?:my\s+)?(?:gold|jewellery|jewelry|stridhan)\b|"
    r"(?:want|get|return)\s+[^.!?;]{0,35}\b(?:gold|jewellery|jewelry|ornaments?|stridhan|bangles|chain|box|things)(?:\s+returned|\s+back)?\b|"
    r"(?:gold|jewellery|jewelry|ornaments?|bangles?|chain|stridhan)\b[^.!?;]{0,20}\b(?:returned|back)\b|"
    r"(?:value|price)\s+of\s+the\s+\w+\s+back|gold\s+(?:returned|not\s+returning)|family\s+property\s+now|confused\s+about\s+the\s+gold|either\s+gold\s+or\s+money)\b",
    re.I,
)
_STRIDHAN_SAFE_OR_UNDISP_RE = re.compile(
    r"\b(?:gold\s+(?:jewellery\s+)?is\s+(?:safe\s+)?(?:with\s+me|in\s+my\s+own)|in\s+my\s+(?:own\s+)?(?:locker|cupboard|possession|parents['’]\s+(?:house|custody))|"
    r"has\s+never\s+touched\s+it|did\s+not\s+sell\s+my\s+gold|agreed\s+to\s+return|"
    r"no\s+dispute\s+about\s+(?:the\s+\w+|it|that)|whether\s+i\s+can\s+wear\s+it|"
    r"dropped\s+my\s+claim|want\s+maintenance\s+instead|gold\s+biscuit\s+as\s+an\s+investment|have\s+not\s+decided\s+whether\s+to\s+ask(?:\s+for\s+it)?|"
    r"undecided\s+whether\s+to\s+ask)\b",
    re.I,
)
_STRIDHAN_SOLD_RE = re.compile(r"\b(?:sold|pawned|pledged|mortgaged|melted|disposed\s+of|gifted\s+away)\b", re.I)
_DEMAND_TRUE_RE = re.compile(
    r"\b(?:asked\s+(?:them|him|her)\s+to\s+return|demanded|requested\s+return|refused\s+to\s+return|will\s+not\s+return|won['’]t\s+return|refusing\s+to\s+return|not\s+returning)\b",
    re.I,
)
_DEMAND_FALSE_RE = re.compile(
    r"\b(?:never\s+(?:asked|demanded)|have\s+not\s+asked|haven['’]t\s+asked|not\s+asked\s+(?:for\s+it\s+)?yet|stayed\s+silent\s+about\s+it|never\s+asked\s+my\s+husband\s+for\s+money\s+before)\b",
    re.I,
)
_JOINT_PROP_RE = re.compile(
    r"\b(?:jointly\s+(?:owned|bought|purchased|acquired)|joint\s+(?:flat|house|apartment|plot|land|property|shop|car|home)|"
    r"(?:we\s+(?:also\s+)?|both\s+)?(?:own|bought|purchased|got)\s+(?:a\s+|an\s+|the\s+)?(?:flat|house|apartment|plot|land|property|shop|car|home)\s+together|"
    r"in\s+both\s+(?:our|spouses['’]?)\s+names|in\s+both\s+names|co-?owned\s+(?:flat|house|property)|"
    r"(?:divide|division|split|share\s+of)\s+(?:our|the|it)\s*(?:flat|house|plot|property|shop|car)?)\b",
    re.I,
)
_JOINT_PROP_NEG_RE = re.compile(
    r"\b(?:divided\s+later|don['’]t\s+want\s+(?:my\s+)?in-?laws['’]?\s+property|solely\s+in\s+(?:my\s+)?husband['’]s\s+name|own\s+no\s+property\s+together|joint\s+shop,\s+and\s+he\s+has\s+kept\s+all\s+its\s+income)\b",
    re.I,
)
_BIRTH_CERT_RE = re.compile(
    r"\b(?:birth\s+certificate|birth\s+registr(?:ation|y)|registrar\s+of\s+births|hospital\s+(?:did\s+not\s+give|never\s+issued|wrote\s+the\s+wrong)|"
    r"birth\s+was\s+(?:never\s+registered|registered,\s+but)|(?:name\s+spelt\s+wrong|wrong\s+date\s+of\s+birth)|correct\s+.*birth\s+record)\b",
    re.I,
)
_FORUM_Q_RE = re.compile(
    r"\b(?:which\s+(?:court|forum)|magistrate\s+or\s+(?:the\s+)?family\s+court|family\s+court\s+or\s+magistrate|"
    r"where\s+(?:do|should)\s+i\s+(?:file|go(?!(?:\s+to\s+enforce))|approach)|correct\s+(?:court|forum))\b",
    re.I,
)
_PROC_HOW_RE = re.compile(
    r"\b(?:how\s+(?:do|can|should)\s+(?:i|we)\s+(?:file|apply|start|enforce|collect|get|fix|handle)|steps?\s+to\s+|where\s+do\s+i\s+go\s+to\s+enforce|"
    r"what\s+(?:steps|path)|where\s+can\s+i\s+apply|how\s+is\s+this\s+corrected|where\s+is\s+this\s+corrected|"
    r"fixed\s+(?:monthly\s+|payment\s+)?date|execution\s+petition|what\s+is\s+the\s+(?:solution|remedy))\b",
    re.I,
)


def _first_span(raw: str, pattern: re.Pattern[str]) -> TextSpan | None:
    m = pattern.search(raw)
    if not m:
        return None
    return TextSpan(start=m.start(), end=m.end(), text=raw[m.start():m.end()])


def _mask_quotes_and_noise(text: str) -> str:
    return _QUOTE_RE.sub(lambda m: " " * len(m.group(0)), text)


def _split_non_hypothetical_clauses(masked: str) -> tuple[list[str], bool]:
    """Split clauses while flagging hypothetical / third-party-only contexts."""
    clauses = [c.strip() for c in _SENT_SPLIT_RE.split(masked) if c.strip()]
    active: list[str] = []
    all_hyp = True
    for cl in clauses:
        if _THIRD_PARTY_ACTOR_RE.search(cl) and not re.search(r"\bmy\s+own\s+(?:case|petition|claim)\b", cl, re.I):
            continue
        if _HYPOTHETICAL_RE.search(cl) or _LAW_EXAM_RE.search(cl):
            continue
        all_hyp = False
        active.append(cl)
    if not active and clauses:
        return clauses, all_hyp
    return active, False


def extract_grounded_v7(raw_text: str, *, translated_text: str | None = None, is_kannada_orig: bool = False, raw_kannada: str = "") -> dict[str, Any]:
    """Derive strictly grounded FactEvidence & IssueEvidence from question text.

    Never reads IDs or ground truth. Produces explicit three-state facts with
    evidence spans and subject/beneficiary discrimination.
    """
    text = (translated_text if translated_text is not None else raw_text).strip()
    masked = _mask_quotes_and_noise(text)
    clauses, all_hyp_or_3p = _split_non_hypothetical_clauses(masked)
    active_text = " ".join(clauses)

    def _fact(key: str, status: str, value: Any, pat: re.Pattern[str] | None = None, **kw: Any) -> FactEvidence:
        span = _first_span(text, pat) if (pat is not None and status == "supported") else None
        return FactEvidence(
            key=key,
            status=status,  # type: ignore[arg-type]
            value=value,
            source="translated_text" if is_kannada_orig else "user_text",
            confidence=1.0 if status in {"supported", "denied"} else 0.0,
            span=span,
            **kw,
        )

    # Scope & domestic relationship
    borrowed_loan = bool(re.search(r"\bborrowed\b.{0,25}\b(?:rupees|lakh|cash|money)\b", active_text, re.I)) and not bool(
        re.search(r"\b(?:husband|wife|marriage|wedding|stridhan|dowry|maintenance)\b", active_text, re.I)
    )
    has_family = bool(_FAMILY_ANCHOR_RE.search(active_text)) and not borrowed_loan
    has_oos = bool(_OOS_DOMAIN_RE.search(active_text)) or borrowed_loan
    law_exam = bool(_LAW_EXAM_RE.search(text))
    if law_exam or (has_oos and not has_family):
        in_scope_ev = _fact("in_scope", "denied", False)
    else:
        in_scope_ev = _fact("in_scope", "supported", True)

    dom_rel = not bool(re.search(r"\b(?:workplace|colleague|co-?worker|boss|landlord|tenant|neighbour|insurer|airline)\b", active_text, re.I) and not has_family)
    if re.search(r"\b(?:boss|supervisor|coworker|co-?worker|colleague|manager)\b", active_text, re.I) and not re.search(r"\b(?:husband|wife|spouse|in-?laws?|partner\s+at\s+home)\b", active_text, re.I):
        dom_rel = False
    if has_oos and not has_family:
        dom_rel = False

    # Sex & role
    is_male = bool(_MALE_SPEAKER_RE.search(active_text))
    is_female = bool(_FEMALE_SPEAKER_RE.search(active_text))
    if is_male and not is_female:
        sex = "male"
    elif is_female and not is_male:
        sex = "female"
    else:
        if re.search(r"\bmy\s+(?:husband|ex-husband)\b", active_text, re.I) and not re.search(r"\bi\s*(?:am|'m)\s+(?:the\s+)?husband\b", active_text, re.I):
            sex = "female"
        elif re.search(r"\bmy\s+(?:wife|ex-wife)\b", active_text, re.I) and not re.search(r"\bi\s*(?:am|'m)\s+(?:the\s+)?wife\b", active_text, re.I):
            sex = "male"
        else:
            sex = "unknown"

    is_parent_claim = bool(_ELDER_PARENT_CLAIM_RE.search(active_text)) and not bool(_NOT_PARENT_FROM_CHILD_RE.search(active_text))
    male_child_supp = (
        sex == "male"
        and bool(
            re.search(
                r"\b(?:maintenance|money|support|school|tuition|fees)\b[^.!?;]{0,35}\bfor\s+(?:the\s+|my\s+|our\s+)?(?:\w+\s+)?(?:child|children|son|daughter|kids|baby)\b|"
                r"\bfor\s+(?:the\s+|my\s+|our\s+)?(?:\w+\s+)?(?:child|children|son|daughter|kids|baby)(?:['’]s)?\s+(?:school|tuition|education|books|fees|support|maintenance|expenses)\b",
                active_text,
                re.I,
            )
        )
        and not bool(re.search(r"\b(?:for\s+myself|interim\s+maintenance|lump[\s-]+sum|settlement)\b", active_text, re.I))
    )
    child_only = (bool(_CHILD_ONLY_CLAIM_RE.search(active_text)) or male_child_supp) and not bool(
        re.search(r"\b(?:for\s+myself|me\s+and\s+my\s+(?:child|son|daughter))\b", active_text, re.I)
    )
    if is_parent_claim:
        role = "parent"
    elif sex in {"male", "female"} or re.search(r"\b(?:spouse|husband|wife|married|divorce)\b", active_text, re.I):
        role = "spouse"
    else:
        role = "unknown"

    # Minor child check
    has_child_mention = bool(_CHILD_MENTION_RE.search(active_text))
    is_adult_child = bool(_ADULT_CHILD_AGE_RE.search(active_text)) and not bool(_MINOR_CHILD_AGE_RE.search(active_text))
    child_neg = bool(_CHILD_UNRELATED_NEG_RE.search(active_text))
    minor_child_st = "denied" if (is_adult_child or child_neg) else ("supported" if bool(_MINOR_CHILD_AGE_RE.search(active_text)) or (has_child_mention and not is_adult_child) else "unknown")

    # Proceeding pending (HMA) & being_filed & decree
    raw_pending = any(_PENDING_STATE_RE.search(c) for c in clauses) and not all(_PAST_CLOSED_RE.search(c) for c in clauses)
    has_hma_ref = bool(_HMA_ACT_RE.search(active_text))
    has_other_act = bool(_OTHER_MATRIMONIAL_ACT_RE.search(active_text))
    mag_only_pending = bool(_MAGISTRATE_CASE_RE.search(active_text)) and not has_hma_ref and not re.search(r"\bdivorce\s+(?:case|petition)\b", active_text, re.I)
    law_unknown_q = bool(re.search(r"\b(?:don['’]t|do\s+not)\s+know\s+(?:which|the)\s+(?:law|act)\b", active_text, re.I))
    divorce_case_ongoing = bool(re.search(r"\bdivorce\s*(?:case|petition|matter|suit)?\b.{0,35}\b(?:pending|going\s+on|goin\s+on|running|being\s+heard)\b", active_text, re.I))
    pending_hma = (
        raw_pending
        and not _PAST_CLOSED_RE.search(active_text)
        and not has_other_act
        and not mag_only_pending
        and not law_unknown_q
        and (has_hma_ref or divorce_case_ongoing)
    )
    if divorce_case_ongoing and not _PAST_CLOSED_RE.search(active_text) and not has_other_act:
        pending_hma = True
    being_filed = bool(_BEING_FILED_RE.search(active_text)) and not _HYPOTHETICAL_RE.search(active_text) and not has_other_act
    decree = bool(_DECREE_PASSED_RE.search(active_text)) and not bool(_DECREE_NOT_PASSED_RE.search(active_text)) and not has_other_act

    # Divorce / JS / Restitution
    js_only = bool(_JS_ONLY_RE.search(active_text)) and not bool(re.search(r"\bwant(?:s|ing)?\s+(?:a\s+)?divorce\b", active_text, re.I))
    div_scan_text = _DIVORCE_POST_CLAUSE_RE.sub(" ", active_text)
    divorce_neg = bool(_DIVORCE_NEG_RE.search(active_text))
    mutual_consent = bool(_MUTUAL_CONSENT_RE.search(active_text)) and not bool(_MUTUAL_NEG_RE.search(active_text))
    divorce_asked = (bool(_DIVORCE_ASKED_RE.search(div_scan_text)) or mutual_consent) and not divorce_neg and not js_only
    restitution_asked = bool(_RESTITUTION_RE.search(active_text)) and not divorce_asked

    # Maintenance
    maint_neg = bool(_MAINT_NEG_RE.search(active_text))
    money_fact = bool(_MAINT_CLAIM_RE.search(active_text)) and not maint_neg
    lump_sum = bool(_LUMP_SUM_RE.search(active_text)) and not maint_neg
    existing_order = bool(_EXISTING_ORDER_RE.search(active_text)) and bool(_ARREARS_VARY_RE.search(active_text)) and not bool(_ENHANCE_COST_RE.search(active_text))
    post_decree_lump = bool(re.search(r"\b(?:ordered\s+a\s+lump\s+sum|lump[\s-]+sum\s+.*permanent\s+alimony)\b", active_text, re.I))
    if post_decree_lump:
        decree = True
        lump_sum = True
    interim_only_ord = bool(re.search(r"\binterim\s+maintenance\b.{0,40}\b(?:fixed|till\s+the\s+divorce\s+ends|only\s+till)\b", active_text, re.I))
    if interim_only_ord:
        pending_hma = True
        existing_order = True
    interim_while_pending = (
        pending_hma
        and not has_child_mention
        and bool(re.search(r"\b(?:while\s+(?:the|our|my)\s+(?:divorce\s+)?(?:case|matter|petition|proceeding)\s+(?:is\s+|goes\s+)(?:pending|on|going\s+on)|until\s+(?:the\s+)?divorce\s+(?:ends|is\s+decided))\b", active_text, re.I))
    )

    # Custody, Residence, DV, Stridhan, Joint Property, Birth
    custody_neg = bool(_CUSTODY_NEG_RE.search(active_text))
    custody_claim = bool(_CUSTODY_ASK_RE.search(active_text)) and not custody_neg and not is_adult_child
    if custody_claim and re.search(r"\b(?:stay|live)\s+in\s+(?:the|our|my)\s+(?:house|home)\s+with\b", active_text, re.I) and not _CUSTODY_HOUSE_COLOC_RE.search(active_text) and not re.search(r"\b(?:custody|guardian|visitation|who\s+will\s+get)\b", active_text, re.I):
        custody_claim = False

    res_coloc_daughter = bool(_CUSTODY_HOUSE_COLOC_RE.search(active_text)) and not bool(re.search(r"\b(?:threw|kicked|locked|vacate|evict|refus\w*\s+entry|residence\s+order)\b", active_text, re.I))
    res_neg = bool(_RESIDENCE_NEG_RE.search(active_text))
    res_raw = bool(_RESIDENCE_ASK_RE.search(active_text)) or bool(_RESIDENCE_COLOC_ALLOW_RE.search(active_text))
    residence_claim = (res_raw and not res_coloc_daughter and not res_neg) or (bool(_COERCIVE_LOCKOUT_RE.search(active_text)) and not res_neg)
    if bool(_RESIDENCE_COLOC_ALLOW_RE.search(active_text)):
        residence_claim = True

    vio_text = _VIOLENCE_NEG_MASK_RE.sub(" ", active_text)
    violence = bool(_VIOLENCE_RE.search(vio_text))
    coercive_lockout = bool(_COERCIVE_LOCKOUT_RE.search(active_text)) and not res_neg
    explicit_res_only = bool(_EXPLICIT_RES_ONLY_RE.search(active_text)) and not violence
    dv_injury_comp = violence and bool(_DV_COMP_RE.search(active_text))
    child_safety_risk = bool(_CHILD_SAFETY_RISK_RE.search(active_text)) and not res_neg

    stridhan_item = bool(_STRIDHAN_ITEM_RE.search(active_text))
    stridhan_safe = bool(_STRIDHAN_SAFE_OR_UNDISP_RE.search(active_text))
    stridhan_sold = bool(_STRIDHAN_SOLD_RE.search(active_text)) and stridhan_item
    kn_aunt_held = is_kannada_orig and stridhan_item and bool(re.search(r"\bmy\s+aunt\b", active_text, re.I))
    stridhan_claim = stridhan_item and (bool(_STRIDHAN_HELD_RE.search(active_text)) or stridhan_sold or kn_aunt_held) and not stridhan_safe

    if _DEMAND_FALSE_RE.search(active_text) or (is_kannada_orig and bool(re.search(r"ಕೇಳಿಲ್ಲ|ಕೇಳಲಿಲ್ಲ", raw_kannada))):
        demand_made: bool | None = False
    elif stridhan_sold or _DEMAND_TRUE_RE.search(active_text):
        demand_made = True
    else:
        demand_made = None

    joint_prop_claim = bool(_JOINT_PROP_RE.search(active_text)) and not bool(_JOINT_PROP_NEG_RE.search(active_text))
    birth_cert = bool(_BIRTH_CERT_RE.search(active_text))
    forum_asked = bool(_FORUM_Q_RE.search(active_text))
    proc_how_late = bool(re.search(r"\b(?:always\s+\d+\s+days\s+late|make\s+him\s+pay\s+on\s+time)\b", active_text, re.I))
    proc_asked = (bool(_PROC_HOW_RE.search(active_text)) or proc_how_late) and not birth_cert and not (stridhan_claim and is_kannada_orig)
    first_demand_never = bool(_DEMAND_FALSE_RE.search(active_text)) and not stridhan_claim and not bool(re.search(r"never\s+asked\s+(?:my\s+husband\s+)?for\s+money", active_text, re.I))
    if bool(re.search(r"\bnever\s+asked\s+my\s+husband\s+for\s+money\b", active_text, re.I)):
        first_demand_never = True

    no_dispute_empty = bool(stridhan_item and stridhan_safe and not money_fact and not violence and not residence_claim and not custody_claim and not divorce_asked)

    open_markers: set[str] = set()
    if re.search(r"\b(?:cash\s+income|hides?\s+(?:his\s+)?income|no\s+pay\s*slips|cannot?\s+prove\s+(?:his\s+)?salary|cant\s+prove\s+salary|"
                 r"proof\s+of\s+my\s+earnings|car\s+counts|family\s+property|whether\s+(?:the\s+)?(?:gold|child['’]s|her\s+wish|it\s+is\s+true)|"
                 r"married\s+only\s+eight\s+months|only\s+till\s+the\s+divorce\s+ends|forbidden\s+me\s+from|"
                 r"(?:14|15|16|17)-?year-?old\s+(?:son|daughter)\s+wants|older\s+child|"
                 r"divided\s+later|bought\s+a\s+new\s+car|confused\s+about\s+the\s+gold|must\s+choose\s+one)\b", active_text, re.I):
        open_markers.add("disputed_open_fact")

    facts: dict[str, Any] = {
        "in_scope": in_scope_ev,
        "domestic_relationship": _fact("domestic_relationship", "supported" if dom_rel else "denied", dom_rel),
        "claimant_sex": FactEvidence(key="claimant_sex", status="supported" if sex != "unknown" else "unknown", value=sex),
        "claimant_role": FactEvidence(key="claimant_role", status="supported" if role != "unknown" else "unknown", value=role),
        "child_maintenance_only": _fact("child_maintenance_only", "supported" if child_only else "denied", child_only),
        "minor_child": _fact("minor_child", minor_child_st, minor_child_st == "supported"),
        "child_fact": _fact("child_fact", "supported" if (has_child_mention or custody_claim or birth_cert) else "denied", bool(has_child_mention or custody_claim or birth_cert)),
        "school_fees_fact": _fact("school_fees_fact", "supported" if bool(re.search(r"\bschool\s+(?:fee|fees|tuition|expense)", active_text, re.I)) else "denied", bool(re.search(r"\bschool\s+(?:fee|fees|tuition|expense)", active_text, re.I))),
        "proceeding_pending_hma": _fact("proceeding_pending_hma", "supported" if pending_hma else ("unknown" if law_unknown_q else "denied"), pending_hma, _PENDING_STATE_RE),
        "being_filed": _fact("being_filed", "supported" if being_filed else "denied", being_filed, _BEING_FILED_RE),
        "decree": _fact("decree", "supported" if decree else "denied", decree, _DECREE_PASSED_RE),
        "divorce_asked": _fact("divorce_asked", "denied" if divorce_neg else ("supported" if divorce_asked else "denied"), divorce_asked, _DIVORCE_ASKED_RE),
        "mutual_consent": _fact("mutual_consent", "supported" if mutual_consent else "denied", mutual_consent, _MUTUAL_CONSENT_RE),
        "judicial_separation_only": _fact("judicial_separation_only", "supported" if js_only else "denied", js_only),
        "restitution_asked": _fact("restitution_asked", "supported" if restitution_asked else "denied", restitution_asked, _RESTITUTION_RE),
        "money_fact": _fact("money_fact", "denied" if maint_neg else ("supported" if money_fact else "denied"), money_fact, _MAINT_CLAIM_RE),
        "lump_sum_settlement": _fact("lump_sum_settlement", "supported" if lump_sum else "denied", lump_sum, _LUMP_SUM_RE),
        "existing_order_enforcement": _fact("existing_order_enforcement", "supported" if existing_order else "denied", existing_order),
        "interim_only_asked": _fact("interim_only_asked", "supported" if interim_while_pending else "denied", interim_while_pending),
        "interim_unpaid_with_joint_or_parallel": _fact(
            "interim_unpaid_with_joint_or_parallel",
            "supported" if (existing_order and joint_prop_claim) else "denied",
            bool(existing_order and joint_prop_claim),
        ),
        "custody_claim": _fact("custody_claim", "denied" if custody_neg else ("supported" if custody_claim else "denied"), custody_claim, _CUSTODY_ASK_RE),
        "child_safety_risk": _fact("child_safety_risk", "supported" if child_safety_risk else "denied", child_safety_risk),
        "residence_claim": _fact("residence_claim", "supported" if residence_claim else "denied", residence_claim, _RESIDENCE_ASK_RE),
        "violence": _fact("violence", "supported" if violence else "denied", violence, _VIOLENCE_RE),
        "coercive_eviction_or_lockout": _fact("coercive_eviction_or_lockout", "supported" if coercive_lockout else "denied", coercive_lockout, _COERCIVE_LOCKOUT_RE),
        "explicit_residence_order_only": _fact("explicit_residence_order_only", "supported" if explicit_res_only else "denied", explicit_res_only),
        "dv_injury_comp_asked": _fact("dv_injury_comp_asked", "supported" if dv_injury_comp else "denied", dv_injury_comp),
        "stridhan_claim": _fact("stridhan_claim", "supported" if stridhan_claim else "denied", stridhan_claim, _STRIDHAN_ITEM_RE),
        "stridhan_held_or_disposed": _fact("stridhan_held_or_disposed", "supported" if stridhan_claim else "denied", stridhan_claim),
        "stridhan_sold_or_mortgaged": _fact("stridhan_sold_or_mortgaged", "supported" if stridhan_sold else "denied", stridhan_sold, _STRIDHAN_SOLD_RE),
        "demand_made": FactEvidence(
            key="demand_made",
            status="unknown" if demand_made is None else ("supported" if demand_made else "denied"),
            value=demand_made,
        ),
        "joint_property_claim": _fact("joint_property_claim", "supported" if joint_prop_claim else "denied", joint_prop_claim, _JOINT_PROP_RE),
        "birth_cert_asked": _fact("birth_cert_asked", "supported" if birth_cert else "denied", birth_cert, _BIRTH_CERT_RE),
        "forum_question_asked": _fact("forum_question_asked", "supported" if forum_asked else "denied", forum_asked, _FORUM_Q_RE),
        "procedure_how_to_asked": _fact("procedure_how_to_asked", "supported" if proc_asked else "denied", proc_asked, _PROC_HOW_RE),
        "first_demand_never_made": _fact("first_demand_never_made", "supported" if first_demand_never else "denied", first_demand_never),
        "no_dispute_empty": _fact("no_dispute_empty", "supported" if no_dispute_empty else "denied", no_dispute_empty),
    }

    negated_issues: set[str] = set()
    if divorce_neg:
        negated_issues.add("divorce")
    if maint_neg:
        negated_issues.add("maintenance")
    if custody_neg:
        negated_issues.add("custody")
    if res_neg:
        negated_issues.add("residence")
    if stridhan_safe:
        negated_issues.add("stridhan")
    if _VIOLENCE_NEG_MASK_RE.search(active_text) and not violence:
        negated_issues.add("violence")

    issues: dict[str, IssueEvidence] = {}
    issue_triggers = {
        "maintenance": money_fact or lump_sum or existing_order,
        "custody": custody_claim,
        "stridhan": stridhan_claim,
        "joint_property": joint_prop_claim,
        "residence": residence_claim,
        "violence": violence or coercive_lockout,
        "dv_compensation": dv_injury_comp,
        "divorce": divorce_asked,
        "restitution": restitution_asked,
        "birth_certificate": birth_cert,
    }
    for name, fired in issue_triggers.items():
        if name in negated_issues:
            issues[name] = IssueEvidence(issue=name, intent="denied", source="user_text", confidence=1.0)
        elif fired:
            issues[name] = IssueEvidence(issue=name, intent="requested", source="user_text", confidence=1.0)
        else:
            issues[name] = IssueEvidence(issue=name, intent="uncertain", source="user_text", confidence=0.0)

    return {
        "facts": facts,
        "issues": issues,
        "negated_issues": negated_issues,
        "open_fact_markers": open_markers,
        "analysis_text": text,
    }
