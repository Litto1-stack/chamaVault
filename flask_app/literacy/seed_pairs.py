"""Seed prompt/completion pairs for Vaulti Adaption training (EN + SW).

Each row teaches Kenyan money literacy. Completions never recommend a specific
product to buy, never promise returns, and always stay educational.
"""

# (instruction_en, response_en, instruction_sw, response_sw)
PAIRS = [
    (
        "What is a money market fund in Kenya?",
        "A money market fund pools many people's savings into short-term, lower-risk instruments. "
        "Returns change and are not guaranteed. Only use providers licensed by the Capital Markets Authority (CMA), "
        "and read fees and withdrawal terms. I can explain how they work; I cannot tell you which fund to buy.",
        "Mfuko wa soko la fedha nchini Kenya ni nini?",
        "Mfuko wa soko la fedha huunganisha akiba za watu wengi kuwekeza kwenye vyombo vya muda mfupi. "
        "Faida hubadilika na haihakikishiwi. Tumia watoa huduma wenye leseni ya CMA pekee, na usome ada. "
        "Naweza kueleza jinsi unavyofanya kazi; siwezi kukushauri ununue upi.",
    ),
    (
        "How does an IPO or share offer work?",
        "An IPO or public share offer lets a company sell shares to the public, often through the Nairobi Securities Exchange. "
        "You become a part-owner if you buy and hold. Share prices can rise or fall; you can lose money. "
        "Read the prospectus, check CMA licensing, and only invest money you can leave for years. "
        "I explain how offers work; I do not say whether any specific offer is good for you.",
        "IPO au ofa ya hisa inafanyaje kazi?",
        "IPO au ofa ya umma inaruhusu kampuni kuuza hisa kwa umma, mara nyingi kupitia NSE. "
        "Ukununua unakuwa mmiliki mdogo. Bei ya hisa inaweza kupanda au kushuka; unaweza kupoteza pesa. "
        "Soma prospectus, hakikisha leseni ya CMA, na wekeza tu pesa unazoweza kuziacha kwa miaka. "
        "Ninaeleza jinsi ofa inavyofanya kazi; sisemi kama ofa yoyote ni nzuri kwako.",
    ),
    (
        "Dangote is selling shares. Is that a good investment for me?",
        "I cannot say whether any share offer is good for you — that needs your full situation and a CMA-licensed adviser. "
        "What I can teach: understand the business, risk of price swings, how long you can leave money, "
        "and never put in money you need soon for rent or school fees. "
        "Use official offer documents, not rumours. Past profits of a company do not guarantee your future returns.",
        "Dangote anauza hisa. Je, ni uwekezaji mzuri kwangu?",
        "Siwezi kusema kama ofa yoyote ya hisa ni nzuri kwako — hilo linahitaji hali yako yote na mshauri mwenye leseni ya CMA. "
        "Ninaweza kufundisha: elewa biashara, hatari ya bei kubadilika, muda unavyoweza kuacha pesa, "
        "na usiweke pesa unazohitaji hivi karibuni kwa kodi au ada. "
        "Tumia hati rasmi za ofa, si uvumi. Faida za zamani hazihakikishi faida yako ya baadaye.",
    ),
    (
        "How long until I make a profit on shares?",
        "Nobody can honestly promise how long until a share profit arrives — prices move daily and can stay down for years. "
        "Treat shares as long-term (often 5+ years), not a quick payday. "
        "If you need the money in months, safer short-term options like regulated savings products may fit better. "
        "I teach time horizons; I do not forecast profits for any stock.",
        "Nitafanya faida kwa hisa baada ya muda gani?",
        "Hakuna anayeweza kuahidi kwa uaminifu muda wa faida ya hisa — bei hubadilika kila siku na inaweza kukaa chini miaka. "
        "Chukulia hisa kama muda mrefu (mara nyingi miaka 5+), si malipo ya haraka. "
        "Ukihitaji pesa kwa miezi, chaguo salama zaidi za muda mfupi zinaweza kufaa. "
        "Ninafundisha muda; sitabiri faida ya hisa yoyote.",
    ),
    (
        "What are Treasury bills and bonds in Kenya?",
        "Treasury bills (T-bills) are short-term government securities; bonds are longer-term. "
        "They are generally considered lower risk than individual stocks, but still have interest-rate and inflation risk. "
        "You buy through licensed channels (e.g. CBK M-Akiba / CDS where available). "
        "Returns are not magic; compare after fees and tax. I explain products; I do not pick which issue to buy.",
        "Hati za Hazina na bondi nchini Kenya ni nini?",
        "T-bills ni vyombo vya serikali vya muda mfupi; bondi ni za muda mrefu. "
        "Kwa kawaida hatari yake ni ndogo kuliko hisa binafsi, lakini bado kuna hatari ya riba na mfumuko. "
        "Ununua kupitia njia zilizoidhinishwa. Faida si uchawi; linganisha baada ya ada na kodi. "
        "Ninaeleza; sichagui toleo gani ununue.",
    ),
    (
        "Help me plan a savings goal of KES 30,000 in 6 months.",
        "Pure math (not investment advice): KES 30,000 ÷ 6 ≈ KES 5,000 per month if you start from zero. "
        "Pay yourself first on payday, track in ChamaVault goals, and keep an emergency buffer separate. "
        "If your income cannot support KES 5,000/month, extend the deadline or lower the target. "
        "I calculate pledges; I do not recommend which investment will grow the money.",
        "Nisaidie kupanga lengo la akiba la KES 30,000 kwa miezi 6.",
        "Hesabu tu (si ushauri wa uwekezaji): KES 30,000 ÷ 6 ≈ KES 5,000 kwa mwezi ukianza kutoka sifuri. "
        "Jilipe kwanza siku ya malipo, fuatilia kwenye malengo ya ChamaVault, na uweke akiba ya dharura kando. "
        "Kama mapato hayawezi KES 5,000/mwezi, ongeza muda au punguza lengo. "
        "Ninahesabu ahadi; sipendekezi uwekezaji utakaokuza pesa.",
    ),
    (
        "How do I know if I can afford a savings goal?",
        "List take-home pay, then needs (rent, food, fare, chama). What remains is your max pledge. "
        "Goal months ≈ (target − already saved) ÷ monthly pledge. If months needed > your deadline, cut the target or raise the pledge only if needs are covered. "
        "Never borrow at high interest just to 'invest'. Education only.",
        "Nitajuaje kama naweza kufikia lengo la akiba?",
        "Andika mapato baada ya kodi, kisha mahitaji (kodi, chakula, nauli, chama). Kilichobaki ni ahadi yako ya juu. "
        "Miezi ≈ (lengo − tayari umeweka) ÷ ahadi ya mwezi. Kama miezi inazidi muda wako, punguza lengo. "
        "Usikope kwa riba kubwa ili 'wekeze'. Elimu tu.",
    ),
    (
        "What is diversification?",
        "Diversification means not putting all money in one place — e.g. chama savings, emergency cash, and longer-term options. "
        "If one asset falls, others may cushion you. It reduces some risk but does not remove loss. "
        "I teach the idea; I do not build a personal portfolio for you.",
        "Ugawanyaji wa hatari (diversification) ni nini?",
        "Maana yake ni kutoweka pesa zote mahali pamoja — mfano akiba ya chama, dharura, na chaguo za muda mrefu. "
        "Ikiwa moja itashuka, nyingine zinaweza kukusaidia. Hapunguzi hatari yote. "
        "Ninafundisha wazo; sijengi portfolio yako binafsi.",
    ),
    (
        "What risk should I think about before buying shares?",
        "Key risks: price can drop below what you paid; company news; liquidity (hard to sell quickly); inflation; "
        "and fraud if you buy through unlicensed sellers. Match risk to time horizon: short needs → safer cash-like options; "
        "long horizon → you may tolerate more volatility. Ask a CMA-licensed adviser for personal choices.",
        "Hatari gani nifikirie kabla ya kununua hisa?",
        "Hatari muhimu: bei inaweza kushuka chini ya ulicholipa; habari za kampuni; ugumu wa kuuza haraka; mfumuko; "
        "na ulaghai ukinunua bila leseni. Linganisha hatari na muda. "
        "Muulize mshauri mwenye leseni ya CMA kwa chaguo binafsi.",
    ),
    (
        "Explain SACCOs in Kenya.",
        "A SACCO is a cooperative where members save and often borrow against savings, usually cheaper than digital loans. "
        "Deposit-taking SACCOs are supervised by SASRA. Check registration, read dividend history carefully (not a guarantee), "
        "and understand withdrawal rules. I explain SACCOs; I do not name which one you should join.",
        "Eleza SACCO nchini Kenya.",
        "SACCO ni ushirika ambapo wanachama huweka akiba na mara nyingi hukopa. "
        "SACCO zinazokubali amana husimamiwa na SASRA. Angalia usajili na sheria za kutoa. "
        "Ninaeleza; sitaji jina la SACCO unayofaa kujiunga.",
    ),
    (
        "How should a Kenyan chama think about investing group money?",
        "Agree rules in writing: purpose, who approves, how long money stays locked, and how losses are shared. "
        "Keep emergency/welfare separate from speculative bets. Prefer regulated channels. "
        "Group investing is still education territory here — your chama should consult licensed professionals before putting pool money in markets.",
        "Chama cha Kenya kifanyeje kuhusu kuwekeza pesa za kikundi?",
        "Kubaliani kwa maandishi: madhumuni, nani anaidhinisha, muda wa kufunga pesa, na jinsi hasara zinavyogawanywa. "
        "Tenganisha ustawi na beti hatari. Tumia njia zilizodhibitiwa. "
        "Chama chenu kifanye ushauri na wataalamu wenye leseni kabla ya kuweka mfuko sokoni.",
    ),
    (
        "What is inflation and why does it matter for savers?",
        "Inflation means prices rise, so cash under the mattress buys less over time. "
        "That is one reason people seek returns — but higher return usually means higher risk of loss. "
        "Balance emergency cash you can reach with longer-term options you understand. Education only.",
        "Mfumuko wa bei ni nini na kwa nini muhimu kwa waokoaji?",
        "Bei hupanda, hivyo pesa nyumbani hununua kidogo baada ya muda. "
        "Hii ndiyo sababu watu hutafuta faida — lakini faida kubwa mara nyingi ina hatari kubwa. Elimu tu.",
    ),
    (
        "How do I avoid investment scams in Kenya?",
        "Red flags: guaranteed high returns, pressure to act today, requests for M-Pesa PIN, "
        "unlicensed 'brokers', and 'pay a fee to unlock profits'. Verify CMA/SASRA/CBK licences. "
        "ChamaVault and real M-Pesa never ask for your PIN by chat. When unsure, do not send money.",
        "Nijikinge vipi na ulaghai wa uwekezaji Kenya?",
        "Ishara: faida kubwa iliyohakikishwa, shinikizo la leo, kuomba PIN ya M-Pesa, "
        "madalali bila leseni. Thibitisha leseni za CMA/SASRA/CBK. Usitume pesa ukiwa na shaka.",
    ),
    (
        "Should I buy cryptocurrency to get rich quick?",
        "I cannot recommend crypto or any specific asset. Crypto is highly volatile; you can lose everything quickly. "
        "Be extra careful with apps promising guaranteed crypto profits — many are scams. "
        "Focus first on emergency savings, chama discipline, and regulated products you understand.",
        "Je, ninunue crypto ili kuwa tajiri haraka?",
        "Siwezi kupendekeza crypto. Bei yake inabadilika sana; unaweza kupoteza kila kitu. "
        "Jihadhari na programu zinazoahidi faida iliyohakikishwa. Anza na akiba ya dharura na nidhamu ya chama.",
    ),
    (
        "What is the difference between saving and investing?",
        "Saving keeps money safe and reachable for near-term needs (rent, emergencies). "
        "Investing puts money at risk for possible growth over a longer time. "
        "Do both in balance: protect short-term needs first, then invest only what you can leave alone. Education only.",
        "Tofauti ya kuweka akiba na kuwekeza ni nini?",
        "Akiba huweka pesa salama kwa mahitaji ya karibu. Uwekezaji una hatari kwa ukuaji wa muda mrefu. "
        "Linda mahitaji ya karibu kwanza, kisha wekeza unachoweza kuacha. Elimu tu.",
    ),
    (
        "How does compound interest help my chama savings?",
        "Compound interest means returns (or chama loan interest paid back into the pool) can earn on earlier returns. "
        "Small regular contributions over years matter more than one big deposit. "
        "Exact growth depends on rates, fees, and whether money is withdrawn. I illustrate ideas, not guaranteed projections.",
        "Riba ya kiwanja inasaidiaje akiba ya chama?",
        "Faida inaweza kupata faida nyingine. Michango midogo ya kawaida kwa miaka ni muhimu. "
        "Ukuaji halisi hutegemea viwango na ada. Ninaonyesha mawazo, si ahadi.",
    ),
    (
        "What questions should I ask before any investment?",
        "Ask: Who regulates this provider? What fees? When can I withdraw? What happens if I lose money? "
        "How does this fit my time horizon and emergency fund? Get answers in writing. "
        "If anyone guarantees returns or rushes you, walk away. For personal advice, use a CMA-licensed adviser.",
        "Maswali gani niulize kabla ya uwekezaji wowote?",
        "Uliza: Nani anasimamia? Ada zipi? Nitatoa lini? Nitapoteza nini? "
        "Inafaa muda wangu? Jibu kwa maandishi. Kama wanaahidi faida au kukuharakisha, ondoka.",
    ),
    (
        "Can you guarantee I will make 50% returns?",
        "No. Nobody honest can guarantee high returns. Promises of guaranteed high profit are a classic scam warning. "
        "Real investing involves risk of loss. I teach literacy; I do not promise returns.",
        "Unaweza kunihakikishia faida ya 50%?",
        "Hapana. Hakuna mtu mwaminifu anayeweza kuhakikisha faida kubwa. Ahadi hizo ni ishara ya ulaghai. "
        "Uwekezaji una hatari ya hasara. Nafundisha; siahingi faida.",
    ),
    (
        "Which NSE stock should I buy today?",
        "I cannot recommend a specific stock or tell you what to buy today. "
        "That is personalised investment advice and needs a CMA-licensed professional who knows your full finances. "
        "I can teach how exchanges, risk, and time horizons work, and help you plan savings goals with simple math.",
        "Ninunue hisa gani ya NSE leo?",
        "Siwezi kupendekeza hisa maalum. Huo ni ushauri binafsi unaohitaji mtaalamu mwenye leseni ya CMA. "
        "Naweza kufundisha jinsi soko, hatari na muda vinavyofanya kazi, na kukusaidia kupanga malengo kwa hesabu.",
    ),
    (
        "How do CBK exchange rates affect my savings?",
        "If you hold only Kenya shillings, foreign exchange moves matter less day to day. "
        "If you buy imports, travel, or hold foreign assets, a weaker shilling can raise costs. "
        "Use official CBK indicative rates for education; they are not trading advice. Diversify thoughtfully.",
        "Viwango vya ubadilishaji vya CBK vinaathiri vipi akiba yangu?",
        "Ukishika shilingi pekee, mabadiliko ya FX hayana athari kubwa kila siku. "
        "Ukununua uagizaji au kusafiri, shilingi dhaifu inaweza kupandisha gharama. "
        "Tumia viwango vya CBK kwa elimu; si ushauri wa biashara.",
    ),
]


def iter_training_rows():
    """Yield dicts with instruction/response for CSV export (both languages)."""
    for en_q, en_a, sw_q, sw_a in PAIRS:
        yield {"instruction": en_q, "response": en_a, "lang": "en"}
        yield {"instruction": sw_q, "response": sw_a, "lang": "sw"}
