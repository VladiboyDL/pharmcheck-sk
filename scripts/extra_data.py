# fmt: off
"""Extended drug and interaction data for PharmCheck SK."""

EXTRA_DRUGS = [
    # (trade_name, active_substance, atc_code, strength, form, sukl_code)

    # --- Antikoagulancia / LMWH ---
    ("Clexane 40 mg", "enoxaparin", "B01AB05", "40 mg/0.4 ml", "injekcia", "SKL-0300"),
    ("Clexane 60 mg", "enoxaparin", "B01AB05", "60 mg/0.6 ml", "injekcia", "SKL-0301"),
    ("Clexane 80 mg", "enoxaparin", "B01AB05", "80 mg/0.8 ml", "injekcia", "SKL-0302"),
    ("Clexane 100 mg", "enoxaparin", "B01AB05", "100 mg/1 ml", "injekcia", "SKL-0303"),
    ("Fraxiparine 0,4 ml", "nadroparin", "B01AB06", "3800 IU/0.4 ml", "injekcia", "SKL-0304"),
    ("Fraxiparine 0,6 ml", "nadroparin", "B01AB06", "5700 IU/0.6 ml", "injekcia", "SKL-0305"),
    ("Fragmin 5000 IU", "dalteparin", "B01AB04", "5000 IU", "injekcia", "SKL-0306"),
    ("Heparin Léčiva 5000 IU", "heparin", "B01AB01", "5000 IU/ml", "injekcia", "SKL-0307"),

    # --- MAO inhibítory / Parkinsonove lieky ---
    ("Jumex 5 mg", "selegiline", "N04BD01", "5 mg", "tableta", "SKL-0310"),
    ("Jumex 10 mg", "selegiline", "N04BD01", "10 mg", "tableta", "SKL-0311"),
    ("Azilect 1 mg", "rasagiline", "N04BD02", "1 mg", "tableta", "SKL-0312"),
    ("Aurorix 150 mg", "moclobemide", "N06AG02", "150 mg", "tableta", "SKL-0313"),
    ("Aurorix 300 mg", "moclobemide", "N06AG02", "300 mg", "tableta", "SKL-0314"),
    ("Nakom", "levodopa/carbidopa", "N04BA02", "250/25 mg", "tableta", "SKL-0315"),
    ("Nakom Mite", "levodopa/carbidopa", "N04BA02", "100/25 mg", "tableta", "SKL-0316"),
    ("Sinemet CR", "levodopa/carbidopa", "N04BA02", "200/50 mg", "tableta", "SKL-0317"),
    ("Madopar 250 mg", "levodopa/benserazide", "N04BA02", "200/50 mg", "kapsula", "SKL-0318"),
    ("Mirapexin 0,18 mg", "pramipexole", "N04BC05", "0.18 mg", "tableta", "SKL-0319"),
    ("Mirapexin 0,7 mg", "pramipexole", "N04BC05", "0.7 mg", "tableta", "SKL-0320"),
    ("Requip 2 mg", "ropinirole", "N04BC04", "2 mg", "tableta", "SKL-0321"),
    ("Comtan 200 mg", "entacapone", "N04BX02", "200 mg", "tableta", "SKL-0322"),
    ("Stalevo 100/25/200", "levodopa/carbidopa/entacapone", "N04BA03", "100/25/200 mg", "tableta", "SKL-0323"),
    ("Amantadin AL 100 mg", "amantadine", "N04BB01", "100 mg", "tableta", "SKL-0324"),
    ("Akineton 2 mg", "biperiden", "N04AA02", "2 mg", "tableta", "SKL-0325"),

    # --- Opioidné analgetiká ---
    ("Sevredol 10 mg", "morphine", "N02AA01", "10 mg", "tableta", "SKL-0330"),
    ("MST Continus 30 mg", "morphine", "N02AA01", "30 mg", "tableta", "SKL-0331"),
    ("OxyContin 10 mg", "oxycodone", "N02AA05", "10 mg", "tableta", "SKL-0332"),
    ("OxyContin 20 mg", "oxycodone", "N02AA05", "20 mg", "tableta", "SKL-0333"),
    ("Durogesic 25 mcg/h", "fentanyl", "N02AB03", "25 mcg/h", "náplasť", "SKL-0334"),
    ("Durogesic 50 mcg/h", "fentanyl", "N02AB03", "50 mcg/h", "náplasť", "SKL-0335"),
    ("Dolsin 50 mg", "pethidine", "N02AB02", "50 mg", "injekcia", "SKL-0336"),
    ("Transtec 35 mcg/h", "buprenorphine", "N02AE01", "35 mcg/h", "náplasť", "SKL-0337"),
    ("Subutex 8 mg", "buprenorphine", "N07BC01", "8 mg", "tableta", "SKL-0338"),
    ("DHC Continus 60 mg", "dihydrocodeine", "N02AA08", "60 mg", "tableta", "SKL-0339"),
    ("Naloxone Mylan 0,4 mg", "naloxone", "V03AB15", "0.4 mg", "injekcia", "SKL-0340"),

    # --- Imunosupresíva ---
    ("Methotrexát Ebewe 10 mg", "methotrexate", "L04AX03", "10 mg", "tableta", "SKL-0350"),
    ("Methotrexát Ebewe 2,5 mg", "methotrexate", "L04AX03", "2.5 mg", "tableta", "SKL-0351"),
    ("Imuran 50 mg", "azathioprine", "L04AX01", "50 mg", "tableta", "SKL-0352"),
    ("Sandimmun Neoral 100 mg", "ciclosporin", "L04AD01", "100 mg", "kapsula", "SKL-0353"),
    ("Sandimmun Neoral 25 mg", "ciclosporin", "L04AD01", "25 mg", "kapsula", "SKL-0354"),
    ("Prograf 1 mg", "tacrolimus", "L04AD02", "1 mg", "kapsula", "SKL-0355"),
    ("Prograf 5 mg", "tacrolimus", "L04AD02", "5 mg", "kapsula", "SKL-0356"),
    ("CellCept 500 mg", "mycophenolate mofetil", "L04AA06", "500 mg", "tableta", "SKL-0357"),
    ("Arava 20 mg", "leflunomide", "L04AA13", "20 mg", "tableta", "SKL-0358"),
    ("Sulfasalazín EN 500 mg", "sulfasalazine", "A07EC01", "500 mg", "tableta", "SKL-0359"),

    # --- Nitráty ---
    ("Nitroglycerín 0,5 mg", "nitroglycerin", "C01DA02", "0.5 mg", "tableta", "SKL-0360"),
    ("Nitromint sprej", "nitroglycerin", "C01DA02", "0.4 mg/dávka", "sprej", "SKL-0361"),
    ("Mono Mack Depot 50 mg", "isosorbide mononitrate", "C01DA14", "50 mg", "tableta", "SKL-0362"),
    ("Isoket Retard 40 mg", "isosorbide dinitrate", "C01DA08", "40 mg", "tableta", "SKL-0363"),

    # --- Antifungálne ---
    ("Fluconazol Mylan 150 mg", "fluconazole", "J02AC01", "150 mg", "kapsula", "SKL-0370"),
    ("Fluconazol Mylan 50 mg", "fluconazole", "J02AC01", "50 mg", "kapsula", "SKL-0371"),
    ("Itraconazol Mylan 100 mg", "itraconazole", "J02AC02", "100 mg", "kapsula", "SKL-0372"),
    ("Ketokonazol", "ketoconazole", "J02AB02", "200 mg", "tableta", "SKL-0373"),
    ("Nystatin Léčiva", "nystatin", "A07AA02", "500 000 IU", "tableta", "SKL-0374"),

    # --- Antivirotiká ---
    ("Herpesin 400 mg", "aciclovir", "J05AB01", "400 mg", "tableta", "SKL-0380"),
    ("Herpesin 200 mg", "aciclovir", "J05AB01", "200 mg", "tableta", "SKL-0381"),
    ("Valtrex 500 mg", "valaciclovir", "J05AB11", "500 mg", "tableta", "SKL-0382"),
    ("Tamiflu 75 mg", "oseltamivir", "J05AH02", "75 mg", "kapsula", "SKL-0383"),

    # --- Antiepileptiká (doplnenie) ---
    ("Epanutin 100 mg", "phenytoin", "N03AB02", "100 mg", "kapsula", "SKL-0390"),
    ("Luminal 100 mg", "phenobarbital", "N03AA02", "100 mg", "tableta", "SKL-0391"),
    ("Trileptal 300 mg", "oxcarbazepine", "N03AF02", "300 mg", "tableta", "SKL-0392"),
    ("Sabril 500 mg", "vigabatrin", "N03AG04", "500 mg", "tableta", "SKL-0393"),
    ("Zonegran 100 mg", "zonisamide", "N03AX15", "100 mg", "kapsula", "SKL-0394"),

    # --- Antidepresíva (doplnenie) ---
    ("Elontril 150 mg", "bupropion", "N06AX12", "150 mg", "tableta", "SKL-0400"),
    ("Remeron 30 mg", "mirtazapine", "N06AX11", "30 mg", "tableta", "SKL-0401"),
    ("Amitriptylín Léčiva 25 mg", "amitriptyline", "N06AA09", "25 mg", "tableta", "SKL-0402"),
    ("Anafranil 25 mg", "clomipramine", "N06AA04", "25 mg", "tableta", "SKL-0403"),
    ("Prothiaden 75 mg", "dosulepin", "N06AA16", "75 mg", "tableta", "SKL-0404"),
    ("Coaxil 12,5 mg", "tianeptine", "N06AX14", "12.5 mg", "tableta", "SKL-0405"),

    # --- Antipsychotiká (doplnenie) ---
    ("Abilify 10 mg", "aripiprazole", "N05AX12", "10 mg", "tableta", "SKL-0410"),
    ("Leponex 100 mg", "clozapine", "N05AH02", "100 mg", "tableta", "SKL-0411"),
    ("Zyprexa 10 mg", "olanzapine", "N05AH03", "10 mg", "tableta", "SKL-0412"),
    ("Chlorprothixen Léčiva 15 mg", "chlorprothixene", "N05AF03", "15 mg", "tableta", "SKL-0413"),
    ("Sulpirid 50 mg", "sulpiride", "N05AL01", "50 mg", "kapsula", "SKL-0414"),
    ("Invega 6 mg", "paliperidone", "N05AX13", "6 mg", "tableta", "SKL-0415"),

    # --- Hypertenzia (doplnenie) ---
    ("Doxazosin Mylan 4 mg", "doxazosin", "C02CA04", "4 mg", "tableta", "SKL-0420"),
    ("Ebrantil 30 mg", "urapidil", "C02CA06", "30 mg", "kapsula", "SKL-0421"),
    ("Minoxidil 5 mg", "minoxidil", "C02DC01", "5 mg", "tableta", "SKL-0422"),
    ("Catapresan 150 mcg", "clonidine", "C02AC01", "150 mcg", "tableta", "SKL-0423"),

    # --- Dna ---
    ("Colchicin Léčiva 0,5 mg", "colchicine", "M04AC01", "0.5 mg", "tableta", "SKL-0430"),

    # --- Draslík / Elektrolyty ---
    ("Kaldyum 600 mg", "potassium chloride", "A12BA01", "600 mg", "kapsula", "SKL-0440"),
    ("Slow-K", "potassium chloride", "A12BA01", "600 mg", "tableta", "SKL-0441"),
    ("Magnosolv", "magnesium citrate", "A12CC04", "365 mg", "granulát", "SKL-0442"),
    ("Magnesium B6", "magnesium/pyridoxine", "A11JB", "470 mg/5 mg", "tableta", "SKL-0443"),

    # --- Xantíny ---
    ("Euphyllin CR 200 mg", "theophylline", "R03DA04", "200 mg", "tableta", "SKL-0450"),
    ("Euphyllin CR 300 mg", "theophylline", "R03DA04", "300 mg", "tableta", "SKL-0451"),

    # --- Antiarytmiká (doplnenie) ---
    ("Rytmonorm 150 mg", "propafenone", "C01BC03", "150 mg", "tableta", "SKL-0460"),
    ("Sedacoron 200 mg", "amiodarone", "C01BD01", "200 mg", "tableta", "SKL-0461"),
    ("Flecainid Mylan 100 mg", "flecainide", "C01BC04", "100 mg", "tableta", "SKL-0462"),

    # --- Urologické ---
    ("Ditropan 5 mg", "oxybutynin", "G04BD04", "5 mg", "tableta", "SKL-0470"),
    ("Vesicare 5 mg", "solifenacin", "G04BD08", "5 mg", "tableta", "SKL-0471"),
    ("Avodart 0,5 mg", "dutasteride", "G04CB02", "0.5 mg", "kapsula", "SKL-0472"),
    ("Finasterid 5 mg", "finasteride", "G04CB01", "5 mg", "tableta", "SKL-0473"),
    ("Cialis 20 mg", "tadalafil", "G04BE08", "20 mg", "tableta", "SKL-0474"),

    # --- Oftalmologické (perorálne/systémové) ---
    ("Timolol 0,5%", "timolol", "S01ED01", "0.5%", "očné kvapky", "SKL-0480"),
    ("Xalatan", "latanoprost", "S01EE01", "0.005%", "očné kvapky", "SKL-0481"),
    ("Diamox 250 mg", "acetazolamide", "S01EC01", "250 mg", "tableta", "SKL-0482"),

    # --- Dermatologické (systémové) ---
    ("Roaccutane 20 mg", "isotretinoin", "D10BA01", "20 mg", "kapsula", "SKL-0490"),
    ("Dapson 100 mg", "dapsone", "J04BA02", "100 mg", "tableta", "SKL-0491"),

    # --- Onkologická podporná liečba ---
    ("Ondansetron Mylan 8 mg", "ondansetron", "A04AA01", "8 mg", "tableta", "SKL-0500"),
    ("Dexametazon 4 mg", "dexamethasone", "H02AB02", "4 mg", "tableta", "SKL-0501"),
    ("Zofran 4 mg", "ondansetron", "A04AA01", "4 mg", "tableta", "SKL-0502"),
    ("Emend 125 mg", "aprepitant", "A04AD12", "125 mg", "kapsula", "SKL-0503"),
    ("Neulasta", "pegfilgrastim", "L03AA13", "6 mg", "injekcia", "SKL-0504"),

    # --- Osteoporóza ---
    ("Fosamax 70 mg", "alendronate", "M05BA04", "70 mg", "tableta", "SKL-0510"),
    ("Bonviva 150 mg", "ibandronate", "M05BA06", "150 mg", "tableta", "SKL-0511"),
    ("Prolia", "denosumab", "M05BX04", "60 mg", "injekcia", "SKL-0512"),

    # --- Migrény ---
    ("Sumatriptan Mylan 50 mg", "sumatriptan", "N02CC01", "50 mg", "tableta", "SKL-0520"),
    ("Relpax 40 mg", "eletriptan", "N02CC06", "40 mg", "tableta", "SKL-0521"),
    ("Zomig 2,5 mg", "zolmitriptan", "N02CC03", "2.5 mg", "tableta", "SKL-0522"),

    # --- Ďalšie bežné ---
    ("Phosphalugel", "aluminium phosphate", "A02AB03", None, "gél", "SKL-0530"),
    ("Maalox", "aluminium/magnesium hydroxide", "A02AD01", None, "suspenzia", "SKL-0531"),
    ("Gaviscon", "alginate/bicarbonate", "A02BX13", None, "suspenzia", "SKL-0532"),
    ("Espumisan 40 mg", "simeticone", "A03AX13", "40 mg", "kapsula", "SKL-0533"),
    ("Kreon 25000", "pancreatin", "A09AA02", "25000 IU", "kapsula", "SKL-0534"),
    ("Trimedat 200 mg", "trimebutine", "A03AA05", "200 mg", "tableta", "SKL-0535"),
    ("Mezym Forte", "pancreatin", "A09AA02", "10000 IU", "tableta", "SKL-0536"),
    ("Ganaton 50 mg", "itopride", "A03FA07", "50 mg", "tableta", "SKL-0537"),
    ("Flebaven 500 mg", "diosmin/hesperidin", "C05CA53", "500 mg", "tableta", "SKL-0538"),
    ("Ginkor Fort", "ginkgo/troxerutin", "C05CX", None, "kapsula", "SKL-0539"),
    ("Venoruton 300 mg", "oxerutin", "C05CA01", "300 mg", "kapsula", "SKL-0540"),
    ("Ascorutin", "ascorbic acid/rutin", "C05CA51", None, "tableta", "SKL-0541"),
    ("Zinkorot 25 mg", "zinc", "A12CB01", "25 mg", "tableta", "SKL-0542"),
    ("Milgamma N", "benfotiamine/pyridoxine", "A11DB", None, "kapsula", "SKL-0543"),
    ("Thioctacid 600 HR", "thioctic acid", "A16AX01", "600 mg", "tableta", "SKL-0544"),
    ("Berlipril 10 mg", "enalapril", "C09AA02", "10 mg", "tableta", "SKL-0545"),
    ("Lokren 20 mg", "betaxolol", "C07AB05", "20 mg", "tableta", "SKL-0546"),
    ("Tenormin 50 mg", "atenolol", "C07AB03", "50 mg", "tableta", "SKL-0547"),
    ("Sectral 200 mg", "acebutolol", "C07AB04", "200 mg", "tableta", "SKL-0548"),
    ("Nimotop 30 mg", "nimodipine", "C08CA06", "30 mg", "tableta", "SKL-0549"),
    ("Lercapress 10 mg", "lercanidipine", "C08CA13", "10 mg", "tableta", "SKL-0550"),
    ("Zanidip 10 mg", "lercanidipine", "C08CA13", "10 mg", "tableta", "SKL-0551"),
    ("Fenofibrat Mylan 267 mg", "fenofibrate", "C10AB05", "267 mg", "kapsula", "SKL-0552"),
    ("Lipanthyl 267 M", "fenofibrate", "C10AB05", "267 mg", "kapsula", "SKL-0553"),
    ("Ezetrol 10 mg", "ezetimibe", "C10AX09", "10 mg", "tableta", "SKL-0554"),
    ("Atorvastatin/Ezetimib Mylan", "atorvastatin/ezetimibe", "C10BA05", "20/10 mg", "tableta", "SKL-0555"),
    ("Telmisartan/HCT Mylan 80/12,5", "telmisartan/hydrochlorothiazide", "C09DA07", "80/12.5 mg", "tableta", "SKL-0556"),
    ("Exforge 5/160 mg", "amlodipine/valsartan", "C09DB01", "5/160 mg", "tableta", "SKL-0557"),
    ("Perindopril/Amlodipín Mylan", "perindopril/amlodipine", "C09BB04", "5/5 mg", "tableta", "SKL-0558"),
    ("Triam-Co", "triamterene/hydrochlorothiazide", "C03EA01", "50/25 mg", "tableta", "SKL-0559"),
    ("Spironolaktón/HCT Mylan", "spironolactone/hydrochlorothiazide", "C03EA", "25/25 mg", "tableta", "SKL-0560"),
    ("Dopegyt 250 mg", "methyldopa", "C02AB01", "250 mg", "tableta", "SKL-0561"),
    ("Nifecard XL 30 mg", "nifedipine", "C08CA05", "30 mg", "tableta", "SKL-0562"),
    ("Nifecard XL 60 mg", "nifedipine", "C08CA05", "60 mg", "tableta", "SKL-0563"),

    # --- Ďalšie antibiotiká ---
    ("Duomox 1000 mg", "amoxicillin", "J01CA04", "1000 mg", "tableta", "SKL-0570"),
    ("Cefixim Mylan 400 mg", "cefixime", "J01DD08", "400 mg", "tableta", "SKL-0571"),
    ("Ofloxin 200 mg", "ofloxacin", "J01MA01", "200 mg", "tableta", "SKL-0572"),
    ("Noroxin 400 mg", "norfloxacin", "J01MA06", "400 mg", "tableta", "SKL-0573"),
    ("Dalacin C 300 mg", "clindamycin", "J01FF01", "300 mg", "kapsula", "SKL-0574"),
    ("Rulid 150 mg", "roxithromycin", "J01FA06", "150 mg", "tableta", "SKL-0575"),
    ("Rifadin 300 mg", "rifampicin", "J04AB02", "300 mg", "kapsula", "SKL-0576"),
    ("Isoniazid Léčiva 300 mg", "isoniazid", "J04AC01", "300 mg", "tableta", "SKL-0577"),
    ("Linezolid Mylan 600 mg", "linezolid", "J01XX08", "600 mg", "tableta", "SKL-0578"),
    ("Vancomycín Mylan 250 mg", "vancomycin", "A07AA09", "250 mg", "kapsula", "SKL-0579"),

    # --- Ďalšie CNS ---
    ("Risperdal 1 mg", "risperidone", "N05AX08", "1 mg", "tableta", "SKL-0580"),
    ("Ebixa 10 mg", "memantine", "N06DX01", "10 mg", "tableta", "SKL-0581"),
    ("Aricept 10 mg", "donepezil", "N06DA02", "10 mg", "tableta", "SKL-0582"),
    ("Exelon 4,5 mg", "rivastigmine", "N06DA03", "4.5 mg", "kapsula", "SKL-0583"),
    ("Buspar 10 mg", "buspirone", "N05BE01", "10 mg", "tableta", "SKL-0584"),
    ("Atarax 25 mg", "hydroxyzine", "N05BB01", "25 mg", "tableta", "SKL-0585"),
]

EXTRA_INTERACTIONS = [
    # (drug_a_substance, drug_a_atc, drug_b_substance, drug_b_atc, severity, mechanism, management, alternatives)

    # === SELEGILÍN interakcie ===
    ("selegiline", "N04BD01", "sertraline", "N06AB06", "Závažná",
     "Kombinácia inhibítora MAO (selegilín) a SSRI (sertralín) môže vyvolať potenciálne fatálny serotonínový syndróm. Príznaky: hypertermia, rigidita, myoklonus, autonómna instabilita, zmeny psychického stavu, kóma.",
     "KONTRAINDIKOVANÁ kombinácia. Medzi vysadením sertralínu a začiatkom selegilínu musí uplynúť minimálne 14 dní. Medzi vysadením selegilínu a začiatkom SSRI minimálne 14 dní.",
     "Ak je MAO-B inhibítor potrebný pre Parkinsonovu chorobu, zvážte neantidepresívne liečebné stratégie alebo použite antidepresívum bez serotonergickej aktivity."),

    ("selegiline", "N04BD01", "escitalopram", "N06AB10", "Závažná",
     "MAO inhibítor + SSRI: riziko serotonínového syndrómu. Escitalopram je silné SSRI. Kombinácia je kontraindikovaná.",
     "KONTRAINDIKOVANÁ. Dodržať 14-dňový interval medzi liekmi.",
     None),

    ("selegiline", "N04BD01", "fluoxetine", "N06AB03", "Závažná",
     "MAO inhibítor + SSRI: riziko serotonínového syndrómu. Fluoxetín má dlhý polčas (aktívny metabolit norfluoxetín ~14 dní), preto je washout obdobie dlhšie.",
     "KONTRAINDIKOVANÁ. Po vysadení fluoxetínu počkajte minimálne 5 týždňov pred začatím selegilínu (kvôli dlhému polčasu norfluoxetínu).",
     None),

    ("selegiline", "N04BD01", "paroxetine", "N06AB05", "Závažná",
     "MAO inhibítor + SSRI: riziko serotonínového syndrómu.",
     "KONTRAINDIKOVANÁ. 14-dňový interval medzi liekmi.",
     None),

    ("selegiline", "N04BD01", "citalopram", "N06AB04", "Závažná",
     "MAO inhibítor + SSRI: riziko serotonínového syndrómu.",
     "KONTRAINDIKOVANÁ. 14-dňový interval medzi liekmi.",
     None),

    ("selegiline", "N04BD01", "venlafaxine", "N06AX16", "Závažná",
     "MAO inhibítor + SNRI: vysoké riziko serotonínového syndrómu. Venlafaxín má silnú serotonergickú aktivitu.",
     "KONTRAINDIKOVANÁ kombinácia. 14-dňový washout interval.",
     None),

    ("selegiline", "N04BD01", "duloxetine", "N06AX21", "Závažná",
     "MAO inhibítor + SNRI: riziko serotonínového syndrómu.",
     "KONTRAINDIKOVANÁ. 14-dňový washout.",
     None),

    ("selegiline", "N04BD01", "tramadol", "N02AX02", "Závažná",
     "Kombinácia MAO inhibítora s tramadolom môže viesť k serotonénovému syndrómu a/alebo záchvatom. Tramadol má serotonergickú aktivitu a inhibuje spätné vychytávanie serotonínu.",
     "KONTRAINDIKOVANÁ kombinácia. Nepoužívajte tramadol u pacientov užívajúcich alebo ktorí nedávno užívali MAO inhibítory.",
     "Paracetamol, nízke dávky morfínu (nie petidín!), gabapentín alebo pregabalín na zvládnutie bolesti."),

    ("selegiline", "N04BD01", "pethidine", "N02AB02", "Závažná",
     "ABSOLÚTNA KONTRAINDIKÁCIA. Kombinácia MAO inhibítora s petidínom môže spôsobiť fatálnu reakciu: hypertermiu, kŕče, kómu, kardiovaskulárny kolaps a smrť.",
     "NIKDY nekombinujte. Toto je jedna z najnebezpečnejších liekových interakcií. Aj pri terapeutických dávkach môže nastať smrť.",
     "Morfín je bezpečnejšia alternatíva u pacientov na MAO inhibítoroch (aj keď stále vyžaduje opatrnosť a nižšie dávky)."),

    ("selegiline", "N04BD01", "morphine", "N02AA01", "Stredná",
     "MAO inhibítory môžu zosilniť účinky opioidov vrátane útlmu dýchania a hypotenzie. Menšie riziko ako pri petidíne, ale opatrnosť je potrebná.",
     "Ak je kombinácia nevyhnutná, začnite s nízkou dávkou morfínu (25-50% bežnej dávky) a pomaly titrujte. Monitorujte útlm dýchania a krvný tlak.",
     None),

    ("selegiline", "N04BD01", "amitriptyline", "N06AA09", "Závažná",
     "MAO inhibítor + tricyklické antidepresívum: riziko serotonínového syndrómu, hypertenznej krízy, kŕčov. Kontraindikovaná kombinácia.",
     "KONTRAINDIKOVANÁ. 14-dňový washout interval medzi liekmi.",
     None),

    ("selegiline", "N04BD01", "clomipramine", "N06AA04", "Závažná",
     "MAO inhibítor + TCA so silnou serotonergickou aktivitou: vysoké riziko serotonínového syndrómu.",
     "KONTRAINDIKOVANÁ. Klomipramín má najsilnejšiu serotonergickú aktivitu zo všetkých TCA.",
     None),

    ("selegiline", "N04BD01", "linezolid", "J01XX08", "Závažná",
     "Linezolid je reverzibilný neselektívny MAO inhibítor. Kombinácia dvoch MAO inhibítorov zvyšuje riziko serotonínového syndrómu a hypertenznej krízy.",
     "KONTRAINDIKOVANÁ. Ak je linezolid nevyhnutný, vysaďte selegilín a dodržte washout.",
     None),

    ("selegiline", "N04BD01", "sumatriptan", "N02CC01", "Závažná",
     "Triptány sú agonisty serotonínu. Kombinácia s MAO inhibítorom zvyšuje riziko serotonínového syndrómu.",
     "KONTRAINDIKOVANÁ. Nepoužívajte triptány s MAO inhibítormi.",
     "Paracetamol, NSAID alebo ergotamín na liečbu migrény."),

    ("selegiline", "N04BD01", "ondansetron", "A04AA01", "Stredná",
     "Ondansetrón je antagonista 5-HT3 receptorov so slabou serotonergickou aktivitou. Teoretické riziko serotonínového syndrómu pri kombinácii s MAO inhibítormi.",
     "Používajte s opatrnosťou. Monitorujte príznaky serotonínového syndrómu. Klinický význam je neistý ale opatrnosť je namieste.",
     "Metoklopramid (s vlastnými rizikami) alebo dexametazón na antiemetickú liečbu."),

    # === ENOXAPARÍN interakcie ===
    ("enoxaparin", "B01AB05", "ibuprofen", "M01AE01", "Závažná",
     "NSAID výrazne zvyšujú riziko krvácania u pacientov na nízkomolekulárnom heparíne (LMWH). Ibuprofén inhibuje funkciu trombocytov a poškodzuje sliznicu GIT, čím kumuluje antikoagulačné riziko enoxaparínu.",
     "Vyhnite sa kombinácii ak je to možné. Ak je NSAID nevyhnutné, použite najnižšiu dávku na najkratšiu dobu s dôsledným monitorovaním príznakov krvácania. Zvážte gastroprotekciu PPI.",
     "Paracetamol je bezpečnejšia analgetická alternatíva u pacientov na LMWH."),

    ("enoxaparin", "B01AB05", "diclofenac", "M01AB05", "Závažná",
     "Diklofenak v kombinácii s enoxaparínom výrazne zvyšuje riziko krvácania. NSAID poškodzuje sliznicu GIT a inhibuje trombocyty.",
     "Vyhnite sa kombinácii. Použite paracetamol na bolesť.",
     "Paracetamol, topický diklofenak gél."),

    ("enoxaparin", "B01AB05", "naproxen", "M01AE02", "Závažná",
     "Naproxén s enoxaparínom: zvýšené riziko krvácania. Dlhý polčas naproxénu túto interakciu zhoršuje.",
     "Vyhnite sa kombinácii.",
     "Paracetamol."),

    ("enoxaparin", "B01AB05", "acetylsalicylic acid", "B01AC06", "Závažná",
     "Kyselina acetylsalicylová (aspirín) v kombinácii s enoxaparínom výrazne zvyšuje riziko závažného krvácania. Aspirín ireverzibilne inhibuje COX-1 v trombocytoch, čo v kombinácii s antikoagulačným účinkom LMWH vytvára vysoké riziko hemoragických komplikácií.",
     "Kombinácia len pri jasnej indikácii (napr. akútny koronárny syndróm). Ak je kombinovaná, používajte nízke dávky aspirínu (75-100 mg) a dôsledne monitorujte príznaky krvácania. Zvážte gastroprotekciu.",
     "Ak je antiagregačná liečba nevyhnutná spolu s LMWH, prehodnoťte trvanie a nevyhnutnosť kombinácie."),

    ("enoxaparin", "B01AB05", "clopidogrel", "B01AC04", "Závažná",
     "Trojitá antitrombotická terapia (enoxaparín + aspirín + klopidogrel) alebo duálna kombinácia LMWH + antiagregancium výrazne zvyšuje riziko závažného a fatálneho krvácania.",
     "Len pri jasnej indikácii (AKS, PCI). Obmedzte trvanie kombinácie na minimum. Dôsledne monitorujte príznaky krvácania.",
     None),

    ("enoxaparin", "B01AB05", "warfarin", "B01AA03", "Závažná",
     "Súbežné podávanie LMWH a warfarínu počas prekrývacej terapie zvyšuje riziko krvácania. Táto kombinácia sa používa krátkodobo pri zahajovaní warfarínovej liečby.",
     "Prekrývacia terapia by mala trvať minimálne 5 dní a kým INR nie je v terapeutickom rozmedzí (2,0-3,0) po 2 po sebe idúce dni. Potom vysaďte enoxaparín.",
     None),

    ("enoxaparin", "B01AB05", "sertraline", "N06AB06", "Stredná",
     "SSRI znižujú serotonín v trombocytoch, čím oslabujú agregáciu trombocytov. V kombinácii s antikoagulanciami sa zvyšuje riziko krvácania.",
     "Monitorujte príznaky krvácania. Zvážte gastroprotekciu. Poučte pacienta o varovných príznakoch.",
     None),

    ("enoxaparin", "B01AB05", "escitalopram", "N06AB10", "Stredná",
     "SSRI oslabujú funkciu trombocytov. Kombinácia s LMWH zvyšuje riziko krvácania.",
     "Monitorujte príznaky krvácania.",
     None),

    # === Kyselina acetylsalicylová + ibuprofén ===
    ("acetylsalicylic acid", "B01AC06", "ibuprofen", "M01AE01", "Závažná",
     "Ibuprofén môže blokovať ireverzibilnú inhibíciu COX-1 aspirínom v trombocytoch, čím znižuje kardioprotektívny účinok nízkych dávok aspirínu. Súčasne sa zvyšuje riziko GI krvácania pri kombinácii dvoch NSAID/antitrombotík.",
     "Ak je aspirín užívaný na kardioprotekciu: podajte aspirín aspoň 30 minút PRED ibuprofenom alebo 8 hodín PO ibuprofene. Najlepšie sa vyhnúť pravidelnej kombinácii. Zvážte PPI na gastroprotekciu.",
     "Paracetamol na bolesť u pacientov na kardioprotektívnom aspiríne. Ak je NSAID nevyhnutné, naproxén menej interferuje s antitrombocytovým účinkom aspirínu."),

    # === Nitráty + PDE5 inhibítory ===
    ("nitroglycerin", "C01DA02", "sildenafil", "G04BE03", "Závažná",
     "ABSOLÚTNA KONTRAINDIKÁCIA. PDE5 inhibítory potencujú hypotenzný účinok nitrátov. Kombinácia môže spôsobiť závažnú, potenciálne fatálnu hypotenziu a kardiovaskulárny kolaps.",
     "NIKDY nekombinujte. Sildenafil nesmie byť podaný do 24 hodín od nitrátu. Nitrát nesmie byť podaný do 24 hodín od sildenafilu (48 hodín od tadalafilu).",
     "Na erektilnú dysfunkciu u pacientov na nitrátoch: zvážte iné prístupy (vákuové zariadenia, intrakavernózne injekcie). Na anginu pectoris u pacientov na PDE5i: použite iné antianginózne lieky (betablokátory, blokátory Ca kanálov)."),

    ("isosorbide mononitrate", "C01DA14", "sildenafil", "G04BE03", "Závažná",
     "KONTRAINDIKOVANÁ kombinácia. Rovnaký mechanizmus ako nitroglycerín + sildenafil – riziko fatálnej hypotenzie.",
     "NIKDY nekombinujte. Platí pre všetky formy nitrátov a všetky PDE5 inhibítory.",
     None),

    ("nitroglycerin", "C01DA02", "tadalafil", "G04BE08", "Závažná",
     "KONTRAINDIKOVANÁ. Tadalafil má dlhší polčas (17,5 h) ako sildenafil, preto je washout obdobie dlhšie (48 hodín).",
     "NIKDY nekombinujte. Nitrát nesmie byť podaný do 48 hodín od tadalafilu.",
     None),

    # === Methotrexát interakcie ===
    ("methotrexate", "L04AX03", "ibuprofen", "M01AE01", "Závažná",
     "NSAID znižujú renálny klírens metotrexátu, čo môže spôsobiť toxicitu metotrexátu (útlm kostnej drene, hepatotoxicita, mukozitída, renálne zlyhanie).",
     "Vyhnite sa NSAID s metotrexátom, najmä pri vyšších dávkach metotrexátu. Ak musíte použiť, monitorujte hladiny metotrexátu a krvný obraz.",
     "Paracetamol na zvládnutie bolesti."),

    ("methotrexate", "L04AX03", "diclofenac", "M01AB05", "Závažná",
     "Diklofenak znižuje renálny klírens metotrexátu. Riziko závažnej toxicity.",
     "Vyhnite sa kombinácii. Ak je NSAID nevyhnutné, monitorujte krvný obraz a hladiny metotrexátu.",
     "Paracetamol."),

    ("methotrexate", "L04AX03", "sulfamethoxazole/trimethoprim", "J01EE01", "Závažná",
     "Trimetoprim inhibuje dihydrofolát reduktázu rovnako ako metotrexát. Kombinácia výrazne zvyšuje riziko pancytopénie a megaloblastovej anémie.",
     "KONTRAINDIKOVANÁ kombinácia. Použite alternatívne antibiotikum.",
     "Amoxicilín, cefalosporíny alebo fluorochinolóny."),

    ("methotrexate", "L04AX03", "omeprazole", "A02BC01", "Stredná",
     "PPI môžu znížiť renálnu elimináciu metotrexátu, čím zvyšujú jeho hladiny a riziko toxicity, najmä pri vyšších dávkach metotrexátu.",
     "Pri nízkodávkovom metotrexáte (≤25 mg/týždeň) je riziko nízke. Pri vysokodávkovej liečbe zvážte prerušenie PPI.",
     None),

    # === Theophylline interakcie ===
    ("theophylline", "R03DA04", "ciprofloxacin", "J01MA02", "Závažná",
     "Ciprofloxacín inhibuje CYP1A2, hlavný enzým metabolizmu teofylínu. Hladiny teofylínu sa môžu zvýšiť o 15-40%, čo vedie k toxicite (nauzea, vracanie, tachykardia, arytmie, kŕče).",
     "Ak je kombinácia nevyhnutná, znížte dávku teofylínu o 30-50% a monitorujte sérové hladiny. Zvážte alternatívne antibiotikum.",
     "Azitromycín, amoxicilín alebo cefalosporíny (nemajú vplyv na metabolizmus teofylínu)."),

    ("theophylline", "R03DA04", "clarithromycin", "J01FA09", "Stredná",
     "Klaritromycín inhibuje CYP3A4, čo môže mierne zvýšiť hladiny teofylínu.",
     "Monitorujte hladiny teofylínu. Úprava dávky podľa sérových hladín.",
     "Azitromycín."),

    ("theophylline", "R03DA04", "carbamazepine", "N03AF01", "Stredná",
     "Karbamazepín indukuje CYP1A2, čím znižuje hladiny teofylínu. Súčasne teofylín môže znížiť hladiny karbamazepínu.",
     "Monitorujte hladiny oboch liekov. Môže byť potrebné zvýšenie dávky teofylínu.",
     None),

    # === Ciclosporin interakcie ===
    ("ciclosporin", "L04AD01", "clarithromycin", "J01FA09", "Závažná",
     "Klaritromycín inhibuje CYP3A4 a P-glykoproteín, výrazne zvyšujúc hladiny ciklosporínu (až 2-3x). Riziko nefrotoxicity.",
     "Vyhnite sa kombinácii. Ak je nevyhnutná, monitorujte hladiny ciklosporínu a funkciu obličiek denne. Znížte dávku ciklosporínu.",
     "Azitromycín (menšia inhibícia CYP3A4)."),

    ("ciclosporin", "L04AD01", "ibuprofen", "M01AE01", "Závažná",
     "NSAID zvyšujú nefrotoxicitu ciklosporínu. Ibuprofén znižuje prietok krvi obličkami, čo v kombinácii s nefrotoxicitou ciklosporínu výrazne zvyšuje riziko akútneho zlyhania obličiek.",
     "Vyhnite sa NSAID u pacientov na ciklosporíne. Ak je analgetikum nevyhnutné, paracetamol je bezpečnejší.",
     "Paracetamol."),

    # === Fenytoín interakcie ===
    ("phenytoin", "N03AB02", "warfarin", "B01AA03", "Závažná",
     "Fenytoín a warfarín majú zložitú obojsmernú interakciu. Fenytoín môže indukovať metabolizmus warfarínu (zníženie účinku) alebo ho vytesniť z väzby na bielkoviny (dočasné zvýšenie účinku). Nepredvídateľná.",
     "Dôsledne monitorujte INR pri zahájení, zmene dávky alebo vysadení fenytoínu. Časté kontroly INR.",
     None),

    ("phenytoin", "N03AB02", "omeprazole", "A02BC01", "Stredná",
     "Omeprazol inhibuje CYP2C19, čím môže zvýšiť hladiny fenytoínu.",
     "Monitorujte hladiny fenytoínu. Zvážte pantoprazol alebo H2 blokátor.",
     "Pantoprazol (menšia inhibícia CYP2C19)."),

    # === Kolchicín interakcie ===
    ("colchicine", "M04AC01", "clarithromycin", "J01FA09", "Závažná",
     "Klaritromycín inhibuje CYP3A4 a P-glykoproteín, výrazne zvyšujúc hladiny kolchicínu. Riziko závažnej až fatálnej toxicity kolchicínu (pancytopénia, multiorgánové zlyhanie).",
     "KONTRAINDIKOVANÁ u pacientov s poruchou funkcie obličiek alebo pečene. U ostatných: znížte dávku kolchicínu a monitorujte krvný obraz.",
     "Azitromycín."),

    ("colchicine", "M04AC01", "itraconazole", "J02AC02", "Závažná",
     "Itrakonazol inhibuje CYP3A4 a P-glykoproteín, zvyšujúc hladiny a toxicitu kolchicínu.",
     "KONTRAINDIKOVANÁ u pacientov s renálnou alebo hepatálnou insuficienciou.",
     None),

    # === Rifampicín interakcie ===
    ("rifampicin", "J04AB02", "warfarin", "B01AA03", "Závažná",
     "Rifampicín je jeden z najsilnejších enzýmových induktorov (CYP2C9, CYP3A4, CYP1A2). Dramaticky zvyšuje metabolizmus warfarínu, znižujúc jeho účinok o 50-70%. INR môže klesnúť na subterapeutickú úroveň do 5-7 dní.",
     "Ak je kombinácia nevyhnutná, výrazne zvýšte dávku warfarínu a monitorujte INR každé 3-5 dní. Po vysadení rifampicínu znížte dávku warfarínu postupne (enzýmová indukcia ustupuje 2-3 týždne).",
     "Zvážte NOAK (rivaroxaban, apixaban), hoci aj tie sú ovplyvnené rifampicínom. Alternatívne antituberkulotiká s menšou enzýmovou indukciou."),

    # === Moclobemid ===
    ("moclobemide", "N06AG02", "tramadol", "N02AX02", "Závažná",
     "Moklobemid je reverzibilný MAO-A inhibítor. Kombinácia s tramadolom zvyšuje riziko serotonínového syndrómu.",
     "Vyhnite sa kombinácii. Ak je kombinácia nevyhnutná, použite najnižšie dávky a dôsledne monitorujte.",
     "Paracetamol, NSAID, gabapentín."),

    ("moclobemide", "N06AG02", "sertraline", "N06AB06", "Závažná",
     "MAO-A inhibítor + SSRI: riziko serotonínového syndrómu. Aj keď je moklobemid reverzibilný a selektívny, kombinácia je kontraindikovaná.",
     "KONTRAINDIKOVANÁ. Moklobemid má krátky polčas (~2 h), preto stačí 1-dňový washout po vysadení moklobemidu pred začiatkom SSRI. Ale po vysadení SSRI pred moklobemidom dodržte 14 dní (5 týždňov po fluoxetíne).",
     None),

    # === Sumatriptan ===
    ("sumatriptan", "N02CC01", "sertraline", "N06AB06", "Stredná",
     "Triptány sú serotonínoví agonisté. Kombinácia s SSRI môže zvýšiť riziko serotonínového syndrómu, hoci klinický výskyt je nízky.",
     "Kombinácia sa bežne používa ale pacient by mal byť poučený o príznakoch serotonínového syndrómu. Monitorujte, najmä pri začatí alebo zvyšovaní dávok.",
     None),

    ("sumatriptan", "N02CC01", "venlafaxine", "N06AX16", "Stredná",
     "Triptán + SNRI: teoretické riziko serotonínového syndrómu. Vyššie riziko ako s SSRI kvôli duálnemu serotonínovému účinku venlafaxínu.",
     "Používajte s opatrnosťou. Poučte pacienta o príznakoch.",
     None),

    # === Itrakonazol ===
    ("itraconazole", "J02AC02", "simvastatin", "C10AA01", "Závažná",
     "Itrakonazol je silný inhibítor CYP3A4, dramaticky zvyšujúci hladiny simvastatínu. Riziko rabdomyolýzy.",
     "KONTRAINDIKOVANÁ kombinácia. Pozastavte simvastatín počas liečby itrakonazolom.",
     "Pravastatín alebo rosuvastatín."),

    ("itraconazole", "J02AC02", "warfarin", "B01AA03", "Závažná",
     "Itrakonazol inhibuje CYP3A4 a môže zvýšiť hladiny warfarínu.",
     "Monitorujte INR pri zahájení a ukončení itrakonazolu. Upravte dávku warfarínu.",
     None),

    # === Clozapín ===
    ("clozapine", "N05AH02", "ciprofloxacin", "J01MA02", "Závažná",
     "Ciprofloxacín inhibuje CYP1A2, hlavný enzým metabolizmu klozapínu. Hladiny klozapínu sa môžu zdvojnásobiť, čo zvyšuje riziko záchvatov, sedácie, agranulocytózy.",
     "Ak je kombinácia nevyhnutná, znížte dávku klozapínu o 33-50%. Monitorujte hladiny klozapínu a krvný obraz.",
     "Azitromycín, amoxicilín (nemajú vplyv na CYP1A2)."),

    # === Amitriptylín ===
    ("amitriptyline", "N06AA09", "tramadol", "N02AX02", "Závažná",
     "TCA + tramadol: zvýšené riziko serotonínového syndrómu a kŕčov. Amitriptylín inhibuje spätné vychytávanie serotonínu a noradrenalínu.",
     "Vyhnite sa kombinácii ak je to možné. Ak musíte, použite najnižšie dávky a monitorujte.",
     "Paracetamol, gabapentín."),

    # === Valproát + karbamazepín ===
    ("valproic acid", "N03AG01", "carbamazepine", "N03AF01", "Stredná",
     "Zložitá obojsmerná interakcia. Karbamazepín indukuje metabolizmus valproátu (znižuje hladiny). Valproát inhibuje epoxid hydrolázu, čím zvyšuje hladiny toxického metabolitu karbamazepínu (karbamazepín-10,11-epoxid).",
     "Monitorujte hladiny oboch liekov. Sledujte príznaky toxicity karbamazepínu (závraty, diplopia, ataxia). Môže byť potrebné zvýšenie dávky valproátu.",
     None),

    # === Rasagilín ===
    ("rasagiline", "N04BD02", "tramadol", "N02AX02", "Závažná",
     "Rasagilín (MAO-B inhibítor) + tramadol: riziko serotonínového syndrómu.",
     "KONTRAINDIKOVANÁ kombinácia.",
     "Paracetamol, gabapentín, pregabalín."),

    ("rasagiline", "N04BD02", "sertraline", "N06AB06", "Závažná",
     "MAO-B inhibítor + SSRI: riziko serotonínového syndrómu. Platia rovnaké opatrenia ako pri selegilíne.",
     "KONTRAINDIKOVANÁ. 14-dňový washout interval.",
     None),

    # === Doplnenie existujúcich ===
    ("etoricoxib", "M01AH05", "warfarin", "B01AA03", "Stredná",
     "Etorikoxib môže zvýšiť antikoagulačný účinok warfarínu. Menšie riziko GI krvácania ako neselektívne NSAID, ale INR monitorovanie je potrebné.",
     "Monitorujte INR pri začiatku a zmene dávky etorikoxibu.",
     None),

    ("etoricoxib", "M01AH05", "lithium", "N05AN01", "Stredná",
     "COX-2 inhibítory môžu zvýšiť hladiny lítia znížením renálnej eliminácie.",
     "Monitorujte hladiny lítia. Zvážte nižšiu dávku alebo paracetamol.",
     "Paracetamol."),

    ("isotretinoin", "D10BA01", "doxycycline", "J01AA02", "Závažná",
     "Oba lieky môžu spôsobiť zvýšenie intrakraniálneho tlaku (pseudotumor cerebri). Kombinácia výrazne zvyšuje toto riziko.",
     "KONTRAINDIKOVANÁ kombinácia. Nepoužívajte tetracyklíny s izotretinoínom.",
     "Ak je antibiotikum pre akné nevyhnutné, použite erytromycín alebo trimetoprim."),
]
# fmt: on
