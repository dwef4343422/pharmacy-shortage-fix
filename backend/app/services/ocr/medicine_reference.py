"""
Medicine Reference Database — canonical names used for verification matching.

Requirement #10 asks us to match OCR'd medicine names against *the medicine
database* with RapidFuzz (>= 90% similarity). This module is the default source
of canonical names. In a deployment with a populated medicines table you can
replace ``get_reference_medicines()`` with a query (e.g. ``SELECT DISTINCT name
FROM medicines``) — the matcher only needs an iterable of candidate strings, so
the rest of the pipeline is unchanged.

The list below is a curated starter set of common pharmaceutical products
(English + a few Arabic) so the matcher works out-of-the-box on a fresh DB.
"""

from __future__ import annotations

from typing import List

# English common medicines / active ingredients.
_ENGLISH = [
    "Paracetamol", "Panadol", "Panadol Extra", "Calpol", "Tylenol",
    "Ibuprofen", "Brufen", "Nurofen", "Aspirin", "Disprin",
    "Amoxicillin", "Amoxil", "Augmentin", "Clavulanic Acid",
    "Azithromycin", "Zithromax", "Ciprofloxacin", "Cipro", "Levofloxacin",
    "Metronidazole", "Flagyl", "Omeprazole", "Losec", "Pantoprazole",
    "Ranitidine", "Zantac", "Cetirizine", "Zyrtec", "Loratadine", "Claritin",
    "Diphenhydramine", "Benadryl", "Prednisolone", "Prednisone", "Dexamethasone",
    "Salbutamol", "Ventolin", "Albuterol", "Montelukast", "Singulair",
    "Insulin", "Metformin", "Glucophage", "Glibenclamide", "Glyburide",
    "Amlodipine", "Norvasc", "Losartan", "Cozaar", "Enalapril", "Ramipril",
    "Atenolol", "Propranolol", "Bisoprolol", "Furosemide", "Lasix",
    "Warfarin", "Clopidogrel", "Plavix", "Aspirin", "Atorvastatin", "Lipitor",
    "Simvastatin", "Rosuvastatin", "Cefixime", "Ceftriaxone", "Rocephin",
    "Doxycycline", "Tetracycline", "Clindamycin", "Erythromycin",
    "Ondansetron", "Zofran", "Domperidone", "Motilium", "Ranitidine",
    "Loperamide", "Imodium", "ORS", "Oral Rehydration Salts",
    "Vitamin C", "Ascorbic Acid", "Vitamin D", "Vitamin B12", "Folic Acid",
    "Ferrous Sulfate", "Iron Supplement", "Calcium", "Zinc",
    "Hydrocortisone", "Betamethasone", "Clotrimazole", "Fluconazole",
    "Amphotericin", "Acyclovir", "Zovirax", "Valacyclovir",
    "Tramadol", "Tapentadol", "Morphine", "Codeine", "Paracetamol Codeine",
    "Diclofenac", "Voltaren", "Naproxen", "Indomethacin",
    "Gabapentin", "Pregabalin", "Lyrica", "Carbamazepine", "Phenytoin",
    "Saline", "Sodium Chloride", "Glucose", "Dextrose", "Ringer Lactate",
    "Adrenaline", "Epinephrine", "Noradrenaline", "Dopamine", "Atropine",
    "Heparin", "Enoxaparin", "Clexane", "Gentamicin", "Neomycin",
    "Ketoconazole", "Miconazole", "Terbinafine", "Lamisil",
]

# A few common Arabic medicine names (kept normalized-friendly).
_ARABIC = [
    "باراسيتامول", "بنادول", "ايبوبروفين", "بروفين", "اموكسيسيلين",
    "اموكسيل", "اوغمنتين", "ازيثرومايسين", "سيبروفلوكساسين", "ميترونيدازول",
    "اوميبرازول", "لوسيك", "سيتيريزين", "ميتفورمين", "انالابرil",
    "سالبوتامول", "فنتولين", "انسولين", "ديكلوفيناك", "فولتارين",
]

# Combined, de-duplicated canonical list.
_REFERENCE: List[str] = sorted({*_ENGLISH, *_ARABIC}, key=lambda s: s.lower())


def get_reference_medicines() -> List[str]:
    """Return the canonical medicine-name list used for verification matching."""
    return list(_REFERENCE)


def set_reference_medicines(names: List[str]) -> None:
    """Override the reference list (e.g. with DB-sourced names). Test hook."""
    global _REFERENCE
    _REFERENCE = sorted(set(names), key=lambda s: s.lower())
