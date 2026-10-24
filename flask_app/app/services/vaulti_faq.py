"""Vaulti's local FAQ: about 15 money topics in English and Swahili (education only, no regulated advice)."""

# topic -> (keywords in either language, English answer, Swahili answer)
FAQ = {
    "budgeting": (["budget", "bajeti", "spend", "matumizi", "plan my money"],
        "Try the 50/30/20 idea: about half of income for needs (rent, food, fare), 30% for wants, 20% for savings. Write it down on payday, and pay your chama contribution first, before wants.",
        "Jaribu mpango wa 50/30/20: nusu ya mapato kwa mahitaji (kodi, chakula, nauli), 30% kwa matakwa, 20% kwa akiba. Andika siku ya malipo, na utoe mchango wa chama kwanza kabla ya matakwa."),
    "compound interest": (["compound", "interest grow", "riba", "faida ya faida", "grows"],
        "Compound interest means you earn returns on your earlier returns. KES 1,000 a month at 8% a year grows to roughly KES 150,000 in 10 years, of which about KES 30,000 is growth. Starting early matters more than starting big.",
        "Riba ya kiwanja ni faida inayopata faida nyingine. KES 1,000 kila mwezi kwa 8% kwa mwaka inakua hadi takriban KES 150,000 baada ya miaka 10, ambapo karibu KES 30,000 ni ukuaji. Kuanza mapema ni muhimu kuliko kuanza kwa kiasi kikubwa."),
    "chama rules": (["chama rule", "rules", "kanuni", "constitution", "katiba", "how does our chama"],
        "Your chama's rules are agreed by members: the monthly amount, due day, daily late penalty, and how many members must approve a loan. In ChamaVault they are fixed in the chama settings and every payment is on the ledger, so nobody has to rely on memory.",
        "Kanuni za chama chenu zinakubaliwa na wanachama: kiasi cha kila mwezi, siku ya kulipa, faini ya kila siku ya kuchelewa, na wanachama wangapi lazima waidhinishe mkopo. Katika ChamaVault zote zimewekwa wazi na kila malipo yako kwenye leja."),
    "money market funds": (["money market", "mmf", "unit trust", "mfuko wa soko la fedha"],
        "A money market fund pools many people's savings into short-term, low-risk instruments, and is usually easy to withdraw from. Returns are not guaranteed and change over time. Only use providers licensed by the Capital Markets Authority (CMA), and read the fund's fees and terms first. I can explain how they work, but I can't tell you which one to buy.",
        "Mfuko wa soko la fedha huunganisha akiba za watu wengi kuwekeza kwenye vyombo vya muda mfupi vyenye hatari ndogo, na mara nyingi ni rahisi kutoa pesa. Faida haihakikishiwi na hubadilika. Tumia watoa huduma walio na leseni ya Mamlaka ya Masoko ya Mitaji (CMA) pekee, na usome ada na masharti. Naweza kueleza jinsi unavyofanya kazi, lakini siwezi kukushauri ununue upi."),
    "loan sharks": (["loan shark", "shark", "digital loan", "mobile loan", "fuliza", "kopa", "mkopo wa simu", "shylock"],
        "Be careful with quick app loans: some charge 10-30% a month, which is huge over a year. Check the total cost (APR), whether the lender is licensed by the Central Bank of Kenya, and never pay a fee upfront to 'unlock' a loan. A chama or SACCO loan is usually far cheaper.",
        "Kuwa makini na mikopo ya haraka ya simu: mingine hutoza 10-30% kwa mwezi, ambayo ni kubwa sana kwa mwaka. Angalia gharama kamili, kama mkopeshaji ana leseni ya Benki Kuu ya Kenya, na usilipe ada mbele ili 'kufungua' mkopo. Mkopo wa chama au SACCO kwa kawaida ni nafuu zaidi."),
    "emergency fund": (["emergency", "dharura", "rainy day", "unexpected"],
        "An emergency fund covers surprises like medical bills or lost income. Aim for 3 to 6 months of basic expenses, built slowly. Keep it somewhere you can reach quickly but won't spend casually. Your chama welfare fund can be one layer of this.",
        "Akiba ya dharura hukusaidia wakati wa mambo yasiyotarajiwa kama matibabu au kupoteza kipato. Lenga gharama za miezi 3 hadi 6, ujenge polepole. Iweke mahali unapoweza kuifikia haraka lakini isitumiwe ovyo. Mfuko wa ustawi wa chama ni sehemu moja ya hili."),
    "mpesa scams": (["scam", "fraud", "mpesa scam", "wrong number", "tapeli", "ulaghai", "pin", "fake message", "reversal"],
        "Never share your M-Pesa PIN, not even with 'M-Pesa staff'. Beware of 'wrong number, please send it back' messages, fake reversal texts, and anyone asking for a fee to release winnings. Real M-Pesa messages never ask for your PIN. ChamaVault will never ask for it by SMS.",
        "Usimpe mtu yeyote PIN yako ya M-Pesa, hata 'wafanyakazi wa M-Pesa'. Jihadhari na ujumbe wa 'nimetuma kwa makosa, rudisha', ujumbe bandia wa kurejesha pesa, na yeyote anayeomba ada ili akupe zawadi. M-Pesa halisi haiombi PIN yako. ChamaVault haitakuomba PIN kwa SMS."),
    "sacco": (["sacco", "cooperative", "ushirika"],
        "A SACCO is a regulated cooperative where members save together and borrow, usually at lower rates than banks. Deposit-taking SACCOs are supervised by SASRA. Many chama members join a SACCO as a next step because loans are often a multiple of your savings.",
        "SACCO ni ushirika unaodhibitiwa ambapo wanachama huweka akiba pamoja na kukopa, kwa kawaida kwa riba ndogo kuliko benki. SACCO zinazokubali amana husimamiwa na SASRA. Wanachama wengi wa chama hujiunga na SACCO kama hatua inayofuata kwa sababu mikopo mara nyingi ni mara kadhaa ya akiba yako."),
    "credit score": (["score", "credit score", "alama", "improve my score", "rating"],
        "Your ChamaVault score rises when you pay early (+15), on time (+10), keep loan installments on schedule (+25) and hit a 3-payment streak (+20). It drops for late payments (-15), missed months (-40) and loan default (-100). It reflects your chama record only.",
        "Alama yako ya ChamaVault huongezeka ukilipa mapema (+15), kwa wakati (+10), ukilipa awamu za mkopo kwa ratiba (+25) na ukifikisha malipo 3 mfululizo (+20). Hupungua kwa kuchelewa (-15), mwezi uliokosa (-40) na kushindwa kulipa mkopo (-100). Inaonyesha rekodi yako ya chama pekee."),
    "late penalty": (["penalty", "faini", "late", "kuchelewa", "overdue"],
        "If you pay after the due day, a penalty accrues for each day late. Paying even a day early avoids it and improves your score. You can pay a part of the penalty from the payment screen.",
        "Ukilipa baada ya siku ya mwisho, faini hujilimbikiza kila siku ya kuchelewa. Kulipa hata siku moja mapema huepusha faini na kuongeza alama yako. Unaweza kulipa sehemu ya faini kupitia ukurasa wa malipo."),
    "chama loans": (["loan", "borrow", "mkopo", "kukopa", "how do loans work"],
        "Request a loan from the Loans page. Other members vote, and once enough approve, the treasurer pays it out. You repay in monthly installments with a flat interest the chama set. That interest stays in the group pool, so it benefits everyone.",
        "Omba mkopo kwenye ukurasa wa Mikopo. Wanachama wengine hupiga kura, na wakitosha kuidhinisha, mweka hazina hulipa. Unalipa kwa awamu za kila mwezi na riba isiyobadilika iliyowekwa na chama. Riba hiyo inabaki kwenye mfuko wa kikundi, hivyo inamnufaisha kila mtu."),
    "welfare fund": (["welfare", "ustawi", "funeral", "msiba", "harambee"],
        "A welfare fund is a small shared pot for emergencies like funerals or hospital bills, separate from your savings. Members pay any amount they choose. Using a shared fund avoids ad-hoc fundraising when a crisis hits.",
        "Mfuko wa ustawi ni akiba ndogo ya pamoja kwa dharura kama misiba au bili za hospitali, tofauti na akiba zako. Wanachama hulipa kiasi chochote wanachotaka. Mfuko wa pamoja huepusha michango ya dharura wakati wa msiba."),
    "saving goals": (["goal", "lengo", "save for", "kuweka akiba", "target"],
        "Give your savings a name and a number, like school fees KES 30,000 by January. Divide by the months left to see the monthly amount, then set it aside right after you get paid. Our group goal bar on the home page works the same way.",
        "Pe akiba yako jina na namba, kama ada ya shule KES 30,000 ifikapo Januari. Gawanya kwa miezi iliyobaki upate kiasi cha kila mwezi, kisha kiweke kando mara tu unapolipwa. Upau wa lengo la kikundi kwenye ukurasa wa mwanzo hufanya kazi vivyo hivyo."),
    "inflation": (["inflation", "mfumuko", "prices rise", "bei"],
        "Inflation means prices rise over time, so cash kept under the mattress buys less each year. That is one reason people put savings into places that may earn something. Higher returns usually mean higher risk, so spread your money and only invest what you can leave alone.",
        "Mfumuko wa bei unamaanisha bei hupanda kadri muda unavyoenda, hivyo pesa zilizofichwa nyumbani hununua kidogo kila mwaka. Hii ni sababu moja watu huweka akiba mahali panapoweza kuzaa faida. Faida kubwa kwa kawaida inamaanisha hatari kubwa, kwa hivyo gawanya pesa zako na uwekeze tu unachoweza kukiacha."),
    "debt": (["debt", "deni", "owe", "pay off", "clear my loan"],
        "To clear debts, list them all, pay the minimum on each, then put extra money on the one with the highest interest rate first. Avoid borrowing from one lender to repay another.",
        "Kulipa madeni, yaandike yote, lipa kiwango cha chini kwa kila moja, kisha weka pesa za ziada kwenye lenye riba ya juu zaidi kwanza. Epuka kukopa kwa mkopeshaji mmoja ili kulipa mwingine."),
    "insurance": (["insurance", "bima", "nhif", "sha", "cover"],
        "Insurance, like health cover through SHA, protects your savings from big shocks such as a hospital stay. Keeping your cover active is usually cheaper than paying a large bill out of pocket.",
        "Bima, kama ya afya kupitia SHA, hulinda akiba yako dhidi ya mishtuko mikubwa kama kulazwa hospitalini. Kuweka bima yako hai kwa kawaida ni nafuu kuliko kulipa bili kubwa mfukoni."),
}

# Questions that ask for a specific investment recommendation: we educate, we do not advise.
ADVICE_TRIGGERS = ["which stock", "what stock", "should i buy", "should i invest", "best investment",
                   "where should i invest", "guaranteed return", "buy bitcoin", "crypto",
                   "nunue hisa", "wekeza wapi", "uwekeze wapi", "nifanye uwekezaji", "hisa gani"]

NO_ADVICE = {
    "en": "I can teach you how investing works, but I can't recommend specific investments. That needs a licensed adviser, because the right choice depends on your whole situation. Check that anyone advising you is licensed by the Capital Markets Authority. Ask me about money market funds, compound interest or SACCOs and I'll explain the basics.",
    "sw": "Naweza kukufundisha jinsi uwekezaji unavyofanya kazi, lakini siwezi kupendekeza uwekezaji maalum. Hilo linahitaji mshauri mwenye leseni, kwa sababu chaguo sahihi hutegemea hali yako yote. Hakikisha yeyote anayekushauri ana leseni ya Mamlaka ya Masoko ya Mitaji. Niulize kuhusu mifuko ya soko la fedha, riba ya kiwanja au SACCO nami nitaeleza misingi.",
}

FALLBACK = {
    "en": "I'm not sure about that one yet. I can help with: budgeting, compound interest, chama rules, money market funds, loan sharks, emergency funds, M-Pesa scams, SACCOs, your credit score, penalties, chama loans, welfare, saving goals, inflation, debt and insurance.",
    "sw": "Sijui jibu la hilo bado. Naweza kusaidia kuhusu: bajeti, riba ya kiwanja, kanuni za chama, mifuko ya soko la fedha, mikopo ya haraka, akiba ya dharura, ulaghai wa M-Pesa, SACCO, alama yako, faini, mikopo ya chama, ustawi, malengo ya akiba, mfumuko wa bei, madeni na bima.",
}

DISCLAIMER = {
    "en": "Education only, not financial advice.",
    "sw": "Elimu tu, si ushauri wa kifedha.",
}
