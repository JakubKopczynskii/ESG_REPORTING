"""
ESG Framework Definitions
Covers key SASB and GRI disclosure requirements used by the Materiality Agent.
"""

# ─── SASB Topic Categories (cross-industry + sector-specific) ────────────────
SASB_GENERAL_TOPICS = {
    "GHG_EMISSIONS": {
        "id": "IF-EU-110a",
        "name": "Greenhouse Gas Emissions",
        "keywords": ["scope 1", "scope 2", "scope 3", "ghg", "co2", "methane", "carbon", "emissions"],
        "required_disclosures": [
            "Gross global Scope 1 emissions (metric tons CO2-e)",
            "Percentage covered under emissions-limiting regulations",
            "Gross global Scope 2 emissions",
            "Discussion of long-term strategy / targets for reducing emissions",
        ],
    },
    "ENERGY_MANAGEMENT": {
        "id": "IF-EU-120a",
        "name": "Energy Management",
        "keywords": ["energy consumption", "renewable energy", "energy intensity", "kwh", "mwh"],
        "required_disclosures": [
            "Total energy consumed",
            "Percentage renewable energy",
            "Energy intensity",
        ],
    },
    "WATER_MANAGEMENT": {
        "id": "IF-EU-140a",
        "name": "Water & Wastewater Management",
        "keywords": ["water withdrawal", "water consumption", "wastewater", "water stress"],
        "required_disclosures": [
            "Total water withdrawn",
            "Total water consumed",
            "Water withdrawn in high baseline water stress regions",
        ],
    },
    "WASTE_HAZARDOUS": {
        "id": "RT-CH-150a",
        "name": "Waste & Hazardous Materials Management",
        "keywords": ["waste", "hazardous", "recycling", "landfill", "disposal"],
        "required_disclosures": [
            "Amount of hazardous waste generated",
            "Amount of hazardous waste recycled",
            "Number of reportable spills",
        ],
    },
    "BIODIVERSITY": {
        "id": "EM-MM-160a",
        "name": "Biodiversity Impacts",
        "keywords": ["biodiversity", "deforestation", "habitat", "land use", "ecosystem"],
        "required_disclosures": [
            "Operations in or near biodiversity-sensitive areas",
            "Percentage of land restored or rehabilitated",
        ],
    },
    "LABOR_PRACTICES": {
        "id": "SV-PS-310a",
        "name": "Labor Practices",
        "keywords": ["employee", "labor", "workforce", "turnover", "safety", "injury", "fatality"],
        "required_disclosures": [
            "Total recordable incident rate (TRIR)",
            "Fatality rate",
            "Employee turnover rate",
            "Percentage of employees covered by collective bargaining",
        ],
    },
    "SUPPLY_CHAIN": {
        "id": "CG-MR-430a",
        "name": "Supply Chain Management",
        "keywords": ["supply chain", "supplier", "sourcing", "procurement", "conflict minerals"],
        "required_disclosures": [
            "Percentage of Tier 1 suppliers audited to ESG criteria",
            "Percentage of materials sourced from certified sources",
            "Discussion of supply chain transparency",
        ],
    },
    "BUSINESS_ETHICS": {
        "id": "SV-PS-510a",
        "name": "Business Ethics & Transparency",
        "keywords": ["ethics", "corruption", "bribery", "compliance", "whistleblower", "fines"],
        "required_disclosures": [
            "Total amount of monetary losses from legal proceedings",
            "Description of policies and practices for prevention of bribery",
        ],
    },
    "BOARD_DIVERSITY": {
        "id": "CN-TE-330a",
        "name": "Board Diversity & Governance",
        "keywords": ["board", "diversity", "governance", "independent directors", "ESG committee"],
        "required_disclosures": [
            "Percentage of gender diversity on board",
            "Percentage of independent directors",
            "ESG oversight structure",
        ],
    },
    "CLIMATE_RISK": {
        "id": "FN-IN-450a",
        "name": "Physical and Transition Climate Risk",
        "keywords": ["climate risk", "tcfd", "physical risk", "transition risk", "scenario analysis"],
        "required_disclosures": [
            "TCFD-aligned scenario analysis",
            "Financial exposure to physical climate risks",
            "Transition risk exposure",
        ],
    },
}

# ─── GRI Standards Index ─────────────────────────────────────────────────────
GRI_STANDARDS = {
    "GRI_2_GENERAL": {
        "standard": "GRI 2: General Disclosures 2021",
        "disclosures": {
            "2-1": "Organizational details",
            "2-2": "Entities included in sustainability reporting",
            "2-5": "External assurance",
            "2-6": "Activities, value chain and other relationships",
            "2-9": "Governance structure and composition",
            "2-22": "Statement on sustainable development strategy",
            "2-29": "Approach to stakeholder engagement",
            "2-30": "Collective bargaining agreements",
        },
    },
    "GRI_3_MATERIAL": {
        "standard": "GRI 3: Material Topics 2021",
        "disclosures": {
            "3-1": "Process to determine material topics",
            "3-2": "List of material topics",
            "3-3": "Management of material topics",
        },
    },
    "GRI_305_EMISSIONS": {
        "standard": "GRI 305: Emissions 2016",
        "disclosures": {
            "305-1": "Direct (Scope 1) GHG emissions",
            "305-2": "Energy indirect (Scope 2) GHG emissions",
            "305-3": "Other indirect (Scope 3) GHG emissions",
            "305-4": "GHG emissions intensity",
            "305-5": "Reduction of GHG emissions",
        },
    },
    "GRI_302_ENERGY": {
        "standard": "GRI 302: Energy 2016",
        "disclosures": {
            "302-1": "Energy consumption within the organization",
            "302-2": "Energy consumption outside the organization",
            "302-3": "Energy intensity",
            "302-4": "Reduction of energy consumption",
        },
    },
    "GRI_303_WATER": {
        "standard": "GRI 303: Water and Effluents 2018",
        "disclosures": {
            "303-1": "Interactions with water as a shared resource",
            "303-3": "Water withdrawal",
            "303-4": "Water discharge",
            "303-5": "Water consumption",
        },
    },
    "GRI_306_WASTE": {
        "standard": "GRI 306: Waste 2020",
        "disclosures": {
            "306-1": "Waste generation and significant waste-related impacts",
            "306-3": "Waste generated",
            "306-4": "Waste diverted from disposal",
            "306-5": "Waste directed to disposal",
        },
    },
    "GRI_401_EMPLOYMENT": {
        "standard": "GRI 401: Employment 2016",
        "disclosures": {
            "401-1": "New employee hires and employee turnover",
            "401-2": "Benefits provided to full-time employees",
        },
    },
    "GRI_403_SAFETY": {
        "standard": "GRI 403: Occupational Health and Safety 2018",
        "disclosures": {
            "403-1": "Occupational health and safety management system",
            "403-9": "Work-related injuries",
            "403-10": "Work-related ill health",
        },
    },
    "GRI_408_CHILD_LABOR": {
        "standard": "GRI 408: Child Labor 2016",
        "disclosures": {
            "408-1": "Operations and suppliers at significant risk for incidents of child labor",
        },
    },
    "GRI_409_FORCED_LABOR": {
        "standard": "GRI 409: Forced or Compulsory Labor 2016",
        "disclosures": {
            "409-1": "Operations and suppliers at significant risk for incidents of forced or compulsory labor",
        },
    },
}

# ─── Scoring weights per category ────────────────────────────────────────────
MATERIALITY_WEIGHTS = {
    "GHG_EMISSIONS": 0.20,
    "ENERGY_MANAGEMENT": 0.10,
    "WATER_MANAGEMENT": 0.08,
    "WASTE_HAZARDOUS": 0.07,
    "BIODIVERSITY": 0.08,
    "LABOR_PRACTICES": 0.12,
    "SUPPLY_CHAIN": 0.10,
    "BUSINESS_ETHICS": 0.10,
    "BOARD_DIVERSITY": 0.07,
    "CLIMATE_RISK": 0.08,
}

def get_all_keywords() -> list[str]:
    """Flatten all SASB keyword lists for quick text scanning."""
    kw = []
    for topic in SASB_GENERAL_TOPICS.values():
        kw.extend(topic["keywords"])
    return list(set(kw))