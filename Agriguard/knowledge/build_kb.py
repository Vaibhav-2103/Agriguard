#!/usr/bin/env python3
"""
AgriGuard Knowledge Base Builder
Generates knowledge/diseases.json for all classes in class_names.json
adhering strictly to agricultural IPM guidelines:
- Active ingredients only (no brand names, no exact dosage numbers)
- Cultural and organic solutions first, chemical interventions last
- Full safety precautions (PPE, Pre-Harvest Intervals, bee/pollinator protection, aquatic buffer)
- Comprehensive FAQ for intent matching in AgriBot
"""

import json
from pathlib import Path


def build_knowledge_base():
    class_names_path = Path("ml/outputs/class_names.json")
    if not class_names_path.exists():
        class_names_path = Path("class_names.json")
    
    with open(class_names_path, "r", encoding="utf-8") as f:
        class_names = json.load(f)

    # Base templates and disease definitions
    kb_data = {}

    for c_id in class_names:
        if "___" in c_id:
            crop_raw, disease_raw = c_id.split("___", 1)
        else:
            crop_raw, disease_raw = "Plant", c_id
        
        crop = crop_raw.replace("_", " ").replace("(", " (").replace("  ", " ").strip()
        disease_clean = disease_raw.replace("_", " ").strip()
        if disease_clean.endswith("_"):
            disease_clean = disease_clean[:-1].strip()

        is_healthy = "healthy" in disease_raw.lower()

        if is_healthy:
            entry = {
                "class_id": c_id,
                "crop": crop,
                "disease_name": f"Healthy {crop}",
                "scientific_name": f"{crop} (Cultivated)",
                "disease_type": "healthy",
                "summary": f"The {crop} foliage appears vibrant, robust, and free of macroscopic pathogenic lesions or pest infestations.",
                "symptoms": [
                    "Normal uniform green coloration across leaves.",
                    "No visible necrotic spots, chlorosis, wilting, or fungal sporulation.",
                    "Turgid leaf structure and normal growth vigor."
                ],
                "causes_and_spread": [
                    "Optimal crop nutrition, good cultural hygiene, and favorable microclimatic balance maintain this condition.",
                    "Not applicable; healthy tissues carry no contagious pathogen load."
                ],
                "treatment_by_severity": {
                    "Low": {
                        "immediate_actions": [
                            "Continue standard cultural practices and scheduled drip/furrow irrigation.",
                            "Inspect lower canopy weekly for any early pest or fungal signs."
                        ],
                        "organic_options": [
                            "Apply routine compost tea or foliar sea-kelp extract to boost natural plant immunity.",
                            "Maintain mulching around root zones to conserve soil moisture and microbial flora."
                        ],
                        "chemical_options": []
                    },
                    "Medium": {
                        "immediate_actions": [
                            "Maintain balanced macro and micronutrient fertigation.",
                            "Ensure good air drainage through proper pruning and weed suppression."
                        ],
                        "organic_options": [
                            "Beneficial mycorrhizal root inoculation to support nutrient uptake."
                        ],
                        "chemical_options": []
                    },
                    "High": {
                        "immediate_actions": [
                            "No curative chemical intervention required. Continue standard preventative scouting."
                        ],
                        "organic_options": [
                            "Maintain healthy organic matter in topsoil."
                        ],
                        "chemical_options": []
                    }
                },
                "fertilizer_and_nutrition": [
                    f"Maintain soil-tested balanced N-P-K tailored to {crop} growth stage.",
                    "Avoid excessive synthetic nitrogen applications which can induce soft, pathogen-vulnerable vegetative flushes.",
                    "Ensure adequate calcium, potassium, and magnesium for reinforced cell wall structure."
                ],
                "precautions_and_prevention": [
                    "Sanitize pruning shears between plants with 70% isopropyl alcohol or bleach solution.",
                    "Water at the base using drip lines to avoid prolonged leaf wetness.",
                    "Maintain recommended plant spacing for optimal sunlight penetration and airflow."
                ],
                "recovery_outlook": "Excellent. The crop is in prime condition. Continue routine preventative monitoring.",
                "when_to_consult_expert": "Consult your local agricultural extension officer if you observe unexplained yellowing, stunting, or blossom drop as weather shifts.",
                "faq": [
                    {
                        "q": f"Does my {crop} have any disease?",
                        "a": f"No, your {crop} shows no signs of disease. The foliage is healthy and vigorous.",
                        "keywords": ["disease", "healthy", "sick", "problem", "issue", "safe"]
                    },
                    {
                        "q": "Should I spray any pesticide or fungicide now?",
                        "a": "No chemical spray is needed for healthy foliage. Excessive prophylactic chemical spraying wastes money and may harm beneficial predator insects.",
                        "keywords": ["spray", "chemical", "pesticide", "fungicide", "medicine"]
                    },
                    {
                        "q": "How can I keep my crop healthy?",
                        "a": "Follow regular drip irrigation, balanced soil nutrition based on soil tests, weed clearance, and scout weekly for pests.",
                        "keywords": ["keep", "care", "prevent", "maintain", "healthy", "tips"]
                    }
                ],
                "verified": False,
                "source_notes": f"Standard agronomical management practices for {crop} (ICAR / FAO / State University Extension Guidelines)."
            }
        else:
            # Diseased class: customize scientific name, disease type, and active ingredients
            disease_type = "fungal"
            sci_name = f"{crop} pathogen"
            
            # Identify disease type & specifics
            d_lower = disease_raw.lower()
            if "bacterial" in d_lower or "greening" in d_lower:
                disease_type = "bacterial"
            elif "virus" in d_lower:
                disease_type = "viral"
            elif "mite" in d_lower:
                disease_type = "pest"
            else:
                disease_type = "fungal"

            # Crop-specific pathogen botanical mapping
            if "apple_scab" in d_lower:
                sci_name = "Venturia inaequalis"
            elif "black_rot" in d_lower and "grape" in crop_raw.lower():
                sci_name = "Guignardia bidwellii"
            elif "black_rot" in d_lower and "apple" in crop_raw.lower():
                sci_name = "Botryosphaeria obtusa"
            elif "cedar_apple_rust" in d_lower:
                sci_name = "Gymnosporangium juniperi-virginianae"
            elif "powdery_mildew" in d_lower:
                sci_name = "Podosphaera / Erysiphe species"
            elif "gray_leaf_spot" in d_lower:
                sci_name = "Cercospora zeae-maydis"
            elif "common_rust" in d_lower:
                sci_name = "Puccinia sorghi"
            elif "northern_leaf_blight" in d_lower:
                sci_name = "Exserohilum turcicum"
            elif "esca" in d_lower:
                sci_name = "Phaeomoniella chlamydospora complex"
            elif "citrus_greening" in d_lower or "haunglongbing" in d_lower:
                sci_name = "Candidatus Liberibacter asiaticus"
            elif "early_blight" in d_lower:
                sci_name = "Alternaria solani"
            elif "late_blight" in d_lower:
                sci_name = "Phytophthora infestans"
            elif "leaf_mold" in d_lower:
                sci_name = "Passalora fulva"
            elif "septoria" in d_lower:
                sci_name = "Septoria lycopersici"
            elif "spider_mite" in d_lower:
                sci_name = "Tetranychus urticae"
            elif "target_spot" in d_lower:
                sci_name = "Corynespora cassiicola"
            elif "yellow_leaf_curl" in d_lower:
                sci_name = "Tomato yellow leaf curl begomovirus"
            elif "mosaic_virus" in d_lower:
                sci_name = "Tomato mosaic tobamovirus"
            elif "leaf_scorch" in d_lower:
                sci_name = "Diplocarpon earlianum"
            elif "bacterial_spot" in d_lower:
                sci_name = "Xanthomonas species"

            # Curate IPM plans
            if disease_type == "fungal":
                chem_low = [
                    {
                        "active_ingredient": "Copper hydroxide or Copper oxychloride",
                        "note": "Preventative broad-spectrum contact fungicide to protect uninfected leaves. Consult local label for pre-harvest interval.",
                        "caution": "Wear full protective eye and respiratory gear. Toxic to aquatic organisms; maintain buffer distance from waterways."
                    }
                ]
                chem_med = [
                    {
                        "active_ingredient": "Azoxystrobin or Chlorothalonil",
                        "note": "Broad-spectrum contact and translaminar action to halt lesion expansion. Rotate chemical modes of action (FRAC codes) to avoid resistance.",
                        "caution": "Observe mandatory pre-harvest interval (PHI) printed on packaging. Keep honeybees and livestock away during application."
                    },
                    {
                        "active_ingredient": "Mancozeb or Difenoconazole",
                        "note": "Curative and protective systemic fungicide for expanding spots.",
                        "caution": "Never apply in windy conditions or immediately prior to rainfall. Wear protective chemical-resistant gloves and respirator."
                    }
                ]
                chem_high = [
                    {
                        "active_ingredient": "Metalaxyl-M + Mancozeb or Trifloxystrobin + Tebuconazole",
                        "note": "Dual-action systemic fungicide formulated for severe epidemic suppression.",
                        "caution": "Follow exact container label guidelines and state agricultural department directives. Observe strict re-entry intervals (REI)."
                    }
                ]
                organic_low = [
                    "Foliar spray of cold-pressed neem oil (azadirachtin) or potassium bicarbonate.",
                    "Spray beneficial bio-fungicide like Bacillus subtilis or Trichoderma viride to colonize leaf surface."
                ]
                organic_med = [
                    "Apply certified copper octanoate (copper soap) or sulfur-based organic formulation.",
                    "Prune severely spotted lower leaves and burn or deeply bury debris away from field."
                ]
                organic_high = [
                    "Immediate sanitary pruning of heavily infected branches.",
                    "Foliar bio-agent spray combination (Bacillus amyloliquefaciens) combined with copper-based organic protectant."
                ]
            elif disease_type == "bacterial":
                chem_low = [
                    {
                        "active_ingredient": "Fixed copper compounds (Copper hydroxide)",
                        "note": "Bactericide protectant to decrease surface bacterial populations before wet weather.",
                        "caution": "Do not mix with acidic foliar sprays; risk of phytotoxicity on young foliage. Wear gloves and mask."
                    }
                ]
                chem_med = [
                    {
                        "active_ingredient": "Copper hydroxide mixed with Mancozeb",
                        "note": "Synergistic tank mixture commonly recommended by university extensions to overcome copper-tolerant bacterial strains.",
                        "caution": "Observe strict Pre-Harvest Interval (PHI). Wear protective overalls and eye protection."
                    }
                ]
                chem_high = [
                    {
                        "active_ingredient": "Streptomycin sulfate or Kasugamycin (where permitted by national regulation)",
                        "note": "Agricultural antibiotic for emergency suppression of systemic bacterial blight.",
                        "caution": "Restricted use strictly under agricultural officer supervision. Observe local pesticide laws and maximum residue limits (MRL)."
                    }
                ]
                organic_low = [
                    "Foliar application of Bacillus subtilis or Pseudomonas fluorescens antagonistic bacteria.",
                    "Ensure overhead irrigation is immediately halted to stop splashing bacterial cells."
                ]
                organic_med = [
                    "Spray approved organic fixed copper bactericide.",
                    "Drench soil with compost bio-extract enriched with antagonistic Trichoderma."
                ]
                organic_high = [
                    "Remove and destroy severely blighted plants to preserve adjacent crops.",
                    "Solarize affected soil beds and disinfect all farm tools with 10% sodium hypochlorite."
                ]
            elif disease_type == "viral":
                chem_low = [
                    {
                        "active_ingredient": "No chemical cures plant viruses directly. Target vector insects.",
                        "note": "Focus chemical control solely on sap-sucking vectors (whiteflies, aphids, thrips).",
                        "caution": "Do not spray broad-spectrum chemicals indiscriminately; protect beneficial pollinating bees."
                    }
                ]
                chem_med = [
                    {
                        "active_ingredient": "Acetamiprid or Thiamethoxam",
                        "note": "Systemic insecticide targeting virus-vectoring sucking pests on foliage.",
                        "caution": "Hazardous to bees: never spray during active morning bloom hours. Wear personal protective equipment."
                    }
                ]
                chem_high = [
                    {
                        "active_ingredient": "Pyriproxyfen or Spiromesifen",
                        "note": "Insect growth regulator targeting vector nymphs and whitefly populations.",
                        "caution": "Follow label safety buffer guidelines near open water sources."
                    }
                ]
                organic_low = [
                    "Install yellow or blue sticky traps (10-15 per acre) to monitor and trap winged vector insects.",
                    "Spray cold-pressed neem seed kernel extract (NSKE 5%) or horticultural mineral oil."
                ]
                organic_med = [
                    "Foliar spray of entomopathogenic fungus Beauveria bassiana or Verticillium lecanii.",
                    "Erect 40-mesh insect-proof netting around nursery beds or greenhouse entries."
                ]
                organic_high = [
                    "Rogue (uproot) and destroy all plants showing severe viral mosaic, stunting, or leaf curl immediately.",
                    "Keep field free of solanaceous and asteraceous weed hosts within a 30-meter perimeter."
                ]
            else: # pest (mites)
                chem_low = [
                    {
                        "active_ingredient": "Wettable Sulfur",
                        "note": "Miticidal contact spray effective against two-spotted spider mites.",
                        "caution": "Do not apply if ambient temperature exceeds 32°C (90°F) or within 2 weeks of oil sprays to prevent foliar burn."
                    }
                ]
                chem_med = [
                    {
                        "active_ingredient": "Abamectin or Spiromesifen",
                        "note": "Translaminar miticide specifically targeting mite larvae and adult feeding stages.",
                        "caution": "High toxicity to bees; spray in late evening when bees are not foraging. Observe PHI."
                    }
                ]
                chem_high = [
                    {
                        "active_ingredient": "Bifenazate or Hexythiazox",
                        "note": "Targeted acaricide with ovicidal and long residual knockdown activity against resistant populations.",
                        "caution": "Rotate FRAC/IRAC groups to prevent rapid mite resistance development."
                    }
                ]
                organic_low = [
                    "High-pressure water jet spray to under-surface of foliage to physically dislodge mite colonies.",
                    "Release predatory phytoseiid mites (e.g. Phytoseiulus persimilis or Neoseiulus californicus)."
                ]
                organic_med = [
                    "Spray botanical azadirachtin or potassium salts of fatty acids (insecticidal soap).",
                    "Dust sulfur or apply horticultural dormant/summer oil ensuring complete lower leaf coverage."
                ]
                organic_high = [
                    "Prune severely webbed leaves and safely burn them.",
                    "Combine insecticidal soap with predatory mite releases and moisture regulation."
                ]

            entry = {
                "class_id": c_id,
                "crop": crop,
                "disease_name": disease_clean,
                "scientific_name": sci_name,
                "disease_type": disease_type,
                "summary": f"{disease_clean} is a prominent {disease_type} disease impacting {crop}. It attacks foliage, stems, or fruits, leading to photosynthetic disruption, yield reduction, and crop damage if unmanaged.",
                "symptoms": [
                    f"Noticeable lesions and discoloration visible on {crop} foliage.",
                    "Chlorotic yellow halos surrounding expanding brownish necrotic spots or spots with concentric rings.",
                    "Premature defoliation, blighted leaf tissue, or stunting in advanced stages."
                ],
                "causes_and_spread": [
                    f"Pathogen ({sci_name}) favored by high relative humidity, poor canopy airflow, and free moisture on foliage.",
                    "Disseminated by wind-blown spores, water splashing from overhead irrigation or rain, and contaminated farm tools.",
                    "Can overwinter on unharvested infected crop residue or alternate weed hosts."
                ],
                "treatment_by_severity": {
                    "Low": {
                        "immediate_actions": [
                            "Carefully hand-prune isolated symptomatic leaves and safely discard away from the field.",
                            "Switch overhead irrigation to ground drip lines to keep foliage completely dry.",
                            "Improve plant ventilation by staking and clearing ground weeds."
                        ],
                        "organic_options": organic_low,
                        "chemical_options": chem_low
                    },
                    "Medium": {
                        "immediate_actions": [
                            "Prune infected foliage using disinfected shears (sterilize in 70% alcohol between cuts).",
                            "Isolate severely affected rows and restrict farm equipment movement to prevent mechanical transmission.",
                            "Initiate targeted protective spray according to local agricultural extension schedules."
                        ],
                        "organic_options": organic_med,
                        "chemical_options": chem_med
                    },
                    "High": {
                        "immediate_actions": [
                            "Uproot non-recoverable diseased crop sections to stop epidemic outbreak across neighboring plots.",
                            "Halt all overhead spraying and high-nitrogen fertilizers immediately.",
                            "Apply emergency curative treatment under advice of your district agricultural extension officer."
                        ],
                        "organic_options": organic_high,
                        "chemical_options": chem_high
                    }
                },
                "fertilizer_and_nutrition": [
                    "Avoid excessive synthetic nitrogen; soft flushes are highly susceptible to pathogens.",
                    "Supplement with potassium (potash) and soluble silica to thicken leaf epidermal cell walls.",
                    "Apply calcium and boron foliar sprays during early growth to strengthen plant tissue resilience."
                ],
                "precautions_and_prevention": [
                    "Practice 2-3 year crop rotation with non-host botanical families.",
                    "Source certified pathogen-free seeds and disease-resistant crop cultivars.",
                    "Destroy and incorporate or burn all post-harvest crop stubble to eliminate overwintering inoculum.",
                    "Always wear protective clothing, mask, and chemical-resistant gloves when handling any agricultural compounds.",
                    "Respect the Pre-Harvest Interval (PHI) indicated on manufacturer product labels."
                ],
                "recovery_outlook": "Moderate to good if managed at Low to Medium severity. At High severity, focus on protecting healthy new flushes and neighboring crops.",
                "when_to_consult_expert": "Consult your local Krishi Vigyan Kendra (KVK) or university agricultural extension officer if lesions cover more than 30% of the field canopy or if symptoms fail to respond after initial treatment.",
                "faq": [
                    {
                        "q": f"What disease does my {crop} have?",
                        "a": f"The model detected {disease_clean} ({sci_name}), a {disease_type} disease common in {crop}.",
                        "keywords": ["what", "identify", "disease", "name", "problem", "diagnosis"]
                    },
                    {
                        "q": "How do I treat this disease?",
                        "a": "Start with Integrated Pest Management: remove infected leaves, stop overhead watering, and apply recommended organic bio-fungicides or label-directed chemical protectants based on severity level.",
                        "keywords": ["treatment", "cure", "treat", "control", "manage", "fix", "spray"]
                    },
                    {
                        "q": "What organic options can I use?",
                        "a": f"You can apply cold-pressed neem oil (azadirachtin), antagonistic bio-control agents like Bacillus subtilis or Trichoderma, and practice prompt sanitary pruning.",
                        "keywords": ["organic", "natural", "home", "neem", "biological", "herbal"]
                    },
                    {
                        "q": "Will this disease spread to other plants?",
                        "a": "Yes, spores and bacteria spread rapidly via rain splashes, wind currents, and contaminated hands or shears. Prune infected parts and disinfect tools to prevent spreading.",
                        "keywords": ["spread", "contagious", "neighbor", "other", "plants", "field"]
                    },
                    {
                        "q": "Is it safe to harvest and consume the crop?",
                        "a": "Unblemished fruits and produce are generally safe after thorough washing. If any chemical protectants were sprayed, strictly obey the label's Pre-Harvest Interval (PHI) before picking.",
                        "keywords": ["harvest", "eat", "safe", "consumption", "food", "market"]
                    },
                    {
                        "q": "How long will recovery take?",
                        "a": "Infected leaves cannot heal, but new healthy leaves should emerge within 10 to 14 days under proper IPM treatment and dry foliage conditions.",
                        "keywords": ["recovery", "time", "how long", "recover", "days", "heal"]
                    }
                ],
                "verified": False,
                "source_notes": f"Integrated Pest Management Guidelines for {crop} diseases (USDA / ICAR / University Agricultural Extension services)."
            }

        kb_data[c_id] = entry

    # Save to knowledge/diseases.json
    out_file = Path("knowledge/diseases.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(kb_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated Knowledge Base for {len(kb_data)} classes at {out_file.resolve()}")
    return kb_data


if __name__ == "__main__":
    build_knowledge_base()
