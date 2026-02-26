#!/usr/bin/env python3
"""
Generate multilingual seed corpora JSONL using Gemini generateContent API.

Output format per line:
{"text":"...","lang":"...","domain":"...","register":"...","style":"..."}
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import random
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable


DOMAINS = ("news", "science", "finance", "health", "education", "travel", "culture", "technology", "policy")
REGISTERS = ("formal", "colloquial", "technical", "instructional", "narrative")
STYLES = ("summary", "qa", "checklist", "memo", "opinion", "report", "analysis")

LANG_LABEL = {
    "en": "English",
    "es": "Spanish",
    "zh": "Simplified Chinese",
    "ja": "Japanese",
    "ar": "Arabic",
    "fr": "French",
    "pt": "Portuguese",
    "hi": "Hindi",
}

WRITING_PROFILES_FALLBACK = (
    {
        "id": "field_notes",
        "instruction": "Write like direct field notes: concrete observations, sparse interpretation, high specificity.",
    },
    {
        "id": "investigative_brief",
        "instruction": "Write like an investigative brief: evidence-led, cross-checked claims, careful qualification.",
    },
    {
        "id": "historical_narrative",
        "instruction": "Write with historical narrative cadence: temporal anchors, contextual transitions, grounded detail.",
    },
    {
        "id": "policy_memorandum",
        "instruction": "Write as a policy memo: constraints, trade-offs, and implementation implications.",
    },
    {
        "id": "technical_postmortem",
        "instruction": "Write as a technical postmortem: failure chain, root causes, mitigations, verification steps.",
    },
    {
        "id": "community_oral",
        "instruction": "Write in a community oral-storytelling register: lived experience, local references, vivid voice.",
    },
    {
        "id": "scientific_abstract",
        "instruction": "Write like a scientific abstract: objective framing, method hints, measured conclusions.",
    },
    {
        "id": "trade_journal",
        "instruction": "Write as a specialist trade journal entry with domain terms and practical constraints.",
    },
    {
        "id": "courtroom_digest",
        "instruction": "Write as a courtroom digest: procedural sequence, contested points, narrowly scoped inferences.",
    },
    {
        "id": "travel_dispatch",
        "instruction": "Write like a travel dispatch: place-rich sensory detail, logistical nuance, local texture.",
    },
    {
        "id": "editorial_argument",
        "instruction": "Write as an editorial argument: clear stance, counterpoints, persuasive structure.",
    },
    {
        "id": "instructional_walkthrough",
        "instruction": "Write as an instructional walkthrough: operational steps, caveats, and expected outcomes.",
    },
    {
        "id": "dialogic_reflection",
        "instruction": "Write as reflective dialogue prose without direct quotes: alternating perspectives and tensions.",
    },
    {
        "id": "cultural_critique",
        "instruction": "Write as cultural critique: symbolic interpretation, social context, careful generalization.",
    },
    {
        "id": "economic_snapshot",
        "instruction": "Write as an economic snapshot: indicators, comparison windows, uncertainty-aware claims.",
    },
    {
        "id": "speculative_scenario",
        "instruction": "Write as a plausible speculative scenario: near-future framing, constraints, concrete impacts.",
    },
)




PROMPT_MIX_RECIPES: dict[str, str] = {
    "counterfactual": "Include one plausible counterfactual angle without turning speculative fiction.",
    "regional_voice": "Use a clear regional or local voice variant within the target language.",
    "rare_lexicon": "Prefer less-common but natural vocabulary; avoid generic repeated high-frequency terms.",
    "contrastive_structure": "Use contrastive framing (before/after, baseline/intervention, center/periphery).",
    "concrete_numerics": "Anchor claims with concrete numerics, magnitudes, ranges, or timelines when natural.",
    "stakeholder_tension": "Frame at least one tension between stakeholder goals, constraints, or incentives.",
    "domain_jargon": "Inject domain-specific terms naturally and explain by context, not definitions.",
    "narrative_shift": "Use varied sentence rhythm and transition cadence; avoid uniform sentence patterns.",
    "evidence_cues": "Use evidence cues (reported, observed, measured, archived) without citation markup.",
    "edge_case_focus": "Include one edge case or failure mode and its practical consequence.",
    "cross_region_compare": "Compare two regions or contexts within the same language ecosystem.",
    "policy_tradeoff": "Present at least one explicit trade-off and a constrained decision path.",
    "operational_detail": "Include operational details (roles, process steps, constraints, handoffs).",
    "time_horizon": "Mention short-term versus long-term effects with concrete temporal markers.",
    "socio_cultural_context": "Embed social or cultural context signals relevant to the topic.",
    "risk_register": "Surface risks, mitigations, and residual uncertainty in natural prose.",
}


PROMPT_MIX_RECIPES_LOCALIZED: dict[str, dict[str, str]] = {
    "es": {
        "counterfactual": "Incluye un ángulo contrafactual plausible sin convertirlo en ficción especulativa.",
        "regional_voice": "Usa una variante regional o local clara dentro del idioma objetivo.",
        "rare_lexicon": "Prefiere vocabulario menos común pero natural; evita frases genéricas repetidas.",
        "contrastive_structure": "Usa un encuadre contrastivo (antes/después, base/intervención, centro/periferia).",
        "concrete_numerics": "Ancla afirmaciones con cifras concretas, magnitudes, rangos o plazos cuando sea natural.",
        "stakeholder_tension": "Plantea al menos una tensión entre metas, restricciones o incentivos de actores.",
        "domain_jargon": "Incorpora jerga de dominio de forma natural y aclarada por contexto.",
        "narrative_shift": "Varía ritmo y cadencia de frases; evita patrones uniformes.",
        "evidence_cues": "Usa señales de evidencia (reportado, observado, medido, archivado) sin formato de cita.",
        "edge_case_focus": "Incluye un caso límite o modo de fallo y su consecuencia práctica.",
        "cross_region_compare": "Compara dos regiones o contextos dentro del mismo ecosistema lingüístico.",
        "policy_tradeoff": "Presenta al menos un trade-off explícito y una ruta de decisión con restricciones.",
        "operational_detail": "Incluye detalles operativos (roles, pasos, restricciones, transferencias).",
        "time_horizon": "Menciona efectos de corto y largo plazo con marcadores temporales concretos.",
        "socio_cultural_context": "Integra señales de contexto social o cultural relevantes al tema.",
        "risk_register": "Expón riesgos, mitigaciones e incertidumbre residual en prosa natural.",
    },
    "fr": {
        "counterfactual": "Inclure un angle contrefactuel plausible sans basculer dans la fiction spéculative.",
        "regional_voice": "Utiliser une variante régionale ou locale nette dans la langue cible.",
        "rare_lexicon": "Privilégier un lexique moins courant mais naturel; éviter les formulations génériques répétées.",
        "contrastive_structure": "Adopter un cadrage contrastif (avant/après, base/intervention, centre/périphérie).",
        "concrete_numerics": "Ancrer les affirmations avec des chiffres, ordres de grandeur, fourchettes ou échéances.",
        "stakeholder_tension": "Montrer au moins une tension entre objectifs, contraintes ou incitations des acteurs.",
        "domain_jargon": "Intégrer du jargon métier de façon naturelle, clarifié par le contexte.",
        "narrative_shift": "Varier le rythme et la cadence des phrases; éviter les structures uniformes.",
        "evidence_cues": "Employer des marqueurs de preuve (rapporté, observé, mesuré, archivé) sans citations.",
        "edge_case_focus": "Inclure un cas limite ou un mode d'échec et sa conséquence pratique.",
        "cross_region_compare": "Comparer deux régions ou contextes dans le même écosystème linguistique.",
        "policy_tradeoff": "Présenter au moins un arbitrage explicite et une décision sous contraintes.",
        "operational_detail": "Inclure des détails opérationnels (rôles, étapes, contraintes, transferts).",
        "time_horizon": "Mentionner effets court et long terme avec repères temporels concrets.",
        "socio_cultural_context": "Intégrer des signaux de contexte socio-culturel pertinents.",
        "risk_register": "Exposer risques, mitigations et incertitude résiduelle en prose naturelle.",
    },
    "pt": {
        "counterfactual": "Inclua um ângulo contrafactual plausível sem virar ficção especulativa.",
        "regional_voice": "Use uma variante regional/local clara dentro do idioma alvo.",
        "rare_lexicon": "Prefira léxico menos comum, porém natural; evite frases genéricas repetidas.",
        "contrastive_structure": "Use enquadramento contrastivo (antes/depois, base/intervenção, centro/periferia).",
        "concrete_numerics": "Ancore afirmações com números concretos, magnitudes, intervalos ou prazos.",
        "stakeholder_tension": "Mostre ao menos uma tensão entre metas, restrições ou incentivos de atores.",
        "domain_jargon": "Insira jargão de domínio de forma natural e compreensível pelo contexto.",
        "narrative_shift": "Varie ritmo e cadência das frases; evite padrões uniformes.",
        "evidence_cues": "Use pistas de evidência (relatado, observado, medido, arquivado) sem citações formais.",
        "edge_case_focus": "Inclua um caso limite ou modo de falha e sua consequência prática.",
        "cross_region_compare": "Compare duas regiões/contextos no mesmo ecossistema linguístico.",
        "policy_tradeoff": "Apresente pelo menos um trade-off explícito e decisão sob restrições.",
        "operational_detail": "Inclua detalhes operacionais (papéis, etapas, restrições, handoffs).",
        "time_horizon": "Mencione efeitos de curto e longo prazo com marcadores temporais concretos.",
        "socio_cultural_context": "Inclua sinais de contexto sociocultural relevantes ao tema.",
        "risk_register": "Explicite riscos, mitigação e incerteza residual em prosa natural.",
    },
    "ar": {
        "counterfactual": "أضف زاوية افتراضية محتملة دون تحويل النص إلى خيال مضاربي.",
        "regional_voice": "استخدم نبرة محلية/إقليمية واضحة داخل اللغة المستهدفة.",
        "rare_lexicon": "فضّل مفردات أقل شيوعًا ولكن طبيعية وتجنب الصيغ العامة المكررة.",
        "contrastive_structure": "استخدم بناءً مقارنًا (قبل/بعد، خط أساس/تدخل، مركز/هامش).",
        "concrete_numerics": "اسند الادعاءات بأرقام أو نطاقات أو جداول زمنية ملموسة عندما يكون ذلك طبيعيًا.",
        "stakeholder_tension": "أبرز توترًا واحدًا على الأقل بين أهداف أو قيود أو حوافز الجهات المعنية.",
        "domain_jargon": "أدرج مصطلحات تخصصية بشكل طبيعي ومفهوم من السياق.",
        "narrative_shift": "نوّع إيقاع الجمل والانتقال بينها وتجنب النمط الموحد.",
        "evidence_cues": "استخدم إشارات أدلة مثل: مُبلّغ، مُلاحظ، مُقاس، مُؤرشف دون تنسيق اقتباس.",
        "edge_case_focus": "ضمّن حالة طرفية أو نمط فشل وتأثيره العملي.",
        "cross_region_compare": "قارن بين منطقتين أو سياقين داخل نفس البيئة اللغوية.",
        "policy_tradeoff": "اعرض مقايضة واضحة واحدة على الأقل ومسار قرار تحت قيود.",
        "operational_detail": "أضف تفاصيل تشغيلية (الأدوار، الخطوات، القيود، التسليمات).",
        "time_horizon": "اذكر آثار المدى القصير والطويل مع مؤشرات زمنية ملموسة.",
        "socio_cultural_context": "ادمج إشارات سياق اجتماعي/ثقافي مرتبطة بالموضوع.",
        "risk_register": "اعرض المخاطر والتخفيف وعدم اليقين المتبقي بصياغة طبيعية.",
    },
    "hi": {
        "counterfactual": "कल्पनात्मक कथा बनाए बिना एक यथार्थ प्रतिकल्पित कोण शामिल करें।",
        "regional_voice": "लक्षित भाषा के भीतर स्पष्ट क्षेत्रीय/स्थानीय शैली का उपयोग करें।",
        "rare_lexicon": "कम प्रचलित लेकिन स्वाभाविक शब्दावली चुनें; दोहराए गए सामान्य वाक्यांशों से बचें।",
        "contrastive_structure": "विरोधी संरचना अपनाएँ (पहले/बाद में, बेसलाइन/हस्तक्षेप, केंद्र/परिधि)।",
        "concrete_numerics": "जहाँ स्वाभाविक हो, दावों को ठोस संख्याओं/रेंज/समय-सीमा से जोड़ें।",
        "stakeholder_tension": "हितधारकों के लक्ष्य, बाधाएँ या प्रोत्साहनों के बीच कम से कम एक तनाव दिखाएँ।",
        "domain_jargon": "डोमेन-विशिष्ट शब्दावली स्वाभाविक रूप से शामिल करें और संदर्भ से स्पष्ट करें।",
        "narrative_shift": "वाक्य-लय और संक्रमण में विविधता रखें; एकरूप पैटर्न से बचें।",
        "evidence_cues": "साक्ष्य संकेतों का उपयोग करें (रिपोर्टेड, अवलोकित, मापा, अभिलेखित) बिना उद्धरण-फॉर्मेट के।",
        "edge_case_focus": "एक एज-केस या विफलता-स्थिति और उसका व्यावहारिक प्रभाव शामिल करें।",
        "cross_region_compare": "एक ही भाषाई पारिस्थितिकी में दो क्षेत्रों/संदर्भों की तुलना करें।",
        "policy_tradeoff": "कम से कम एक स्पष्ट ट्रेड-ऑफ और सीमाओं के भीतर निर्णय-पथ प्रस्तुत करें।",
        "operational_detail": "संचालन संबंधी विवरण दें (भूमिकाएँ, चरण, बाधाएँ, हैंडऑफ)।",
        "time_horizon": "अल्पकालिक और दीर्घकालिक प्रभावों को ठोस समय-संकेतों के साथ बताएं।",
        "socio_cultural_context": "विषय से जुड़े सामाजिक/सांस्कृतिक संदर्भ संकेत शामिल करें।",
        "risk_register": "जोखिम, शमन और अवशिष्ट अनिश्चितता को स्वाभाविक गद्य में प्रस्तुत करें।",
    },
    "zh": {
        "counterfactual": "加入一个可信的反事实角度，但不要写成科幻推演。",
        "regional_voice": "在目标语言内部使用明确的地域/地方表达风格。",
        "rare_lexicon": "优先使用较少见但自然的词汇，避免泛化且重复的高频套话。",
        "contrastive_structure": "使用对比结构（前后、基线/干预、中心/边缘）。",
        "concrete_numerics": "在自然场景下用具体数字、区间、量级或时间线支撑表述。",
        "stakeholder_tension": "至少体现一个利益相关方目标、约束或激励之间的张力。",
        "domain_jargon": "自然嵌入领域术语，并通过语境让其可理解。",
        "narrative_shift": "变化句式节奏与转承方式，避免整段句法同质化。",
        "evidence_cues": "使用证据线索（报道、观察、测量、存档），但不要引用格式。",
        "edge_case_focus": "包含一个边界案例或失败模式及其实际后果。",
        "cross_region_compare": "在同一语言生态内比较两个地区或语境。",
        "policy_tradeoff": "至少呈现一个明确权衡及受约束的决策路径。",
        "operational_detail": "加入操作层细节（角色、步骤、约束、交接）。",
        "time_horizon": "用具体时间标记区分短期与长期影响。",
        "socio_cultural_context": "嵌入与主题相关的社会文化语境信号。",
        "risk_register": "以自然行文呈现风险、缓解措施与剩余不确定性。",
    },
    "ja": {
        "counterfactual": "SF調にせず、妥当な反実仮想の視点を1つ含める。",
        "regional_voice": "対象言語内で地域性のある語り口を明確に使う。",
        "rare_lexicon": "不自然にならない範囲でやや希少な語彙を使い、定型句の反復を避ける。",
        "contrastive_structure": "対比構造（前後、ベースライン/介入、中心/周縁）を取り入れる。",
        "concrete_numerics": "自然な文脈で具体的な数値・幅・規模・時期を盛り込む。",
        "stakeholder_tension": "利害関係者の目標・制約・インセンティブの緊張を少なくとも1つ示す。",
        "domain_jargon": "分野用語を自然に織り込み、文脈で理解できるようにする。",
        "narrative_shift": "文のリズムと遷移を変化させ、単調な構文を避ける。",
        "evidence_cues": "報告・観測・測定・記録などの根拠シグナルを入れる（引用形式は不要）。",
        "edge_case_focus": "エッジケースや故障モードを1つ示し、実務上の影響を書く。",
        "cross_region_compare": "同じ言語圏内で2つの地域・文脈を比較する。",
        "policy_tradeoff": "少なくとも1つの明確なトレードオフと制約下の判断経路を示す。",
        "operational_detail": "運用面の詳細（役割、手順、制約、引き継ぎ）を含める。",
        "time_horizon": "短期・長期の影響を具体的な時間指標で示す。",
        "socio_cultural_context": "テーマに関連する社会文化的文脈の手がかりを埋め込む。",
        "risk_register": "リスク、緩和策、残余不確実性を自然な文章で示す。",
    },
}


PROMPT_META_LOCALIZED: dict[str, dict[str, str]] = {
    "es": {"constraints": "Restricciones", "mix": "Directivas de mezcla de prompt (aplica todas)", "seed": "Usa estos ejemplos semilla como anclas de estilo/tema (no copies literalmente)", "json": "Devuelve SOLO JSON estricto, como arreglo de objetos con una clave: text."},
    "fr": {"constraints": "Contraintes", "mix": "Directives de mélange de prompt (appliquer toutes)", "seed": "Utiliser ces exemples graine comme ancres style/thème (sans copie verbatim)", "json": "Retourner STRICTEMENT du JSON, tableau d'objets avec une clé: text."},
    "pt": {"constraints": "Restrições", "mix": "Diretivas de mistura de prompt (aplicar todas)", "seed": "Use estes exemplos-semente como âncoras de estilo/tema (não copie literalmente)", "json": "Retorne SOMENTE JSON estrito, como array de objetos com uma chave: text."},
    "ar": {"constraints": "القيود", "mix": "تعليمات مزج الموجه (طبّق الجميع)", "seed": "استخدم أمثلة البذور كمرتكزات للأسلوب/الموضوع (دون نسخ حرفي)", "json": "أعد JSON صارمًا فقط كمصفوفة كائنات بمفتاح واحد: text."},
    "hi": {"constraints": "प्रतिबंध", "mix": "प्रॉम्प्ट-मिश्रण निर्देश (सभी लागू करें)", "seed": "इन सीड उदाहरणों को शैली/विषय एंकर की तरह उपयोग करें (शाब्दिक नकल न करें)", "json": "केवल सख्त JSON लौटाएँ: एक ही key `text` वाले objects की array."},
    "zh": {"constraints": "约束", "mix": "提示词混合指令（全部执行）", "seed": "将以下种子示例作为风格/主题锚点（不要逐字复用）", "json": "只返回严格 JSON：对象数组，每个对象仅含 key `text`。"},
    "ja": {"constraints": "制約", "mix": "プロンプト混合ディレクティブ（すべて適用）", "seed": "次のシード例を文体・話題のアンカーとして使う（逐語コピー禁止）", "json": "厳密なJSONのみを返す。キーは `text` のみ。"},
}


PROMPT_LINES_LOCALIZED: dict[str, dict[str, str]] = {
    "es": {
        "generate": "Genera {n} párrafos diversos solo en {label}.",
        "lang_purity": "Pureza lingüística: SOLO {label}; sin inglés salvo lang=en.",
        "domain": "Dominio: {domain}",
        "register": "Registro: {register}",
        "style": "Estilo: {style}",
        "profile": "Perfil de escritura: {profile}",
        "length": "Longitud: cada texto entre {min_chars} y {max_chars} caracteres.",
        "no_bullets": "Sin listas, sin markdown, sin etiquetas y sin metadatos en el texto.",
        "avoid_repeat": "Evita repetir frases exactas.",
        "distinct": "Sé temática y estilísticamente distinto de cada ejemplo semilla.",
        "no_reuse": "No reutilices entidades, patrones de frase ni estructura de escenario de las semillas.",
    },
    "fr": {
        "generate": "Génère {n} paragraphes variés uniquement en {label}.",
        "lang_purity": "Pureté linguistique : UNIQUEMENT {label}; pas d'anglais sauf lang=en.",
        "domain": "Domaine : {domain}",
        "register": "Registre : {register}",
        "style": "Style : {style}",
        "profile": "Profil d'écriture : {profile}",
        "length": "Longueur : chaque texte entre {min_chars} et {max_chars} caractères.",
        "no_bullets": "Pas de listes, pas de markdown, pas de balises, pas de métadonnées dans le texte.",
        "avoid_repeat": "Évite de répéter des formulations exactes.",
        "distinct": "Sois distinct sur le fond et le style par rapport à chaque graine.",
        "no_reuse": "Ne réutilise pas entités, schémas phrastiques ni structure de scénario des graines.",
    },
    "pt": {
        "generate": "Gere {n} parágrafos diversos somente em {label}.",
        "lang_purity": "Pureza linguística: SOMENTE {label}; sem inglês, exceto lang=en.",
        "domain": "Domínio: {domain}",
        "register": "Registro: {register}",
        "style": "Estilo: {style}",
        "profile": "Perfil de escrita: {profile}",
        "length": "Tamanho: cada texto entre {min_chars} e {max_chars} caracteres.",
        "no_bullets": "Sem listas, sem markdown, sem tags e sem metadados no texto.",
        "avoid_repeat": "Evite repetir frases exatas.",
        "distinct": "Seja tematicamente e estilisticamente distinto de cada semente.",
        "no_reuse": "Não reutilize entidades, padrões frasais nem estrutura de cenário das sementes.",
    },
    "ar": {
        "generate": "أنشئ {n} فقرات متنوعة باللغة {label} فقط.",
        "lang_purity": "نقاء اللغة: {label} فقط؛ لا تستخدم الإنجليزية إلا إذا كان lang=en.",
        "domain": "المجال: {domain}",
        "register": "السجل: {register}",
        "style": "الأسلوب: {style}",
        "profile": "ملف الكتابة: {profile}",
        "length": "الطول: كل نص بين {min_chars} و {max_chars} حرفًا.",
        "no_bullets": "بدون قوائم أو Markdown أو وسوم أو بيانات وصفية داخل النص.",
        "avoid_repeat": "تجنب تكرار العبارات نفسها حرفيًا.",
        "distinct": "اجعل النص مختلفًا موضوعيًا وأسلوبيًا عن كل مثال بذري.",
        "no_reuse": "لا تعِد استخدام الكيانات أو أنماط الصياغة أو بنية السيناريو من البذور.",
    },
    "hi": {
        "generate": "केवल {label} में {n} विविध अनुच्छेद तैयार करें।",
        "lang_purity": "भाषाई शुद्धता: केवल {label}; अंग्रेज़ी नहीं (सिर्फ lang=en में अनुमति)।",
        "domain": "डोमेन: {domain}",
        "register": "रजिस्टर: {register}",
        "style": "शैली: {style}",
        "profile": "लेखन प्रोफ़ाइल: {profile}",
        "length": "लंबाई: प्रत्येक पाठ {min_chars} से {max_chars} वर्णों के बीच हो।",
        "no_bullets": "कोई बुलेट सूची, markdown, टैग या मेटाडेटा नहीं।",
        "avoid_repeat": "एक जैसी पंक्तियाँ/वाक्यांश दोहराने से बचें।",
        "distinct": "हर seed उदाहरण से विषय और शैली दोनों में स्पष्ट रूप से अलग रहें।",
        "no_reuse": "seed से entities, phrase patterns या scenario संरचना पुन: उपयोग न करें।",
    },
    "zh": {
        "generate": "仅使用{label}生成 {n} 条多样化段落文本。",
        "lang_purity": "语言纯度：仅限{label}；除 lang=en 外不得使用英文。",
        "domain": "领域：{domain}",
        "register": "语体：{register}",
        "style": "风格：{style}",
        "profile": "写作画像：{profile}",
        "length": "长度：每条文本为 {min_chars} 到 {max_chars} 字符。",
        "no_bullets": "不要使用列表、Markdown、标签或元数据。",
        "avoid_repeat": "避免重复完全相同的短语。",
        "distinct": "在主题和风格上都要与每个种子示例明显不同。",
        "no_reuse": "不要复用种子中的实体、措辞模式或情境结构。",
    },
    "ja": {
        "generate": "{label}のみで多様な段落テキストを {n} 本生成してください。",
        "lang_purity": "言語純度: {label}のみ。lang=en 以外では英語を使わない。",
        "domain": "ドメイン: {domain}",
        "register": "レジスター: {register}",
        "style": "スタイル: {style}",
        "profile": "文体プロファイル: {profile}",
        "length": "長さ: 各テキストは {min_chars}〜{max_chars} 文字。",
        "no_bullets": "箇条書き・Markdown・タグ・メタデータを含めない。",
        "avoid_repeat": "同一フレーズの反復を避ける。",
        "distinct": "各シード例と話題・文体の両面で明確に差別化する。",
        "no_reuse": "シードの固有名詞、言い回しパターン、シナリオ構造を再利用しない。",
    },
}


def _prompt_line(lang: str, key: str, fallback: str, **kwargs) -> str:
    tmpl = PROMPT_LINES_LOCALIZED.get(lang, {}).get(key, fallback)
    return str(tmpl).format(**kwargs)


def _prompt_mix_instruction(recipe_id: str, lang: str) -> str:
    loc = PROMPT_MIX_RECIPES_LOCALIZED.get(lang, {})
    if recipe_id in loc:
        return str(loc[recipe_id])
    return str(PROMPT_MIX_RECIPES.get(recipe_id, recipe_id))


def _prompt_meta(lang: str, key: str, fallback: str) -> str:
    return str(PROMPT_META_LOCALIZED.get(lang, {}).get(key, fallback))
def _load_writing_profiles(path: Path) -> list[dict]:
    if not path.exists():
        return [{"id": str(p["id"]), "instructions": {"default": str(p["instruction"])}} for p in WRITING_PROFILES_FALLBACK]
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return [{"id": str(p["id"]), "instructions": {"default": str(p["instruction"])}} for p in WRITING_PROFILES_FALLBACK]
    raw = obj.get("profiles", [])
    out: list[dict] = []
    if not isinstance(raw, list):
        return [{"id": str(p["id"]), "instructions": {"default": str(p["instruction"])}} for p in WRITING_PROFILES_FALLBACK]
    for p in raw:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id", "")).strip()
        inst = p.get("instructions", {})
        if not pid or not isinstance(inst, dict):
            continue
        norm: dict[str, str] = {}
        for k, v in inst.items():
            if not isinstance(k, str):
                continue
            if isinstance(v, str) and v.strip():
                norm[k.strip()] = v.strip()
        if not norm:
            continue
        out.append({"id": pid, "instructions": norm})
    if not out:
        return [{"id": str(p["id"]), "instructions": {"default": str(p["instruction"])}} for p in WRITING_PROFILES_FALLBACK]
    return out


def _pick_profile_instruction(profile: dict, lang: str) -> str:
    inst = profile.get("instructions", {})
    if not isinstance(inst, dict):
        return "balanced neutral prose"
    for key in (lang, "default", "en"):
        val = inst.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    for _, val in inst.items():
        if isinstance(val, str) and val.strip():
            return val.strip()
    return "balanced neutral prose"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        if k and k not in os.environ:
            os.environ[k] = v


def _extract_text(resp: dict) -> str:
    parts = resp.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return "\n".join(str(p.get("text", "")) for p in parts if isinstance(p, dict))


def _strip_fences(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _iter_seed_texts(path: Path) -> Iterable[str]:
    if not path.exists():
        return []
    out: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            txt = str(obj.get("text", "")).strip()
            if txt:
                out.append(txt)
    return out


def _norm(s: str) -> str:
    return " ".join(s.split()).strip().lower()


def _call_gemini(
    *,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
    timeout_s: float,
) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": float(temperature)},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def _usage_tokens(resp: dict) -> tuple[int, int, int]:
    md = resp.get("usageMetadata", {}) if isinstance(resp, dict) else {}
    if not isinstance(md, dict):
        return (0, 0, 0)
    prompt = int(md.get("promptTokenCount", 0) or 0)
    cand = int(md.get("candidatesTokenCount", 0) or 0)
    total = int(md.get("totalTokenCount", 0) or (prompt + cand))
    return (prompt, cand, total)


def _build_prompt(
    *,
    lang: str,
    domain: str,
    register: str,
    style: str,
    n: int,
    min_chars: int,
    max_chars: int,
    seed_examples: list[str],
    prompt_style: str,
    writing_profile_instruction: str,
    prompt_mix_instructions: list[str],
) -> str:
    label = LANG_LABEL.get(lang, lang)
    seeds = "\n".join(f"- {x[:700].replace(chr(10), ' ')}" for x in seed_examples) if seed_examples else "- (none)"

    style_block = ""
    if str(prompt_style).strip().lower() == "exotic":
        style_block = (
            "- Be highly creative and culturally rich: include regional idioms, niche domains, uncommon settings, and varied rhetorical voice.\n"
            "- Prefer less-generic content over bland summaries; avoid repetitive corporate phrasing.\n"
            "- Use diverse within-language variants (regional tone/register) without switching language.\n"
        )
    elif str(prompt_style).strip().lower() == "creative":
        style_block = (
            "- Be creative and varied in tone/topic, but remain coherent and realistic.\n"
            "- Prefer specific imagery/examples over generic filler.\n"
        )

    mix_block = ""
    if prompt_mix_instructions:
        mix_lines = "\n".join(f"- {x}" for x in prompt_mix_instructions)
        mix_title = _prompt_meta(lang, "mix", "Prompt-mix directives (apply all)")
        mix_block = f"- {mix_title}:\n{mix_lines}\n"

    constraints_title = _prompt_meta(lang, "constraints", "Constraints")
    seed_title = _prompt_meta(lang, "seed", "Use these seed examples as style/topic anchors (do not copy verbatim)")
    json_title = _prompt_meta(lang, "json", "Return STRICT JSON only, as an array of objects with one key: text.")

    return (
        _prompt_line(lang, "generate", "Generate {n} diverse paragraph texts in {label} only.", n=n, label=label) + "\n"
        + f"{constraints_title}:\n"
        + "- " + _prompt_line(lang, "lang_purity", "Language purity: ONLY {label}; no English unless lang=en.", label=label) + "\n"
        + "- " + _prompt_line(lang, "domain", "Domain: {domain}", domain=domain) + "\n"
        + "- " + _prompt_line(lang, "register", "Register: {register}", register=register) + "\n"
        + "- " + _prompt_line(lang, "style", "Style: {style}", style=style) + "\n"
        + "- " + _prompt_line(lang, "profile", "Writing profile: {profile}", profile=writing_profile_instruction) + "\n"
        + "- " + _prompt_line(lang, "length", "Length: each text {min_chars} to {max_chars} characters.", min_chars=min_chars, max_chars=max_chars) + "\n"
        + "- " + _prompt_line(lang, "no_bullets", "No bullet lists, no markdown, no tags, no metadata in text.") + "\n"
        + "- " + _prompt_line(lang, "avoid_repeat", "Avoid repeating exact phrases.") + "\n\n"
        + f"{style_block}"
        + "- " + _prompt_line(lang, "distinct", "Be topically and stylistically distinct from every seed example.") + "\n"
        + "- " + _prompt_line(lang, "no_reuse", "Do not reuse seed entities, phrase patterns, or scenario structure.") + "\n\n"
        + f"{mix_block}"
        + f"{seed_title}:\n{seeds}\n\n"
        + f"{json_title}\n"
        + "Example: [{\"text\":\"...\"},{\"text\":\"...\"}]"
    )

def _run_lang(


    *,
    lang: str,
    args: argparse.Namespace,
    api_key: str,
    out_dir: Path,
    seed_dir: Path,
    writing_profiles: list[dict],
) -> None:
    worker = threading.current_thread().name
    started_at = dt.datetime.now().isoformat(timespec="seconds")
    out_path = out_dir / f"{lang}.jsonl"
    seed_pool = list(_iter_seed_texts(seed_dir / f"{lang}.jsonl"))
    seen: set[str] = set()
    written = 0
    call_idx = 0
    cum_prompt_tok = 0
    cum_cand_tok = 0
    cum_total_tok = 0

    # Keep per-language RNG deterministic and independent for parallel runs.
    lang_seed = int(args.seed) + sum(ord(ch) for ch in str(lang))
    rng = random.Random(lang_seed)

    mode = "w"
    if out_path.exists():
        mode = "a"
        with out_path.open("r", encoding="utf-8", errors="replace") as r:
            for line in r:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                txt = str(obj.get("text", "")).strip()
                if not txt:
                    continue
                seen.add(_norm(txt))
                written += 1
    print(
        f"[{lang}] worker={worker} started_at={started_at} "
        f"seed_examples={len(seed_pool)} existing={written} target={int(args.rows_per_lang)}"
    )
    with out_path.open(mode, encoding="utf-8") as f:
        while written < int(args.rows_per_lang):
            call_idx += 1
            call_start = time.time()
            domain = rng.choice(DOMAINS)
            register = rng.choice(REGISTERS)
            style = rng.choice(STYLES)
            need = min(int(args.batch_size), int(args.rows_per_lang) - written)
            if seed_pool:
                k = min(len(seed_pool), max(1, int(args.seed_examples_per_call)))
                seed_examples = rng.sample(seed_pool, k=k)
            else:
                seed_examples = []
            profile_id = "none"
            profile_instruction = "balanced neutral prose"
            if str(args.writing_profile_mode) == "random":
                profile = rng.choice(writing_profiles)
                profile_id = str(profile["id"])
                profile_instruction = _pick_profile_instruction(profile, lang)

            prompt_mix_ids = []
            prompt_mix_instructions: list[str] = []
            if str(args.prompt_mix_mode) == "random":
                pool = [x.strip() for x in str(args.prompt_mix_pool).split(",") if x.strip() and x.strip() in PROMPT_MIX_RECIPES]
                if not pool:
                    pool = list(PROMPT_MIX_RECIPES.keys())
                k_mix = max(1, min(len(pool), int(args.prompt_mix_count)))
                prompt_mix_ids = rng.sample(pool, k=k_mix)
                prompt_mix_instructions = [_prompt_mix_instruction(mid, lang) for mid in prompt_mix_ids]
            prompt = _build_prompt(
                lang=lang,
                domain=domain,
                register=register,
                style=style,
                n=need,
                min_chars=int(args.min_chars),
                max_chars=int(args.max_chars),
                seed_examples=seed_examples,
                prompt_style=str(args.prompt_style),
                writing_profile_instruction=profile_instruction,
                prompt_mix_instructions=prompt_mix_instructions,
            )

            payload = None
            retries_used = 0
            resp_obj: dict | None = None
            for attempt in range(int(args.max_retries)):
                try:
                    resp_obj = _call_gemini(
                        api_key=api_key,
                        model=str(args.model),
                        prompt=prompt,
                        temperature=float(args.temperature),
                        timeout_s=float(args.timeout_s),
                    )
                    txt = _strip_fences(_extract_text(resp_obj))
                    payload = json.loads(txt)
                    break
                except urllib.error.HTTPError as e:
                    retries_used = attempt + 1
                    wait_s = min(90.0, 2.0 * (1.8**attempt))
                    if int(getattr(e, "code", 0)) == 429:
                        print(f"[{lang}] 429 rate limit; retry in {wait_s:.1f}s")
                    else:
                        print(f"[{lang}] HTTP {getattr(e,'code',0)}; retry in {wait_s:.1f}s")
                    time.sleep(wait_s)
                except Exception:
                    retries_used = attempt + 1
                    wait_s = min(30.0, 1.5 * (1.6**attempt))
                    time.sleep(wait_s)

            if not isinstance(payload, list):
                print(f"[{lang}] skip batch: invalid JSON payload")
                time.sleep(max(0.0, int(args.sleep_ms) / 1000.0))
                continue

            accepted = 0
            for obj in payload:
                if not isinstance(obj, dict):
                    continue
                text = str(obj.get("text", "")).strip()
                if len(text) < int(args.min_chars):
                    continue
                key = _norm(text)
                if key in seen:
                    continue
                row = {
                    "text": text,
                    "lang": lang,
                    "domain": domain,
                    "register": register,
                    "style": style,
                    "writing_profile": profile_id,
                    "prompt_mix": prompt_mix_ids,
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                seen.add(key)
                written += 1
                accepted += 1
                if written >= int(args.rows_per_lang):
                    break

            ptok, ctok, ttok = _usage_tokens(resp_obj or {})
            cum_prompt_tok += ptok
            cum_cand_tok += ctok
            cum_total_tok += ttok
            elapsed = time.time() - call_start
            print(
                f"[{lang}] worker={worker} call={call_idx} need={need} accepted={accepted} "
                f"written={written}/{int(args.rows_per_lang)} retries={retries_used} "
                f"profile={profile_id} mix={'+'.join(prompt_mix_ids) if prompt_mix_ids else 'none'} seeds={len(seed_examples)} "
                f"tok_in={ptok} tok_out={ctok} tok_total={ttok} "
                f"cum_tok={cum_total_tok} sec={elapsed:.2f}"
            )

            # Persist rows durably per batch so external row counts reflect progress.
            if accepted > 0:
                f.flush()
                os.fsync(f.fileno())

            if accepted == 0:
                print(f"[{lang}] batch produced 0 accepted rows; continuing")
            if written % 500 == 0 or written < 50:
                print(f"[{lang}] wrote {written}/{int(args.rows_per_lang)}")
            time.sleep(max(0.0, int(args.sleep_ms) / 1000.0))

    ended_at = dt.datetime.now().isoformat(timespec="seconds")
    print(
        f"[{lang}] worker={worker} ended_at={ended_at} complete -> {out_path} (rows={written}, "
        f"cum_prompt_tok={cum_prompt_tok}, cum_out_tok={cum_cand_tok}, cum_total_tok={cum_total_tok})"
    )


DEFAULT_SEED_JSONL_DIR_NEW = "gamma/projects/distillation/shared/data/raw_wikipedia"
DEFAULT_SEED_JSONL_DIR_LEGACY = "gamma/projects/embeddinggemma_subsets/data/raw_wikipedia"


def _resolve_default_seed_dir(arg_value: str) -> str:
    if str(arg_value) != DEFAULT_SEED_JSONL_DIR_NEW:
        return str(arg_value)
    new_p = Path(DEFAULT_SEED_JSONL_DIR_NEW)
    legacy_p = Path(DEFAULT_SEED_JSONL_DIR_LEGACY)
    if new_p.exists():
        print(f"[paths] seed-jsonl-dir: using new default {new_p}")
        return str(new_p)
    if legacy_p.exists():
        print(f"[paths] seed-jsonl-dir: using legacy fallback {legacy_p}")
        return str(legacy_p)
    print(f"[paths] seed-jsonl-dir: defaulting to new path {new_p} (not found yet)")
    return str(new_p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="en,es,zh,ja,ar,fr,pt,hi")
    ap.add_argument("--out-dir", default="/tmp/llm_seed_jsonl")
    ap.add_argument("--model", default="gemini-3-flash-preview")
    ap.add_argument("--rows-per-lang", type=int, default=20000)
    ap.add_argument("--batch-size", type=int, default=12, help="Texts requested per API call.")
    ap.add_argument("--min-chars", type=int, default=300)
    ap.add_argument("--max-chars", type=int, default=1200)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--timeout-s", type=float, default=60.0)
    ap.add_argument("--sleep-ms", type=int, default=200)
    ap.add_argument("--max-retries", type=int, default=5)
    ap.add_argument("--env-file", default=str(Path.home() / ".env"))
    ap.add_argument("--seed-jsonl-dir", default=DEFAULT_SEED_JSONL_DIR_NEW)
    ap.add_argument("--seed-examples-per-call", type=int, default=4)
    ap.add_argument("--prompt-style", choices=["balanced", "creative", "exotic"], default="exotic")
    ap.add_argument("--writing-profile-mode", choices=["off", "random"], default="random")
    ap.add_argument("--writing-profiles-file", default=str(Path(__file__).with_name("writing_profiles.json")))
    ap.add_argument("--prompt-mix-mode", choices=["off", "random"], default="random")
    ap.add_argument("--prompt-mix-count", type=int, default=2, help="How many prompt-mix recipes to combine per call in random mode.")
    ap.add_argument("--prompt-mix-pool", default=",".join(PROMPT_MIX_RECIPES.keys()), help="Comma-separated recipe ids available for random prompt mixing.")
    ap.add_argument("--parallel-workers", type=int, default=1, help="Number of languages to process concurrently.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    args.seed_jsonl_dir = _resolve_default_seed_dir(str(args.seed_jsonl_dir))

    _load_env_file(Path(args.env_file))
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Missing GEMINI_API_KEY (set env or provide --env-file with key).")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    seed_dir = Path(args.seed_jsonl_dir)
    writing_profiles = _load_writing_profiles(Path(args.writing_profiles_file))
    langs = [x.strip() for x in str(args.langs).split(",") if x.strip()]
    workers = max(1, int(args.parallel_workers))
    if workers == 1 or len(langs) <= 1:
        for lang in langs:
            _run_lang(
                lang=lang,
                args=args,
                api_key=api_key,
                out_dir=out_dir,
                seed_dir=seed_dir,
                writing_profiles=writing_profiles,
            )
        return 0

    print(f"[multi] running {len(langs)} languages with parallel_workers={workers}")
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [
            ex.submit(
                _run_lang,
                lang=lang,
                args=args,
                api_key=api_key,
                out_dir=out_dir,
                seed_dir=seed_dir,
                writing_profiles=writing_profiles,
            )
            for lang in langs
        ]
        for fut in cf.as_completed(futs):
            fut.result()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
