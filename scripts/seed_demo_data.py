#!/usr/bin/env python3
"""Seed the PharmCheck SK database with demo data.

Includes 200+ commonly dispensed Slovak medications and well-documented
drug-drug interactions covering key clinical scenarios.
All interaction text is in Slovak.
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "backend" / "data" / "pharmcheck.db"

# fmt: off
DRUGS = [
    # (trade_name, active_substance, atc_code, strength, form, sukl_code)

    # --- Kardiovaskulárne ---
    ("Warfarin Orion 5 mg", "warfarin", "B01AA03", "5 mg", "tableta", "SKL-0001"),
    ("Warfarin Orion 3 mg", "warfarin", "B01AA03", "3 mg", "tableta", "SKL-0002"),
    ("Plavix 75 mg", "clopidogrel", "B01AC04", "75 mg", "tableta", "SKL-0003"),
    ("Trombex 75 mg", "clopidogrel", "B01AC04", "75 mg", "tableta", "SKL-0004"),
    ("Xarelto 20 mg", "rivaroxaban", "B01AF01", "20 mg", "tableta", "SKL-0005"),
    ("Xarelto 15 mg", "rivaroxaban", "B01AF01", "15 mg", "tableta", "SKL-0006"),
    ("Eliquis 5 mg", "apixaban", "B01AF02", "5 mg", "tableta", "SKL-0007"),
    ("Eliquis 2,5 mg", "apixaban", "B01AF02", "2.5 mg", "tableta", "SKL-0008"),
    ("Pradaxa 150 mg", "dabigatran", "B01AE07", "150 mg", "kapsula", "SKL-0009"),
    ("Simvacard 20 mg", "simvastatin", "C10AA01", "20 mg", "tableta", "SKL-0010"),
    ("Simvacard 40 mg", "simvastatin", "C10AA01", "40 mg", "tableta", "SKL-0011"),
    ("Zocor 20 mg", "simvastatin", "C10AA01", "20 mg", "tableta", "SKL-0012"),
    ("Sortis 20 mg", "atorvastatin", "C10AA05", "20 mg", "tableta", "SKL-0013"),
    ("Sortis 40 mg", "atorvastatin", "C10AA05", "40 mg", "tableta", "SKL-0014"),
    ("Atoris 20 mg", "atorvastatin", "C10AA05", "20 mg", "tableta", "SKL-0015"),
    ("Atoris 40 mg", "atorvastatin", "C10AA05", "40 mg", "tableta", "SKL-0016"),
    ("Crestor 10 mg", "rosuvastatin", "C10AA07", "10 mg", "tableta", "SKL-0017"),
    ("Crestor 20 mg", "rosuvastatin", "C10AA07", "20 mg", "tableta", "SKL-0018"),
    ("Rosucard 10 mg", "rosuvastatin", "C10AA07", "10 mg", "tableta", "SKL-0019"),
    ("Tritace 5 mg", "ramipril", "C09AA05", "5 mg", "tableta", "SKL-0020"),
    ("Tritace 10 mg", "ramipril", "C09AA05", "10 mg", "tableta", "SKL-0021"),
    ("Hartil 5 mg", "ramipril", "C09AA05", "5 mg", "tableta", "SKL-0022"),
    ("Prenessa 4 mg", "perindopril", "C09AA04", "4 mg", "tableta", "SKL-0023"),
    ("Prenessa 8 mg", "perindopril", "C09AA04", "8 mg", "tableta", "SKL-0024"),
    ("Prestarium Neo 5 mg", "perindopril", "C09AA04", "5 mg", "tableta", "SKL-0025"),
    ("Enap 10 mg", "enalapril", "C09AA02", "10 mg", "tableta", "SKL-0026"),
    ("Enap 20 mg", "enalapril", "C09AA02", "20 mg", "tableta", "SKL-0027"),
    ("Norvasc 5 mg", "amlodipine", "C08CA01", "5 mg", "tableta", "SKL-0028"),
    ("Norvasc 10 mg", "amlodipine", "C08CA01", "10 mg", "tableta", "SKL-0029"),
    ("Agen 5 mg", "amlodipine", "C08CA01", "5 mg", "tableta", "SKL-0030"),
    ("Agen 10 mg", "amlodipine", "C08CA01", "10 mg", "tableta", "SKL-0031"),
    ("Betaloc ZOK 50 mg", "metoprolol", "C07AB02", "50 mg", "tableta", "SKL-0032"),
    ("Betaloc ZOK 100 mg", "metoprolol", "C07AB02", "100 mg", "tableta", "SKL-0033"),
    ("Vasocardin 50 mg", "metoprolol", "C07AB02", "50 mg", "tableta", "SKL-0034"),
    ("Concor 5 mg", "bisoprolol", "C07AB07", "5 mg", "tableta", "SKL-0035"),
    ("Concor 10 mg", "bisoprolol", "C07AB07", "10 mg", "tableta", "SKL-0036"),
    ("Nebilet 5 mg", "nebivolol", "C07AB12", "5 mg", "tableta", "SKL-0037"),
    ("Carvedilol Mylan 25 mg", "carvedilol", "C07AG02", "25 mg", "tableta", "SKL-0038"),
    ("Furon 40 mg", "furosemide", "C03CA01", "40 mg", "tableta", "SKL-0039"),
    ("Furon 250 mg", "furosemide", "C03CA01", "250 mg", "tableta", "SKL-0040"),
    ("Hydrochlorothiazid Léčiva 25 mg", "hydrochlorothiazide", "C03AA03", "25 mg", "tableta", "SKL-0041"),
    ("Indapamid Mylan 1,5 mg", "indapamide", "C03BA11", "1.5 mg", "tableta", "SKL-0042"),
    ("Verospiron 25 mg", "spironolactone", "C03DA01", "25 mg", "tableta", "SKL-0043"),
    ("Verospiron 100 mg", "spironolactone", "C03DA01", "100 mg", "tableta", "SKL-0044"),
    ("Inspra 25 mg", "eplerenone", "C03DA04", "25 mg", "tableta", "SKL-0045"),
    ("Digoxin 0,25 mg", "digoxin", "C01AA05", "0.25 mg", "tableta", "SKL-0046"),
    ("Cordarone 200 mg", "amiodarone", "C01BD01", "200 mg", "tableta", "SKL-0047"),
    ("Isoptin 80 mg", "verapamil", "C08DA01", "80 mg", "tableta", "SKL-0048"),
    ("Isoptin SR 240 mg", "verapamil", "C08DA01", "240 mg", "tableta", "SKL-0049"),
    ("Diltiacard 90 mg", "diltiazem", "C08DB01", "90 mg", "tableta", "SKL-0050"),
    ("Lorista 50 mg", "losartan", "C09CA01", "50 mg", "tableta", "SKL-0051"),
    ("Lorista 100 mg", "losartan", "C09CA01", "100 mg", "tableta", "SKL-0052"),
    ("Micardis 80 mg", "telmisartan", "C09CA07", "80 mg", "tableta", "SKL-0053"),
    ("Atacand 16 mg", "candesartan", "C09CA06", "16 mg", "tableta", "SKL-0054"),
    ("Valsartan Mylan 160 mg", "valsartan", "C09CA03", "160 mg", "tableta", "SKL-0055"),
    ("Edarbi 40 mg", "azilsartan", "C09CA09", "40 mg", "tableta", "SKL-0056"),
    ("Rilmenidin Teva 1 mg", "rilmenidine", "C02AC06", "1 mg", "tableta", "SKL-0057"),
    ("Dopegyt 250 mg", "methyldopa", "C02AB01", "250 mg", "tableta", "SKL-0058"),

    # --- Bolesť / Zápal ---
    ("Paralen 500", "paracetamol", "N02BE01", "500 mg", "tableta", "SKL-0060"),
    ("Paralen Extra", "paracetamol", "N02BE01", "500 mg", "tableta", "SKL-0061"),
    ("Paralen Grip", "paracetamol", "N02BE01", "500 mg", "tableta", "SKL-0062"),
    ("Panadol 500 mg", "paracetamol", "N02BE01", "500 mg", "tableta", "SKL-0063"),
    ("Nurofen 400", "ibuprofen", "M01AE01", "400 mg", "tableta", "SKL-0064"),
    ("Nurofen Forte 400 mg", "ibuprofen", "M01AE01", "400 mg", "tableta", "SKL-0065"),
    ("Ibalgin 400", "ibuprofen", "M01AE01", "400 mg", "tableta", "SKL-0066"),
    ("Ibalgin 200", "ibuprofen", "M01AE01", "200 mg", "tableta", "SKL-0067"),
    ("Brufen 600 mg", "ibuprofen", "M01AE01", "600 mg", "tableta", "SKL-0068"),
    ("Voltaren 50 mg", "diclofenac", "M01AB05", "50 mg", "tableta", "SKL-0069"),
    ("Voltaren Rapid 50 mg", "diclofenac", "M01AB05", "50 mg", "tableta", "SKL-0070"),
    ("Olfen 50 mg", "diclofenac", "M01AB05", "50 mg", "tableta", "SKL-0071"),
    ("Almiral 50 mg", "diclofenac", "M01AB05", "50 mg", "tableta", "SKL-0072"),
    ("Nimesil 100 mg", "nimesulide", "M01AX17", "100 mg", "granulát", "SKL-0073"),
    ("Aulin 100 mg", "nimesulide", "M01AX17", "100 mg", "tableta", "SKL-0074"),
    ("Tramal 50 mg", "tramadol", "N02AX02", "50 mg", "kapsula", "SKL-0075"),
    ("Tramal Retard 100 mg", "tramadol", "N02AX02", "100 mg", "tableta", "SKL-0076"),
    ("Tramabene 50 mg", "tramadol", "N02AX02", "50 mg", "kapsula", "SKL-0077"),
    ("Novalgin 500 mg", "metamizole", "N02BB02", "500 mg", "tableta", "SKL-0078"),
    ("Nalgesin Forte", "naproxen", "M01AE02", "550 mg", "tableta", "SKL-0079"),
    ("Nalgesin S", "naproxen", "M01AE02", "275 mg", "tableta", "SKL-0080"),
    ("Celebrex 200 mg", "celecoxib", "M01AH01", "200 mg", "kapsula", "SKL-0081"),
    ("Arcoxia 90 mg", "etoricoxib", "M01AH05", "90 mg", "tableta", "SKL-0082"),
    ("Arcoxia 60 mg", "etoricoxib", "M01AH05", "60 mg", "tableta", "SKL-0083"),
    ("Aspirin 100 mg", "acetylsalicylic acid", "B01AC06", "100 mg", "tableta", "SKL-0084"),
    ("Godasal 100 mg", "acetylsalicylic acid", "B01AC06", "100 mg", "tableta", "SKL-0085"),
    ("Acylpyrin 500 mg", "acetylsalicylic acid", "N02BA01", "500 mg", "tableta", "SKL-0086"),
    ("Palexia Retard 50 mg", "tapentadol", "N02AX06", "50 mg", "tableta", "SKL-0087"),
    ("Codein Slovakofarma 30 mg", "codeine", "N02AA59", "30 mg", "tableta", "SKL-0088"),

    # --- Antibiotiká ---
    ("Amoksiklav 1000 mg", "amoxicillin/clavulanate", "J01CR02", "1000 mg", "tableta", "SKL-0090"),
    ("Amoksiklav 625 mg", "amoxicillin/clavulanate", "J01CR02", "625 mg", "tableta", "SKL-0091"),
    ("Augmentin 1 g", "amoxicillin/clavulanate", "J01CR02", "1000 mg", "tableta", "SKL-0092"),
    ("Ospamox 1000 mg", "amoxicillin", "J01CA04", "1000 mg", "tableta", "SKL-0093"),
    ("Ospamox 500 mg", "amoxicillin", "J01CA04", "500 mg", "tableta", "SKL-0094"),
    ("Azitromycín Sandoz 500 mg", "azithromycin", "J01FA10", "500 mg", "tableta", "SKL-0095"),
    ("Sumamed 500 mg", "azithromycin", "J01FA10", "500 mg", "tableta", "SKL-0096"),
    ("Ciprinol 500 mg", "ciprofloxacin", "J01MA02", "500 mg", "tableta", "SKL-0097"),
    ("Ciprobay 500 mg", "ciprofloxacin", "J01MA02", "500 mg", "tableta", "SKL-0098"),
    ("Entizol 250 mg", "metronidazole", "J01XD01", "250 mg", "tableta", "SKL-0099"),
    ("Flagyl 500 mg", "metronidazole", "J01XD01", "500 mg", "tableta", "SKL-0100"),
    ("Doxybene 100 mg", "doxycycline", "J01AA02", "100 mg", "kapsula", "SKL-0101"),
    ("Doxyhexal 100 mg", "doxycycline", "J01AA02", "100 mg", "tableta", "SKL-0102"),
    ("Klaritromycín Krka 500 mg", "clarithromycin", "J01FA09", "500 mg", "tableta", "SKL-0103"),
    ("Fromilid 500 mg", "clarithromycin", "J01FA09", "500 mg", "tableta", "SKL-0104"),
    ("Fromilid Uno 500 mg", "clarithromycin", "J01FA09", "500 mg", "tableta", "SKL-0105"),
    ("Biseptol 480 mg", "sulfamethoxazole/trimethoprim", "J01EE01", "480 mg", "tableta", "SKL-0106"),
    ("Sumetrolim 480 mg", "sulfamethoxazole/trimethoprim", "J01EE01", "480 mg", "tableta", "SKL-0107"),
    ("Zinnat 500 mg", "cefuroxime", "J01DC02", "500 mg", "tableta", "SKL-0108"),
    ("Cefzil 500 mg", "cefprozil", "J01DC10", "500 mg", "tableta", "SKL-0109"),
    ("Tavanic 500 mg", "levofloxacin", "J01MA12", "500 mg", "tableta", "SKL-0110"),
    ("Nitrofurantoin Egis 100 mg", "nitrofurantoin", "J01XE01", "100 mg", "kapsula", "SKL-0111"),
    ("Furazidín HBF 50 mg", "furazidin", "J01XE03", "50 mg", "tableta", "SKL-0112"),
    ("Klacid 500 mg", "clarithromycin", "J01FA09", "500 mg", "tableta", "SKL-0113"),
    ("Amoxicilín Sandoz 1000 mg", "amoxicillin", "J01CA04", "1000 mg", "tableta", "SKL-0114"),

    # --- CNS / Psychiatria ---
    ("Zoloft 50 mg", "sertraline", "N06AB06", "50 mg", "tableta", "SKL-0120"),
    ("Zoloft 100 mg", "sertraline", "N06AB06", "100 mg", "tableta", "SKL-0121"),
    ("Asentra 50 mg", "sertraline", "N06AB06", "50 mg", "tableta", "SKL-0122"),
    ("Cipralex 10 mg", "escitalopram", "N06AB10", "10 mg", "tableta", "SKL-0123"),
    ("Cipralex 20 mg", "escitalopram", "N06AB10", "20 mg", "tableta", "SKL-0124"),
    ("Elicea 10 mg", "escitalopram", "N06AB10", "10 mg", "tableta", "SKL-0125"),
    ("Prozac 20 mg", "fluoxetine", "N06AB03", "20 mg", "kapsula", "SKL-0126"),
    ("Floxet 20 mg", "fluoxetine", "N06AB03", "20 mg", "kapsula", "SKL-0127"),
    ("Paxil 20 mg", "paroxetine", "N06AB05", "20 mg", "tableta", "SKL-0128"),
    ("Seroxat 20 mg", "paroxetine", "N06AB05", "20 mg", "tableta", "SKL-0129"),
    ("Velaxin 75 mg", "venlafaxine", "N06AX16", "75 mg", "kapsula", "SKL-0130"),
    ("Velaxin 150 mg", "venlafaxine", "N06AX16", "150 mg", "kapsula", "SKL-0131"),
    ("Cymbalta 60 mg", "duloxetine", "N06AX21", "60 mg", "kapsula", "SKL-0132"),
    ("Wellbutrin SR 150 mg", "bupropion", "N06AX12", "150 mg", "tableta", "SKL-0133"),
    ("Trittico 150 mg", "trazodone", "N06AX05", "150 mg", "tableta", "SKL-0134"),
    ("Mirtazapín Mylan 30 mg", "mirtazapine", "N06AX11", "30 mg", "tableta", "SKL-0135"),
    ("Diazepam Slovakofarma 5 mg", "diazepam", "N05BA01", "5 mg", "tableta", "SKL-0136"),
    ("Diazepam Slovakofarma 10 mg", "diazepam", "N05BA01", "10 mg", "tableta", "SKL-0137"),
    ("Lexaurin 1,5 mg", "bromazepam", "N05BA08", "1.5 mg", "tableta", "SKL-0138"),
    ("Lexaurin 3 mg", "bromazepam", "N05BA08", "3 mg", "tableta", "SKL-0139"),
    ("Xanax 0,5 mg", "alprazolam", "N05BA12", "0.5 mg", "tableta", "SKL-0140"),
    ("Xanax 1 mg", "alprazolam", "N05BA12", "1 mg", "tableta", "SKL-0141"),
    ("Stilnox 10 mg", "zolpidem", "N05CF02", "10 mg", "tableta", "SKL-0142"),
    ("Tegretol 200 mg", "carbamazepine", "N03AF01", "200 mg", "tableta", "SKL-0143"),
    ("Tegretol CR 400 mg", "carbamazepine", "N03AF01", "400 mg", "tableta", "SKL-0144"),
    ("Lithium Carbonicum", "lithium", "N05AN01", "300 mg", "tableta", "SKL-0145"),
    ("Rivotril 0,5 mg", "clonazepam", "N03AE01", "0.5 mg", "tableta", "SKL-0146"),
    ("Rivotril 2 mg", "clonazepam", "N03AE01", "2 mg", "tableta", "SKL-0147"),
    ("Quetiapín Mylan 25 mg", "quetiapine", "N05AH04", "25 mg", "tableta", "SKL-0148"),
    ("Quetiapín Mylan 100 mg", "quetiapine", "N05AH04", "100 mg", "tableta", "SKL-0149"),
    ("Seroquel 200 mg", "quetiapine", "N05AH04", "200 mg", "tableta", "SKL-0150"),
    ("Olanzapín Mylan 10 mg", "olanzapine", "N05AH03", "10 mg", "tableta", "SKL-0151"),
    ("Risperdal 2 mg", "risperidone", "N05AX08", "2 mg", "tableta", "SKL-0152"),
    ("Lamictal 100 mg", "lamotrigine", "N03AX09", "100 mg", "tableta", "SKL-0153"),
    ("Lamictal 200 mg", "lamotrigine", "N03AX09", "200 mg", "tableta", "SKL-0154"),
    ("Neurontin 300 mg", "gabapentin", "N03AX12", "300 mg", "kapsula", "SKL-0155"),
    ("Neurontin 600 mg", "gabapentin", "N03AX12", "600 mg", "tableta", "SKL-0156"),
    ("Lyrica 75 mg", "pregabalin", "N03AX16", "75 mg", "kapsula", "SKL-0157"),
    ("Lyrica 150 mg", "pregabalin", "N03AX16", "150 mg", "kapsula", "SKL-0158"),
    ("Convulex 500 mg", "valproic acid", "N03AG01", "500 mg", "kapsula", "SKL-0159"),
    ("Depakine Chrono 500 mg", "valproic acid", "N03AG01", "500 mg", "tableta", "SKL-0160"),
    ("Topamax 50 mg", "topiramate", "N03AX11", "50 mg", "tableta", "SKL-0161"),
    ("Keppra 500 mg", "levetiracetam", "N03AX14", "500 mg", "tableta", "SKL-0162"),
    ("Haloperidol Richter 1,5 mg", "haloperidol", "N05AD01", "1.5 mg", "tableta", "SKL-0163"),
    ("Tiapridal 100 mg", "tiapride", "N05AL03", "100 mg", "tableta", "SKL-0164"),

    # --- Diabetes ---
    ("Siofor 850 mg", "metformin", "A10BA02", "850 mg", "tableta", "SKL-0170"),
    ("Siofor 1000 mg", "metformin", "A10BA02", "1000 mg", "tableta", "SKL-0171"),
    ("Glucophage 1000 mg", "metformin", "A10BA02", "1000 mg", "tableta", "SKL-0172"),
    ("Glucophage XR 750 mg", "metformin", "A10BA02", "750 mg", "tableta", "SKL-0173"),
    ("Amaryl 2 mg", "glimepiride", "A10BB12", "2 mg", "tableta", "SKL-0174"),
    ("Amaryl 4 mg", "glimepiride", "A10BB12", "4 mg", "tableta", "SKL-0175"),
    ("Gliclada 30 mg", "gliclazide", "A10BB09", "30 mg", "tableta", "SKL-0176"),
    ("Diaprel MR 60 mg", "gliclazide", "A10BB09", "60 mg", "tableta", "SKL-0177"),
    ("Januvia 100 mg", "sitagliptin", "A10BH01", "100 mg", "tableta", "SKL-0178"),
    ("Galvus 50 mg", "vildagliptin", "A10BH02", "50 mg", "tableta", "SKL-0179"),
    ("Jardiance 10 mg", "empagliflozin", "A10BK03", "10 mg", "tableta", "SKL-0180"),
    ("Jardiance 25 mg", "empagliflozin", "A10BK03", "25 mg", "tableta", "SKL-0181"),
    ("Forxiga 10 mg", "dapagliflozin", "A10BK01", "10 mg", "tableta", "SKL-0182"),
    ("Invokana 300 mg", "canagliflozin", "A10BK02", "300 mg", "tableta", "SKL-0183"),
    ("Victoza", "liraglutide", "A10BJ02", "6 mg/ml", "injekcia", "SKL-0184"),
    ("Ozempic 1 mg", "semaglutide", "A10BJ06", "1 mg", "injekcia", "SKL-0185"),
    ("Humulin R", "insulin (regular)", "A10AB01", "100 IU/ml", "injekcia", "SKL-0186"),
    ("Lantus", "insulin glargine", "A10AE04", "100 IU/ml", "injekcia", "SKL-0187"),
    ("Novorapid", "insulin aspart", "A10AB05", "100 IU/ml", "injekcia", "SKL-0188"),
    ("Tresiba", "insulin degludec", "A10AE06", "100 IU/ml", "injekcia", "SKL-0189"),
    ("Glucobay 100 mg", "acarbose", "A10BF01", "100 mg", "tableta", "SKL-0190"),
    ("Pioglitazon Mylan 30 mg", "pioglitazone", "A10BG03", "30 mg", "tableta", "SKL-0191"),

    # --- Gastrointestinálne ---
    ("Helicid 20 mg", "omeprazole", "A02BC01", "20 mg", "kapsula", "SKL-0200"),
    ("Helicid 40 mg", "omeprazole", "A02BC01", "40 mg", "kapsula", "SKL-0201"),
    ("Omeprazol Mylan 20 mg", "omeprazole", "A02BC01", "20 mg", "kapsula", "SKL-0202"),
    ("Controloc 40 mg", "pantoprazole", "A02BC02", "40 mg", "tableta", "SKL-0203"),
    ("Nolpaza 20 mg", "pantoprazole", "A02BC02", "20 mg", "tableta", "SKL-0204"),
    ("Nolpaza 40 mg", "pantoprazole", "A02BC02", "40 mg", "tableta", "SKL-0205"),
    ("Emanera 20 mg", "esomeprazole", "A02BC05", "20 mg", "kapsula", "SKL-0206"),
    ("Nexium 40 mg", "esomeprazole", "A02BC05", "40 mg", "tableta", "SKL-0207"),
    ("Kvamatel 20 mg", "famotidine", "A02BA03", "20 mg", "tableta", "SKL-0208"),
    ("Cerucal 10 mg", "metoclopramide", "A03FA01", "10 mg", "tableta", "SKL-0209"),
    ("Degan 10 mg", "metoclopramide", "A03FA01", "10 mg", "tableta", "SKL-0210"),
    ("Motilium 10 mg", "domperidone", "A03FA03", "10 mg", "tableta", "SKL-0211"),
    ("Smecta", "diosmectite", "A07BC05", "3 g", "suspenzia", "SKL-0212"),
    ("Imodium 2 mg", "loperamide", "A07DA03", "2 mg", "kapsula", "SKL-0213"),
    ("Ursofalk 250 mg", "ursodeoxycholic acid", "A05AA02", "250 mg", "kapsula", "SKL-0214"),
    ("Duspatalin Retard 200 mg", "mebeverine", "A03AA04", "200 mg", "kapsula", "SKL-0215"),
    ("Buscopan 10 mg", "hyoscine butylbromide", "A03BB01", "10 mg", "tableta", "SKL-0216"),

    # --- Štítna žľaza / Endokrinné ---
    ("Euthyrox 25", "levothyroxine", "H03AA01", "25 mcg", "tableta", "SKL-0220"),
    ("Euthyrox 50", "levothyroxine", "H03AA01", "50 mcg", "tableta", "SKL-0221"),
    ("Euthyrox 75", "levothyroxine", "H03AA01", "75 mcg", "tableta", "SKL-0222"),
    ("Euthyrox 100", "levothyroxine", "H03AA01", "100 mcg", "tableta", "SKL-0223"),
    ("Euthyrox 125", "levothyroxine", "H03AA01", "125 mcg", "tableta", "SKL-0224"),
    ("Letrox 100", "levothyroxine", "H03AA01", "100 mcg", "tableta", "SKL-0225"),
    ("Thyrozol 10 mg", "thiamazole", "H03BB02", "10 mg", "tableta", "SKL-0226"),

    # --- Iné bežné ---
    ("Milurit 100 mg", "allopurinol", "M04AA01", "100 mg", "tableta", "SKL-0230"),
    ("Milurit 300 mg", "allopurinol", "M04AA01", "300 mg", "tableta", "SKL-0231"),
    ("Adenuric 80 mg", "febuxostat", "M04AA03", "80 mg", "tableta", "SKL-0232"),
    ("Prednison 5 mg", "prednisone", "H02AB07", "5 mg", "tableta", "SKL-0233"),
    ("Prednison 20 mg", "prednisone", "H02AB07", "20 mg", "tableta", "SKL-0234"),
    ("Medrol 4 mg", "methylprednisolone", "H02AB04", "4 mg", "tableta", "SKL-0235"),
    ("Medrol 16 mg", "methylprednisolone", "H02AB04", "16 mg", "tableta", "SKL-0236"),
    ("Singulair 10 mg", "montelukast", "R03DC03", "10 mg", "tableta", "SKL-0237"),
    ("Singulair 5 mg", "montelukast", "R03DC03", "5 mg", "žuvacia tableta", "SKL-0238"),
    ("Ventolin", "salbutamol", "R03AC02", "100 mcg", "inhalácia", "SKL-0239"),
    ("Atrovent N", "ipratropium", "R03BB01", "20 mcg", "inhalácia", "SKL-0240"),
    ("Spiriva 18 mcg", "tiotropium", "R03BB04", "18 mcg", "inhalácia", "SKL-0241"),
    ("Seretide Diskus", "salmeterol/fluticasone", "R03AK06", "50/250 mcg", "inhalácia", "SKL-0242"),
    ("Symbicort Turbuhaler", "budesonide/formoterol", "R03AK07", "160/4.5 mcg", "inhalácia", "SKL-0243"),
    ("Xyzal 5 mg", "levocetirizine", "R06AE09", "5 mg", "tableta", "SKL-0244"),
    ("Aerius 5 mg", "desloratadine", "R06AX27", "5 mg", "tableta", "SKL-0245"),
    ("Claritin 10 mg", "loratadine", "R06AX13", "10 mg", "tableta", "SKL-0246"),
    ("ACC Long 600 mg", "acetylcysteine", "R05CB01", "600 mg", "tableta", "SKL-0247"),
    ("Ambrobene 30 mg", "ambroxol", "R05CB06", "30 mg", "tableta", "SKL-0248"),
    ("Sinupret", "herbal combination", "R05X", None, "tableta", "SKL-0249"),
    ("Kanavit", "phytomenadione", "B02BA01", "10 mg", "tableta", "SKL-0250"),
    ("Vessel Due F", "sulodexide", "B01AB11", "250 LSU", "kapsula", "SKL-0251"),
    ("Detralex 500 mg", "diosmin", "C05CA03", "500 mg", "tableta", "SKL-0252"),
    ("Calcium Sandoz Forte", "calcium carbonate", "A12AA04", "500 mg", "tableta", "SKL-0253"),
    ("Caltrate 600 mg", "calcium carbonate", "A12AA04", "600 mg", "tableta", "SKL-0254"),
    ("Vigantol", "cholecalciferol", "A11CC05", "500 IU", "kvapky", "SKL-0255"),
    ("Vigantol 1000 IU", "cholecalciferol", "A11CC05", "1000 IU", "tableta", "SKL-0256"),
    ("Dulcolax 5 mg", "bisacodyl", "A06AB02", "5 mg", "tableta", "SKL-0257"),
    ("Duphalac", "lactulose", "A06AD11", "667 mg/ml", "sirup", "SKL-0258"),
    ("Hylak forte", "lactic acid bacteria", "A09AA01", None, "kvapky", "SKL-0259"),
    ("Linex", "lactobacillus", "A07FA01", None, "kapsula", "SKL-0260"),
    ("Linex Forte", "lactobacillus", "A07FA01", None, "kapsula", "SKL-0261"),
    ("Condrosulf 400 mg", "chondroitin sulfate", "M01AX25", "400 mg", "kapsula", "SKL-0262"),
    ("Dona 1500 mg", "glucosamine", "M01AX05", "1500 mg", "vrecko", "SKL-0263"),
    ("Betaserc 24 mg", "betahistine", "N07CA01", "24 mg", "tableta", "SKL-0264"),
    ("Mydocalm 150 mg", "tolperisone", "M03BX04", "150 mg", "tableta", "SKL-0265"),
    ("Baclofen 10 mg", "baclofen", "M03BX01", "10 mg", "tableta", "SKL-0266"),
    ("Sirdalud 4 mg", "tizanidine", "M03BX02", "4 mg", "tableta", "SKL-0267"),
    ("Trental 400 mg", "pentoxifylline", "C04AD03", "400 mg", "tableta", "SKL-0268"),
    ("Cavinton 5 mg", "vinpocetine", "N06BX18", "5 mg", "tableta", "SKL-0269"),
    ("Nootropil 1200 mg", "piracetam", "N06BX03", "1200 mg", "tableta", "SKL-0270"),
    ("Tanakan 40 mg", "ginkgo biloba", "N06DX02", "40 mg", "tableta", "SKL-0271"),
    ("Fenistil", "dimetindene", "R06AB03", "1 mg/ml", "kvapky", "SKL-0272"),
    ("Zodac 10 mg", "cetirizine", "R06AE07", "10 mg", "tableta", "SKL-0273"),
    ("Olynth 0,1%", "xylometazoline", "R01AA07", "0.1%", "sprej", "SKL-0274"),
    ("Nasivin 0,05%", "oxymetazoline", "R01AA05", "0.05%", "kvapky", "SKL-0275"),
    ("Wobenzym", "enzymes", "M09AB52", None, "tableta", "SKL-0276"),
    ("Magnesium Lacticum", "magnesium", "A12CC05", "500 mg", "tableta", "SKL-0277"),
    ("Ascorutin", "ascorbic acid/rutin", "C05CA51", None, "tableta", "SKL-0278"),
    ("Piracetam AL 1200 mg", "piracetam", "N06BX03", "1200 mg", "tableta", "SKL-0279"),
    ("Ferronat", "iron fumarate", "B03AA02", "350 mg", "tableta", "SKL-0280"),
    ("Sorbifer Durules", "iron sulfate", "B03AA07", "320 mg", "tableta", "SKL-0281"),
    ("Folacin 5 mg", "folic acid", "B03BB01", "5 mg", "tableta", "SKL-0282"),
    ("Torvacard 20 mg", "atorvastatin", "C10AA05", "20 mg", "tableta", "SKL-0283"),
    ("Torvacard 40 mg", "atorvastatin", "C10AA05", "40 mg", "tableta", "SKL-0284"),
    ("Ezetrol 10 mg", "ezetimibe", "C10AX09", "10 mg", "tableta", "SKL-0285"),
    ("Apo-Ome 20 mg", "omeprazole", "A02BC01", "20 mg", "kapsula", "SKL-0286"),
    ("Metformin Teva 1000 mg", "metformin", "A10BA02", "1000 mg", "tableta", "SKL-0287"),
    ("Tamsulosin Mylan 0,4 mg", "tamsulosin", "G04CA02", "0.4 mg", "kapsula", "SKL-0288"),
    ("Prostamol Uno", "serenoa repens", "G04CX02", "320 mg", "kapsula", "SKL-0289"),
    ("Sildenafil Mylan 50 mg", "sildenafil", "G04BE03", "50 mg", "tableta", "SKL-0290"),
    ("Fokusin 0,4 mg", "tamsulosin", "G04CA02", "0.4 mg", "kapsula", "SKL-0291"),
    ("Monkasta 10 mg", "montelukast", "R03DC03", "10 mg", "tableta", "SKL-0292"),
    ("Levetiracetam Mylan 500 mg", "levetiracetam", "N03AX14", "500 mg", "tableta", "SKL-0293"),
    ("Citalopram Mylan 20 mg", "citalopram", "N06AB04", "20 mg", "tableta", "SKL-0294"),
    ("Fluconazol Mylan 150 mg", "fluconazole", "J02AC01", "150 mg", "kapsula", "SKL-0295"),
    ("Diklofenak Mylan 50 mg", "diclofenac", "M01AB05", "50 mg", "tableta", "SKL-0296"),
]

INTERACTIONS = [
    # (drug_a_substance, drug_a_atc, drug_b_substance, drug_b_atc, severity, mechanism, management, alternatives)
    # All text in Slovak

    # --- ZÁVAŽNÉ (Major) ---
    ("warfarin", "B01AA03", "ibuprofen", "M01AE01", "Závažná",
     "NSAID zvyšujú riziko gastrointestinálneho krvácania a môžu zosilniť antikoagulačný účinok warfarínu inhibíciou funkcie trombocytov a vytesnením warfarínu z väzby na plazmatické bielkoviny.",
     "Vyhnite sa kombinácii ak je to možné. Ak je to nevyhnutné, použite najnižšiu dávku NSAID na najkratšiu dobu a pravidelne monitorujte INR. Zvážte pridanie PPI na ochranu GIT.",
     "Paracetamol v nízkych dávkach (<2g/deň) môže byť bezpečnejšou analgetickou alternatívou."),

    ("warfarin", "B01AA03", "diclofenac", "M01AB05", "Závažná",
     "Diklofenak zvyšuje riziko krvácania v kombinácii s warfarínom prostredníctvom inhibície agregácie trombocytov, poškodenia sliznice GIT a potenciálneho vytesnenia z väzby na bielkoviny.",
     "Vyhnite sa kombinácii. Ak je NSAID nevyhnutné, použite krátky cyklus s monitorovaním INR každých 3-5 dní. Pridajte PPI na gastroprotekciu.",
     "Paracetamol alebo topický diklofenak gél na lokálnu bolesť."),

    ("warfarin", "B01AA03", "naproxen", "M01AE02", "Závažná",
     "Naproxén zvyšuje riziko krvácania s warfarínom prostredníctvom antitrombocytových účinkov a poškodenia sliznice GIT. Dlhý polčas naproxénu robí túto interakciu obzvlášť znepokojujúcou.",
     "Vyhnite sa kombinácii. Monitorujte INR ak musíte spolupredpisovať. Pridajte gastroprotekciu.",
     "Paracetamol v štandardných dávkach."),

    ("warfarin", "B01AA03", "acetylsalicylic acid", "B01AC06", "Závažná",
     "Aspirín kombinovaný s warfarínom významne zvyšuje riziko závažného krvácania, vrátane intrakraniálneho krvácania. Duálne antitrombocytové a antikoagulačné účinky znásobujú riziko krvácania.",
     "Vyhnite sa, pokiaľ nie je špecificky indikované (napr. mechanická srdcová chlopňa). Ak je kombinácia nutná, použite najnižšiu dávku aspirínu (75-100 mg) a často monitorujte INR.",
     "Posúďte, či je duálna terapia skutočne potrebná. Zvážte klopidogrel, ak je antitrombocytová liečba potrebná spolu s antikoaguláciou."),

    ("warfarin", "B01AA03", "ciprofloxacin", "J01MA02", "Závažná",
     "Ciprofloxacín inhibuje CYP1A2 a CYP3A4, čím znižuje metabolizmus warfarínu a výrazne zvyšuje INR. Riziko závažných krvácavých príhod.",
     "Ak je kombinácia nevyhnutná, znížte dávku warfarínu o 25-50% a monitorujte INR do 3 dní od začatia ciprofloxacínu. Prekontrolujte INR po ukončení antibiotika.",
     "Amoxicilín alebo cefalosporíny majú menší vplyv na metabolizmus warfarínu."),

    ("warfarin", "B01AA03", "metronidazole", "J01XD01", "Závažná",
     "Metronidazol inhibuje CYP2C9, hlavný enzým pre metabolizmus S-warfarínu, čo vedie k výrazne zvýšenému INR a riziku krvácania.",
     "Znížte dávku warfarínu o 25-50% pri začatí metronidazolu. Monitorujte INR v deň 3-5. Upravte dávku warfarínu po ukončení metronidazolu.",
     "Zvážte alternatívne antibiotiká na základe indikácie."),

    ("warfarin", "B01AA03", "clarithromycin", "J01FA09", "Závažná",
     "Klaritromycín inhibuje CYP3A4, čím znižuje metabolizmus warfarínu a zvyšuje antikoagulačný účinok. INR sa môže zvýšiť 2-3 násobne.",
     "Dôsledne monitorujte INR. Zvážte empirické zníženie dávky warfarínu o 25-33%. Upravte dávku podľa odpovede INR.",
     "Azitromycín má menšiu inhibíciu CYP3A4 a môže byť preferovaný."),

    ("warfarin", "B01AA03", "amiodarone", "C01BD01", "Závažná",
     "Amiodarón je silný inhibítor CYP2C9 a CYP3A4, výrazne zvyšujúci hladiny warfarínu. Interakcia môže pretrvávať týždne až mesiace po vysadení amiodarónu kvôli jeho dlhému polčasu (~40 dní).",
     "Znížte dávku warfarínu o 30-50% pri zahájení amiodarónu. Monitorujte INR týždenne počas prvého mesiaca, potom mesačne. Uvedomte si, že INR sa môže naďalej zvyšovať niekoľko týždňov.",
     "Žiadna priama alternatíva pre indikáciu amiodarónu, ale zvážte NOAK ak je potrebná flexibilita antikoagulácie."),

    ("sertraline", "N06AB06", "tramadol", "N02AX02", "Závažná",
     "Riziko serotonínového syndrómu. Sertralín (SSRI) aj tramadol majú serotonergickú aktivitu. Kombinácia môže spôsobiť potenciálne život ohrozujúci serotonínový syndróm: agitáciu, hypertermiu, myoklonus, zmeny duševného stavu.",
     "Vyhnite sa kombinácii ak je to možné. Ak musíte spolupredpisovať, použite najnižšie účinné dávky a monitorujte príznaky serotonínového syndrómu. Poučte pacienta o varovných príznakoch.",
     "Paracetamol, nízke dávky NSAID (ak nie sú kontraindikované) alebo neserotonergické analgetiká ako gabapentín na zvládnutie bolesti."),

    ("escitalopram", "N06AB10", "tramadol", "N02AX02", "Závažná",
     "Riziko serotonínového syndrómu. Escitalopram (SSRI) aj tramadol zvyšujú serotonergickú aktivitu. Potenciálne fatálna reakcia.",
     "Vyhnite sa kombinácii. Použite alternatívne analgetiká bez serotonergickej aktivity. Ak je to nevyhnutné, začnite s nízkymi dávkami a dôsledne monitorujte.",
     "Paracetamol, NSAID (ak sú vhodné) alebo gabapentín/pregabalín na bolesť."),

    ("fluoxetine", "N06AB03", "tramadol", "N02AX02", "Závažná",
     "Riziko serotonínového syndrómu. Fluoxetín je silné SSRI a inhibítor CYP2D6, ktorý tiež znižuje premenu tramadolu na jeho aktívny metabolit. Paradoxne to môže znížiť analgetickú účinnosť aj zvýšiť riziko sérotonénovej toxicity.",
     "Vyhnite sa kombinácii. Zvoľte neserotonergické analgetikum. Ak je SSRI nevyhnutné, zvážte analgetiká bez serotonergickej aktivity.",
     "Paracetamol alebo neserotonergické analgetiká."),

    ("paroxetine", "N06AB05", "tramadol", "N02AX02", "Závažná",
     "Riziko serotonínového syndrómu. Paroxetín je silné SSRI a CYP2D6 inhibítor. Kombinácia s tramadolom zvyšuje riziko serotonénovej toxicity.",
     "Vyhnite sa kombinácii. Použite alternatívne analgetiká bez serotonergickej aktivity.",
     "Paracetamol alebo gabapentín/pregabalín."),

    ("venlafaxine", "N06AX16", "tramadol", "N02AX02", "Závažná",
     "Vysoké riziko serotonínového syndrómu. Venlafaxín (SNRI) a tramadol majú silnú serotonergickú aktivitu. Kombinácia je obzvlášť nebezpečná.",
     "Kontraindikovaná kombinácia. Použite alternatívne analgetikum. Ak musíte kombinovať, najnižšie dávky s intenzívnym monitorovaním.",
     "Paracetamol, NSAID, gabapentín alebo pregabalín."),

    ("duloxetine", "N06AX21", "tramadol", "N02AX02", "Závažná",
     "Riziko serotonínového syndrómu. Duloxetín (SNRI) a tramadol – oba zvyšujú serotonín. Duloxetín navyše inhibuje CYP2D6.",
     "Vyhnite sa kombinácii. Použite alternatívne analgetiká.",
     "Paracetamol, gabapentín, pregabalín."),

    ("lithium", "N05AN01", "ibuprofen", "M01AE01", "Závažná",
     "NSAID znižujú renálny klírens lítia, potenciálne zvyšujú hladiny lítia o 15-50% a spôsobujú toxicitu lítiom (tremor, zmätenosť, poškodenie obličiek, srdcové arytmie).",
     "Vyhnite sa NSAID u pacientov na lítiu ak je to možné. Ak je NSAID nevyhnutné, monitorujte hladiny lítia do 5-7 dní a podľa toho upravte dávku.",
     "Paracetamol je preferované analgetikum. Aspirín v nízkych dávkach má menší vplyv na hladiny lítia."),

    ("lithium", "N05AN01", "diclofenac", "M01AB05", "Závažná",
     "Diklofenak znižuje renálny klírens lítia, čo vedie k zvýšeným hladinám lítia a riziku toxicity.",
     "Vyhnite sa kombinácii. Monitorujte hladiny lítia ak je NSAID nevyhnutné.",
     "Paracetamol. Topické NSAID môžu mať menší systémový účinok."),

    ("lithium", "N05AN01", "naproxen", "M01AE02", "Závažná",
     "Naproxén znižuje renálny klírens lítia, zvyšuje hladiny lítia a riziko toxicity.",
     "Vyhnite sa. Použite paracetamol na zvládnutie bolesti.",
     "Paracetamol."),

    ("lithium", "N05AN01", "celecoxib", "M01AH01", "Závažná",
     "Aj selektívne COX-2 inhibítory ako celekoxib môžu zvýšiť hladiny lítia znížením renálnej eliminácie.",
     "Vyhnite sa alebo monitorujte hladiny lítia. Celekoxib má menší vplyv ako neselektívne NSAID, ale riziko pretrváva.",
     "Paracetamol."),

    ("digoxin", "C01AA05", "amiodarone", "C01BD01", "Závažná",
     "Amiodarón zvyšuje hladiny digoxínu o 70-100% prostredníctvom inhibície P-glykoproteínu a zníženého renálneho klírensu. Kombinované účinky na AV uzol zvyšujú riziko bradykardie a srdcového bloku.",
     "Znížte dávku digoxínu o 50% pri začatí amiodarónu. Monitorujte hladiny digoxínu a EKG. Sledujte príznaky toxicity digoxínu.",
     "Zvážte kontrolu frekvencie betablokátorom namiesto digoxínu ak je to vhodné."),

    ("digoxin", "C01AA05", "verapamil", "C08DA01", "Závažná",
     "Verapamil zvyšuje hladiny digoxínu o 50-75% inhibíciou P-glykoproteínu. Oba lieky spomaľujú vedenie cez AV uzol, čím zvyšujú riziko úplného srdcového bloku a bradykardie.",
     "Znížte dávku digoxínu o 25-50% pri pridaní verapamilu. Dôsledne monitorujte hladiny digoxínu a srdcovú frekvenciu/EKG.",
     "Zvážte amlodipín (dihydropyridínový BKK), ktorý má minimálny vplyv na hladiny digoxínu a AV vedenie."),

    ("simvastatin", "C10AA01", "clarithromycin", "J01FA09", "Závažná",
     "Klaritromycín je silný inhibítor CYP3A4, dramaticky zvyšujúci hladiny simvastatínu (až 10-násobne). Zvyšuje sa riziko rabdomyolýzy – potenciálne fatálneho rozpadu kostrového svalstva.",
     "KONTRAINDIKOVANÁ kombinácia. Pozastavte simvastatín počas liečby klaritromycínom. Obnovte 3 dni po ukončení antibiotika.",
     "Použite azitromycín namiesto klaritromycínu (minimálna inhibícia CYP3A4). Alebo zmeňte statín na rosuvastatín/pravastatín (nemetabolizované CYP3A4)."),

    ("simvastatin", "C10AA01", "amiodarone", "C01BD01", "Závažná",
     "Amiodarón inhibuje CYP3A4, čím zvyšuje hladiny simvastatínu a riziko myopatie/rabdomyolýzy. FDA odporúča maximálnu dávku simvastatínu 20 mg/deň s amiodarónom.",
     "Neprekračujte simvastatín 20 mg/deň s amiodarónom. Zvážte zmenu na pravastatín alebo rosuvastatín. Monitorujte bolesť/slabosť svalov.",
     "Pravastatín alebo rosuvastatín (nie sú substráty CYP3A4)."),

    ("simvastatin", "C10AA01", "verapamil", "C08DA01", "Závažná",
     "Verapamil inhibuje CYP3A4, čím zvyšuje expozíciu simvastatínom a riziko rabdomyolýzy. FDA obmedzuje simvastatín na 10 mg/deň s verapamilom.",
     "Neprekračujte simvastatín 10 mg/deň s verapamilom. Zvážte zmenu na statín nemetabolizovaný CYP3A4.",
     "Pravastatín alebo rosuvastatín."),

    ("carbamazepine", "N03AF01", "clarithromycin", "J01FA09", "Závažná",
     "Klaritromycín inhibuje CYP3A4, výrazne zvyšujúc hladiny karbamazepínu. Riziko toxicity karbamazepínu: závraty, ataxia, diplopia, nauzea, zmeny srdcového vedenia.",
     "Vyhnite sa kombinácii. Ak je antibiotikum potrebné, použite azitromycín. Ak musíte kombinovať, znížte dávku karbamazepínu a dôsledne monitorujte hladiny.",
     "Azitromycín má minimálnu inhibíciu CYP3A4."),

    ("clopidogrel", "B01AC04", "omeprazole", "A02BC01", "Závažná",
     "Omeprazol inhibuje CYP2C19, ktorý je potrebný na premenu klopidogrelu na jeho aktívny metabolit. To môže znížiť antitrombocytový účinok klopidogrelu a zvýšiť kardiovaskulárne riziko.",
     "Vyhnite sa omeprazolu s klopidogrelom. Použite namiesto neho pantoprazol (menšia inhibícia CYP2C19). Ak je PPI potrebný, pantoprazol je preferovaný.",
     "Pantoprazol alebo H2 blokátory (famotidín) na gastroprotekciu."),

    ("rivaroxaban", "B01AF01", "ibuprofen", "M01AE01", "Závažná",
     "Kombinácia NOAK s NSAID výrazne zvyšuje riziko krvácania. NSAID spôsobujú poškodenie sliznice GIT a inhibujú funkciu trombocytov, čím znásobujú riziko krvácania pri antikoagulačnej liečbe.",
     "Vyhnite sa kombinácii. Ak je krátkodobé použitie NSAID nevyhnutné, použite najnižšiu dávku na najkratšiu dobu. Zvážte PPI na ochranu GIT.",
     "Paracetamol na zvládnutie bolesti."),

    ("apixaban", "B01AF02", "ibuprofen", "M01AE01", "Závažná",
     "NSAID zvyšujú riziko krvácania s NOAK prostredníctvom antitrombocytových účinkov a poškodenia sliznice GIT.",
     "Vyhnite sa. Použite paracetamol na bolesť. Ak je NSAID nevyhnutné, najkratší cyklus s gastroprotekciou.",
     "Paracetamol."),

    ("sulfamethoxazole/trimethoprim", "J01EE01", "warfarin", "B01AA03", "Závažná",
     "Trimetoprim-sulfametoxazol výrazne zvyšuje účinok warfarínu inhibíciou CYP2C9 a vytesnením warfarínu z väzby na bielkoviny. INR sa môže dramaticky zvýšiť v priebehu 3-5 dní.",
     "Empiricky znížte dávku warfarínu o 25-50%. Monitorujte INR do 3-5 dní. Silný klinický dôkaz pre významnú interakciu.",
     "Zvážte alternatívne antibiotikum na základe indikácie."),

    ("valproic acid", "N03AG01", "lamotrigine", "N03AX09", "Závažná",
     "Kyselina valproová inhibuje glukuronidáciu lamotrigínu, čím zdvojnásobuje jeho polčas a hladiny. Zvýšené riziko závažných kožných reakcií vrátane Stevensovho-Johnsonovho syndrómu.",
     "Pri kombinácii s valproátom začnite lamotrigín na polovičnej dávke a titrujte pomaly. Maximálna dávka lamotrigínu je zvyčajne 100-200 mg/deň.",
     None),

    ("fluconazole", "J02AC01", "warfarin", "B01AA03", "Závažná",
     "Flukonazol je silný inhibítor CYP2C9, výrazne zvyšujúci hladiny warfarínu a riziko krvácania.",
     "Znížte dávku warfarínu o 25-50% a monitorujte INR do 3-5 dní od začiatku flukonazolu.",
     None),

    ("fluconazole", "J02AC01", "simvastatin", "C10AA01", "Závažná",
     "Flukonazol inhibuje CYP3A4 a CYP2C9, výrazne zvyšujúc hladiny simvastatínu. Riziko rabdomyolýzy.",
     "Pozastavte simvastatín počas liečby flukonazolom.",
     "Pravastatín alebo rosuvastatín."),

    # --- STREDNÉ (Moderate) ---
    ("simvastatin", "C10AA01", "amlodipine", "C08CA01", "Stredná",
     "Amlodipín inhibuje CYP3A4, mierne zvyšujúc hladiny simvastatínu (1,5-2x). Zvýšené riziko myopatie, najmä pri vyšších dávkach simvastatínu.",
     "Neprekračujte simvastatín 20 mg/deň pri súbežnom podávaní s amlodipínom. Monitorujte bolesti svalov, citlivosť alebo slabosť.",
     "Zvážte atorvastatín (menej ovplyvnený) alebo rosuvastatín/pravastatín (nie sú substráty CYP3A4)."),

    ("atorvastatin", "C10AA05", "clarithromycin", "J01FA09", "Stredná",
     "Klaritromycín inhibuje CYP3A4, čím zvyšuje hladiny atorvastatínu. Nižšie riziko ako pri simvastatíne, ale riziko myopatie je stále zvýšené.",
     "Zvážte dočasné zníženie dávky atorvastatínu počas liečby klaritromycínom. Ak je to možné, použite azitromycín. Monitorujte príznaky svalov.",
     "Azitromycín. Alebo dočasne prejdite na rosuvastatín/pravastatín."),

    ("metformin", "A10BA02", "ciprofloxacin", "J01MA02", "Stredná",
     "Fluorochinolóny môžu spôsobiť hypoglykémiu aj hyperglykémiu. V kombinácii s metformínom môže byť riziko hypoglykémie zvýšené. Ciprofloxacín môže tiež zvýšiť hladiny metformínu prostredníctvom inhibície renálnych transportérov.",
     "Dôsledne monitorujte glykémiu počas liečby ciprofloxacínom. Poučte pacienta o príznakoch hypoglykémie. Zvážte úpravu dávky ak je to potrebné.",
     "Použite alternatívne antibiotiká ak je to možné (amoxicilín, cefalosporíny)."),

    ("ramipril", "C09AA05", "spironolactone", "C03DA01", "Stredná",
     "ACE inhibítory aj spironolaktón zvyšujú retenciu draslíka. Kombinované použitie zvyšuje riziko hyperkaliémie, najmä u pacientov s poruchou funkcie obličiek.",
     "Monitorujte sérový draslík do 1 týždňa od začiatku kombinácie, potom pravidelne. Vyhnite sa doplnkom draslíka. Zabezpečte primeranú funkciu obličiek.",
     "Zvážte tiazidové diuretikum namiesto spironolaktónu ak je riziko hyperkaliémie vysoké."),

    ("enalapril", "C09AA02", "spironolactone", "C03DA01", "Stredná",
     "ACE inhibítor + draslík šetriace diuretikum: riziko hyperkaliémie, najmä u starších pacientov alebo tých s poruchou funkcie obličiek.",
     "Monitorujte draslík a funkciu obličiek. Vyhnite sa doplnkom draslíka a soľným náhradám obsahujúcim draslík.",
     "Zvážte kľučkové diuretikum (furosemid) alebo tiazid."),

    ("ramipril", "C09AA05", "ibuprofen", "M01AE01", "Stredná",
     "NSAID znižujú antihypertenzný účinok ACE inhibítorov a zvyšujú riziko akútneho poškodenia obličiek, najmä u dehydrovaných pacientov alebo pacientov s už existujúcim poškodením obličiek.",
     "Monitorujte krvný tlak a funkciu obličiek. Zabezpečte dostatočnú hydratáciu. Použite NSAID na najkratšiu dobu v najnižšej dávke.",
     "Paracetamol na zvládnutie bolesti (neovplyvňuje kontrolu krvného tlaku)."),

    ("enalapril", "C09AA02", "ibuprofen", "M01AE01", "Stredná",
     "NSAID oslabujú antihypertenzný účinok ACE inhibítora cez inhibíciu prostaglandínov. Riziko trojitého úderu (ACE inhibítor + NSAID + diuretikum) pre akútne poškodenie obličiek.",
     "Vyhnite sa trojitej kombinácii. Monitorujte funkciu obličiek a krvný tlak pri použití NSAID.",
     "Paracetamol."),

    ("losartan", "C09CA01", "ibuprofen", "M01AE01", "Stredná",
     "NSAID znižujú antihypertenzný účinok sartanov a zvyšujú riziko nefrotoxicity, podobne ako pri interakcii s ACE inhibítormi.",
     "Monitorujte krvný tlak a funkciu obličiek. Krátkodobé použitie NSAID v najnižšej dávke ak je to potrebné.",
     "Paracetamol."),

    ("metformin", "A10BA02", "furosemide", "C03CA01", "Stredná",
     "Furosemid môže znížiť klírens metformínu, čím sa zvýšia plazmatické hladiny metformínu. Dehydratácia z diuretík zvyšuje riziko laktátovej acidózy pri metformíne.",
     "Zabezpečte dostatočnú hydratáciu. Monitorujte funkciu obličiek. Zvážte úpravu dávky metformínu ak GFR klesne.",
     None),

    ("omeprazole", "A02BC01", "levothyroxine", "H03AA01", "Stredná",
     "PPI znižujú žalúdočnú kyselinu, ktorá je potrebná na vstrebávanie levotyroxínu. Dlhodobé užívanie PPI môže viesť k suboptimálnym hladinám levotyroxínu a hypotyreóze.",
     "Užívajte levotyroxín aspoň 30-60 minút pred omeprazolom. Monitorujte TSH pri začatí alebo ukončení PPI. Môže byť potrebné zvýšenie dávky levotyroxínu.",
     "H2 blokátory (famotidín) majú menší vplyv na vstrebávanie levotyroxínu."),

    ("pantoprazole", "A02BC02", "levothyroxine", "H03AA01", "Stredná",
     "PPI znižujú žalúdočnú kyselinu potrebnú na vstrebávanie levotyroxínu. Môže vyžadovať úpravu dávky levotyroxínu.",
     "Oddeľte dávkovanie: levotyroxín ráno nalačno, PPI neskôr. Monitorujte TSH.",
     "H2 blokátory ak je potrebná supresia kyseliny."),

    ("carbamazepine", "N03AF01", "sertraline", "N06AB06", "Stredná",
     "Karbamazepín indukuje CYP3A4, potenciálne znižuje hladiny sertralínu a antidepresívnu účinnosť. Sertralín môže zvýšiť hladiny karbamazepínu.",
     "Monitorujte antidepresívnu odpoveď a hladiny karbamazepínu. Môže byť potrebné zvýšenie dávky sertralínu.",
     "Zvážte alternatívne antidepresívum menej ovplyvnené enzýmovou indukciou (napr. escitalopram)."),

    ("metoprolol", "C07AB02", "verapamil", "C08DA01", "Stredná",
     "Oba lieky spomaľujú srdcovú frekvenciu a AV vedenie. Kombinované použitie zvyšuje riziko závažnej bradykardie, AV bloku a hypotenzie.",
     "Vyhnite sa kombinácii alebo používajte s mimoriadnou opatrnosťou. Dôsledne monitorujte srdcovú frekvenciu a EKG. Znížte dávky oboch liekov.",
     "Použite amlodipín (dihydropyridínový BKK) namiesto verapamilu ak je blokáda kalciových kanálov potrebná s betablokátorom."),

    ("bisoprolol", "C07AB07", "verapamil", "C08DA01", "Stredná",
     "Kombinované negatívne chronotropné a dromotropné účinky zvyšujú riziko bradykardie a srdcového bloku.",
     "Vyhnite sa kombinácii. Ak je to nevyhnutné, dôsledne monitorujte srdcovú frekvenciu a EKG.",
     "Amlodipín namiesto verapamilu."),

    ("glimepiride", "A10BB12", "ciprofloxacin", "J01MA02", "Stredná",
     "Fluorochinolóny môžu zosilniť hypoglykemický účinok sulfonylurey. Riziko závažnej hypoglykémie.",
     "Dôsledne monitorujte glykémiu. Zvážte empirické zníženie dávky sulfonylurey počas liečby antibiotikom.",
     "Použite alternatívne antibiotikum ak je to možné."),

    ("allopurinol", "M04AA01", "ramipril", "C09AA05", "Stredná",
     "Zvýšené riziko hypersenzitívnych reakcií a leukopénie pri kombinácii alopurinolu s ACE inhibítormi, najmä pri poruche funkcie obličiek.",
     "Pravidelne monitorujte krvný obraz. Poučte pacienta o príznakoch hypersenzitivity (vyrážka, horúčka). Zabezpečte primeranú funkciu obličiek.",
     None),

    ("prednisone", "H02AB07", "ibuprofen", "M01AE01", "Stredná",
     "Kombinované použitie výrazne zvyšuje riziko GI krvácania a peptického vredu. Oba lieky poškodzujú žalúdočnú sliznicu rôznymi mechanizmami.",
     "Vyhnite sa kombinácii ak je to možné. Ak musíte spolupredpisovať, pridajte PPI na gastroprotekciu (omeprazol alebo pantoprazol). Monitorujte GI príznaky.",
     "Paracetamol na bolesť. Topické NSAID na lokalizovanú bolesť."),

    ("prednisone", "H02AB07", "diclofenac", "M01AB05", "Stredná",
     "Zvýšené riziko GI krvácania. Kortikosteroidy a NSAID sú nezávisle spojené s peptickou ulceráciou.",
     "Pridajte PPI ak je kombinácia nevyhnutná. Monitorujte GI príznaky. Používajte najkratší cyklus oboch liekov.",
     "Paracetamol."),

    ("digoxin", "C01AA05", "furosemide", "C03CA01", "Stredná",
     "Furosemidom vyvolaná hypokaliémia zvyšuje citlivosť na toxicitu digoxínu. Nízke hladiny draslíka zosilňujú väzbu digoxínu na Na+/K+ ATPázu.",
     "Monitorujte hladiny draslíka. Udržiavajte draslík >4,0 mmol/l. Zvážte suplementáciu draslíka alebo draslík šetriace diuretikum.",
     None),

    ("digoxin", "C01AA05", "hydrochlorothiazide", "C03AA03", "Stredná",
     "Tiazidmi vyvolaná hypokaliémia a hypomagneziémia zvyšujú riziko toxicity digoxínu (arytmie, nauzea, poruchy videnia).",
     "Pravidelne monitorujte elektrolyty. Doplňte draslík ak je to potrebné. Monitorujte hladiny digoxínu.",
     None),

    ("warfarin", "B01AA03", "paracetamol", "N02BE01", "Stredná",
     "Pravidelné užívanie paracetamolu (>2g/deň počas >1 týždňa) môže zosilniť antikoagulačný účinok warfarínu, mierne zvyšujúc INR. Mechanizmus zahŕňa inhibíciu syntézy koagulačných faktorov závislých od vitamínu K.",
     "Paracetamol je stále preferovaný pred NSAID pri warfaríne. Monitorujte INR ak sa paracetamol užíva pravidelne vo vyšších dávkach (>2g/deň). Príležitostné užívanie v štandardných dávkach je zvyčajne bezpečné.",
     None),

    ("azithromycin", "J01FA10", "warfarin", "B01AA03", "Stredná",
     "Azitromycín môže mierne zvýšiť účinok warfarínu, hoci menej ako klaritromycín. Mechanizmus môže zahŕňať zmenu črevnej flóry znižujúcu produkciu vitamínu K.",
     "Monitorujte INR počas liečby azitromycínom a krátko po nej. Zvyčajne nie je potrebná úprava dávky.",
     None),

    ("levothyroxine", "H03AA01", "calcium carbonate", "A12AA04", "Stredná",
     "Vápnik znižuje vstrebávanie levotyroxínu cheláciou v GIT. Môže viesť k suboptimálnym hladinám hormónov štítnej žľazy.",
     "Oddeľte podávanie aspoň o 4 hodiny. Užívajte levotyroxín ráno nalačno, vápnik neskôr cez deň.",
     None),

    ("doxycycline", "J01AA02", "calcium carbonate", "A12AA04", "Stredná",
     "Vápnik tvorí nerozpustné cheláty s tetracyklínmi, čím výrazne znižuje vstrebávanie doxycyklínu a účinnosť antibiotika.",
     "Oddeľte dávkovanie o 2-3 hodiny. Užívajte doxycyklín 1 hodinu pred alebo 2 hodiny po vápniku.",
     None),

    ("ciprofloxacin", "J01MA02", "calcium carbonate", "A12AA04", "Stredná",
     "Vápnik chelátuje fluorochinolóny, čím znižuje vstrebávanie ciprofloxacínu až o 40%.",
     "Oddeľte dávkovanie aspoň 2 hodiny pred alebo 6 hodín po vápniku.",
     None),

    ("pregabalin", "N03AX16", "diazepam", "N05BA01", "Stredná",
     "Aditívna depresia CNS. Oba lieky spôsobujú sedáciu, závraty a kognitívne poruchy. Kombinované použitie zvyšuje riziko pádov, najmä u starších.",
     "Použite najnižšie účinné dávky. Upozornite pacienta na zvýšenú sedáciu a riziko pádov. Vyhnite sa riadeniu vozidla alebo obsluhe strojov.",
     None),

    ("gabapentin", "N03AX12", "tramadol", "N02AX02", "Stredná",
     "Aditívna depresia CNS a riziko útlmu dýchania. Oba lieky spôsobujú sedáciu a môžu narušiť dýchanie.",
     "Použite najnižšie účinné dávky. Monitorujte nadmernú sedáciu a útlm dýchania. Poučte pacienta o rizikách.",
     None),

    ("pentoxifylline", "C04AD03", "warfarin", "B01AA03", "Stredná",
     "Pentoxifylín má antitrombocytové vlastnosti a môže zvýšiť riziko krvácania v kombinácii s warfarínom.",
     "Monitorujte INR a sledujte príznaky krvácania. Môže byť potrebná úprava dávky warfarínu.",
     None),

    ("metoclopramide", "A03FA01", "sertraline", "N06AB06", "Stredná",
     "Oba lieky zvyšujú serotonergickú aktivitu. Riziko extrapyramídových príznakov a serotonínového syndrómu pri kombinovanom použití.",
     "Vyhnite sa kombinácii ak je to možné. Používajte na najkratšiu dobu. Monitorujte príznaky serotonínového syndrómu.",
     "Domperidón (neprechádza hematoencefalickou bariérou) na motilitu GIT."),

    ("sulfamethoxazole/trimethoprim", "J01EE01", "metformin", "A10BA02", "Stredná",
     "Trimetoprim znižuje renálnu tubulárnu sekréciu metformínu, potenciálne zvyšujúc hladiny metformínu a riziko laktátovej acidózy.",
     "Monitorujte glykémiu a funkciu obličiek. Zvážte zníženie dávky metformínu počas liečby antibiotikom.",
     None),

    ("doxycycline", "J01AA02", "warfarin", "B01AA03", "Stredná",
     "Doxycyklín môže zosilniť antikoagulačný účinok warfarínu zmenou črevnej flóry a zníženou produkciou vitamínu K.",
     "Monitorujte INR počas liečby doxycyklínom.",
     None),

    ("ciprofloxacin", "J01MA02", "levothyroxine", "H03AA01", "Stredná",
     "Ciprofloxacín môže tvoriť chelačné komplexy s levotyroxínom, čím znižuje jeho vstrebávanie.",
     "Oddeľte podávanie aspoň o 4 hodiny. Užívajte levotyroxín prvý, ciprofloxacín neskôr.",
     None),

    ("sildenafil", "G04BE03", "amlodipine", "C08CA01", "Stredná",
     "Aditívny hypotenzný účinok. Sildenafil aj amlodipín znižujú krvný tlak. Kombinácia môže viesť k symptomatickej hypotenzii.",
     "Poučte pacienta o riziku hypotenzie. Monitorujte krvný tlak. Začnite s nižšou dávkou sildenafilu.",
     None),

    ("amlodipine", "C08CA01", "simvastatin", "C10AA01", "Stredná",
     "Amlodipín inhibuje CYP3A4, čím zvyšuje expozíciu simvastatínom. FDA odporúča max. simvastatín 20 mg/deň s amlodipínom.",
     "Obmedzte simvastatín na 20 mg/deň. Monitorujte príznaky myopatie.",
     "Prejdite na atorvastatín, rosuvastatín alebo pravastatín."),

    # --- MIERNE (Minor) ---
    ("omeprazole", "A02BC01", "calcium carbonate", "A12AA04", "Mierna",
     "PPI znižujú žalúdočnú kyselinu, ktorá je potrebná na optimálne vstrebávanie uhličitanu vápenatého. Dlhodobé užívanie PPI môže znížiť vstrebávanie vápnika a zvýšiť riziko zlomenín.",
     "Zvážte citrát vápenatý namiesto uhličitanu vápenatého (vstrebávanie nezávislé od kyseliny). Zabezpečte dostatočný príjem vitamínu D. Nie je potrebné okamžité opatrenie pri krátkodobom užívaní PPI.",
     "Citrát vápenatý."),

    ("pantoprazole", "A02BC02", "calcium carbonate", "A12AA04", "Mierna",
     "Znížené vstrebávanie vápnika v dôsledku zníženej žalúdočnej kyseliny z PPI.",
     "Pri dlhodobom užívaní PPI prejdite na citrát vápenatý. Zabezpečte dostatočnosť vitamínu D.",
     "Citrát vápenatý."),

    ("metformin", "A10BA02", "omeprazole", "A02BC01", "Mierna",
     "PPI môžu mierne zvýšiť vstrebávanie metformínu. Klinický význam je zvyčajne minimálny.",
     "Zvyčajne nie je potrebná úprava dávky. Monitorujte glykémiu ak sa PPI začne alebo ukončí.",
     None),

    ("metoprolol", "C07AB02", "sertraline", "N06AB06", "Mierna",
     "Sertralín je slabý inhibítor CYP2D6 a môže mierne zvýšiť hladiny metoprololu. Zvyčajne nie je klinicky významné.",
     "Monitorujte srdcovú frekvenciu a krvný tlak. Úprava dávky zvyčajne nie je potrebná.",
     None),

    ("diazepam", "N05BA01", "omeprazole", "A02BC01", "Mierna",
     "Omeprazol inhibuje CYP2C19, ktorý metabolizuje diazepam. Môže mierne zvýšiť hladiny diazepamu a predĺžiť sedáciu.",
     "Monitorujte nadmernú sedáciu. Zvážte zníženie dávky diazepamu ak je to potrebné. Použite lorazepam (nie je substrát CYP2C19) ako alternatívu.",
     "Lorazepam alebo oxazepam (metabolizmus na báze glukuronidácie)."),

    ("zolpidem", "N05CF02", "sertraline", "N06AB06", "Mierna",
     "Aditívna depresia CNS. Oba lieky môžu spôsobiť sedáciu. Sertralín môže mierne zvýšiť hladiny zolpidemu.",
     "Monitorujte nadmernú sedáciu. Zvážte nižšiu dávku zolpidemu.",
     None),

    ("quetiapine", "N05AH04", "sertraline", "N06AB06", "Mierna",
     "Aditívna sedácia a potenciálne predĺženie QT intervalu. Oba lieky môžu spôsobiť ospalosť.",
     "Monitorujte nadmernú sedáciu a zvážte EKG ak existujú rizikové faktory pre predĺženie QT intervalu.",
     None),

    ("furosemide", "C03CA01", "ramipril", "C09AA05", "Mierna",
     "Hypotenzia po prvej dávke pri začatí ACE inhibítora u pacientov na diuretikách. Diuretikmi vyvolaná deplécia objemu zosilňuje hypotenzný účinok ACE inhibítora.",
     "Zvážte vynechanie diuretika 24-48 hodín pred prvou dávkou ACE inhibítora alebo začnite ACE inhibítor v nízkej dávke. Dôsledne monitorujte krvný tlak.",
     None),

    ("hydrochlorothiazide", "C03AA03", "ramipril", "C09AA05", "Mierna",
     "Zosilnený hypotenzný účinok. Bežne používaná terapeutická kombinácia, ale možná hypotenzia po prvej dávke.",
     "Začnite ACE inhibítor v nízkej dávke. Monitorujte krvný tlak, draslík a funkciu obličiek.",
     None),

    ("tizanidine", "M03BX02", "ciprofloxacin", "J01MA02", "Závažná",
     "Ciprofloxacín je silný inhibítor CYP1A2, výrazne zvyšujúci hladiny tizanidínu (až 10-násobne). Riziko závažnej hypotenzie, sedácie a bradykardie.",
     "KONTRAINDIKOVANÁ kombinácia. Nepoužívajte tizanidín s ciprofloxacínom.",
     "Použite alternatívne antibiotikum alebo alternatívne myorelaxancium (baklofén, tolperizón)."),
]
# fmt: on


def seed():
    import os

    os.makedirs(DB_PATH.parent, exist_ok=True)

    # Remove existing DB to start fresh
    if DB_PATH.exists():
        DB_PATH.unlink()

    # Import and run init_db
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.database import init_db

    init_db()

    from extra_data import EXTRA_DRUGS, EXTRA_INTERACTIONS

    conn = sqlite3.connect(str(DB_PATH))

    all_drugs = DRUGS + EXTRA_DRUGS
    all_interactions = INTERACTIONS + EXTRA_INTERACTIONS

    # Insert drugs
    conn.executemany(
        "INSERT INTO drugs (trade_name, active_substance, atc_code, strength, form, sukl_code) VALUES (?, ?, ?, ?, ?, ?)",
        all_drugs,
    )

    # Insert interactions
    conn.executemany(
        "INSERT INTO interactions (drug_a, drug_a_atc, drug_b, drug_b_atc, severity, mechanism, management, alternatives) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        all_interactions,
    )

    conn.commit()

    drug_count = conn.execute("SELECT COUNT(*) FROM drugs").fetchone()[0]
    interaction_count = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]

    severity_counts = {}
    for row in conn.execute("SELECT severity, COUNT(*) FROM interactions GROUP BY severity").fetchall():
        severity_counts[row[0]] = row[1]

    print(f"Nasadených {drug_count} liekov")
    print(f"Nasadených {interaction_count} interakcií:")
    for sev, count in sorted(severity_counts.items()):
        print(f"  {sev}: {count}")

    conn.close()


if __name__ == "__main__":
    seed()
