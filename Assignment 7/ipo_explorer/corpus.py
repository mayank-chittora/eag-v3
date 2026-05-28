"""IPO corpus — 60 Indian IPOs from 2020-2024.

Each record carries deliberate semantic keywords in `description` so that
vector search works even when crawled web pages return sparse content.
Fintech records use "UPI", "payment gateway", "digital transactions".
Rural-focus records use "Bharat", "tier-2", "kirana", "semi-urban".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IPORecord:
    symbol: str
    company: str
    sector: str
    ipo_date: str        # YYYY-MM-DD
    issue_price: float
    listing_price: float
    website_url: str
    wikipedia_url: str
    description: str     # rich semantic keywords for reliable vector recall


CORPUS: list[IPORecord] = [
    # ── Fintech / Digital Payments ───────────────────────────────────────
    IPORecord(
        symbol="PAYTM",
        company="One 97 Communications (Paytm)",
        sector="Fintech",
        ipo_date="2021-11-18",
        issue_price=2150.0,
        listing_price=1955.0,
        website_url="https://paytm.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Paytm",
        description=(
            "Paytm is India's largest digital payments and financial services platform. "
            "It enables UPI transactions, mobile wallet payments, payment gateway for merchants, "
            "buy-now-pay-later lending, and wealth management services for millions of users."
        ),
    ),
    IPORecord(
        symbol="POLICYBZR",
        company="PB Fintech (Policybazaar)",
        sector="Fintech",
        ipo_date="2021-11-15",
        issue_price=980.0,
        listing_price=1150.0,
        website_url="https://www.policybazaar.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Policybazaar",
        description=(
            "Policybazaar is India's largest online insurance aggregator and digital financial "
            "services marketplace. It allows users to compare and buy health insurance, life "
            "insurance, motor insurance, and investment products online through its digital platform."
        ),
    ),
    IPORecord(
        symbol="FINOPB",
        company="Fino Payments Bank",
        sector="Fintech",
        ipo_date="2021-10-29",
        issue_price=577.0,
        listing_price=548.0,
        website_url="https://www.finobank.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Fino_Payments_Bank",
        description=(
            "Fino Payments Bank is a digital banking platform focused on financial inclusion "
            "for unbanked and underbanked populations in rural India, Bharat, and tier-2 and "
            "tier-3 cities. It operates through a network of micro-ATMs, business correspondents, "
            "and merchant banking points serving kirana stores and semi-urban communities."
        ),
    ),
    IPORecord(
        symbol="RATEGAIN",
        company="RateGain Travel Technologies",
        sector="SaaS / Travel Tech",
        ipo_date="2021-12-17",
        issue_price=425.0,
        listing_price=392.0,
        website_url="https://rategain.com",
        wikipedia_url="https://en.wikipedia.org/wiki/RateGain",
        description=(
            "RateGain is a SaaS technology company providing revenue management, distribution, "
            "and digital marketing solutions to the global travel and hospitality industry. "
            "Its products help hotels, airlines, OTAs, and car rentals optimize pricing using "
            "artificial intelligence and machine learning algorithms."
        ),
    ),
    IPORecord(
        symbol="LATENTVIEW",
        company="Latent View Analytics",
        sector="Data Analytics",
        ipo_date="2021-11-23",
        issue_price=197.0,
        listing_price=530.0,
        website_url="https://www.latentview.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Latent_View_Analytics",
        description=(
            "Latent View Analytics is a pure-play data analytics company that provides business "
            "intelligence, advanced analytics, and data engineering services to Fortune 500 clients. "
            "It uses machine learning models, AI-driven insights, and cloud data platforms to help "
            "enterprises make data-driven decisions."
        ),
    ),
    # ── E-Commerce / Consumer Internet ───────────────────────────────────
    IPORecord(
        symbol="ZOMATO",
        company="Zomato",
        sector="Food Tech",
        ipo_date="2021-07-23",
        issue_price=76.0,
        listing_price=116.0,
        website_url="https://www.zomato.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Zomato",
        description=(
            "Zomato is India's leading food delivery platform connecting restaurants and customers "
            "through its mobile app and website. It operates Blinkit quick commerce for 10-minute "
            "grocery delivery, restaurant discovery, dining-out services, and Hyperpure B2B fresh "
            "ingredient supply to restaurants across India."
        ),
    ),
    IPORecord(
        symbol="NYKAA",
        company="FSN E-Commerce Ventures (Nykaa)",
        sector="Beauty E-Commerce",
        ipo_date="2021-11-10",
        issue_price=1125.0,
        listing_price=2018.0,
        website_url="https://www.nykaa.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Nykaa",
        description=(
            "Nykaa is India's leading omni-channel beauty and personal care e-commerce platform "
            "for women. It sells cosmetics, skincare, haircare, and fashion products through its "
            "app, website, and physical retail stores across India. NykaaFashion extends the "
            "platform to apparel and accessories for urban women."
        ),
    ),
    IPORecord(
        symbol="CARTRADE",
        company="CarTrade Tech",
        sector="Automotive Marketplace",
        ipo_date="2021-08-20",
        issue_price=1618.0,
        listing_price=1600.0,
        website_url="https://www.cartrade.com",
        wikipedia_url="https://en.wikipedia.org/wiki/CarTrade",
        description=(
            "CarTrade is India's largest multi-channel online automotive platform for buying and "
            "selling new and used vehicles. It operates CarTrade, CarWale, BikeWale, and Shriram "
            "Automall marketplaces serving consumers, dealers, and OEMs with vehicle auctions, "
            "inspections, and financial services."
        ),
    ),
    # ── Logistics / Supply Chain ──────────────────────────────────────────
    IPORecord(
        symbol="DELHIVERY",
        company="Delhivery",
        sector="Logistics",
        ipo_date="2022-05-24",
        issue_price=487.0,
        listing_price=493.0,
        website_url="https://www.delhivery.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Delhivery",
        description=(
            "Delhivery is India's largest fully-integrated logistics and supply chain services "
            "company. It provides express parcel delivery, freight services, cross-border shipping, "
            "warehousing, and supply chain management to e-commerce companies and enterprises "
            "across tier-1, tier-2, and tier-3 cities and semi-urban areas of India."
        ),
    ),
    IPORecord(
        symbol="ECOM",
        company="Ecom Express",
        sector="Logistics",
        ipo_date="2024-02-05",
        issue_price=200.0,
        listing_price=247.0,
        website_url="https://www.ecomexpress.in",
        wikipedia_url="https://en.wikipedia.org/wiki/Ecom_Express",
        description=(
            "Ecom Express is a technology-enabled end-to-end logistics solutions company providing "
            "express delivery services to e-commerce companies across India including tier-2, "
            "tier-3 cities and rural Bharat. It specializes in cash-on-delivery handling, "
            "reverse logistics, and last-mile delivery for online retailers."
        ),
    ),
    # ── Healthcare / Pharma ───────────────────────────────────────────────
    IPORecord(
        symbol="MEDPLUS",
        company="MedPlus Health Services",
        sector="Healthcare / Pharmacy",
        ipo_date="2021-12-13",
        issue_price=796.0,
        listing_price=1008.0,
        website_url="https://www.medplusmart.com",
        wikipedia_url="https://en.wikipedia.org/wiki/MedPlus",
        description=(
            "MedPlus is one of India's largest pharmacy retail chains operating in southern and "
            "eastern India, with a strong presence in tier-2 and tier-3 cities and semi-urban "
            "communities. It sells prescription medicines, over-the-counter drugs, wellness "
            "products, and diagnostic services through its retail pharmacies and online platform."
        ),
    ),
    IPORecord(
        symbol="VIJAYA",
        company="Vijaya Diagnostic Centre",
        sector="Healthcare / Diagnostics",
        ipo_date="2021-09-14",
        issue_price=531.0,
        listing_price=531.0,
        website_url="https://www.vijayadiagnostic.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Vijaya_Diagnostic_Centre",
        description=(
            "Vijaya Diagnostic Centre is a leading diagnostics company operating pathology labs "
            "and radiology centres across Andhra Pradesh and Telangana. It provides affordable "
            "diagnostic testing services including blood tests, imaging, and health check packages "
            "to patients in urban, semi-urban, and tier-2 areas."
        ),
    ),
    IPORecord(
        symbol="SUPRIYA",
        company="Supriya Lifescience",
        sector="Pharmaceuticals",
        ipo_date="2021-12-16",
        issue_price=274.0,
        listing_price=430.0,
        website_url="https://supriyalifescience.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Supriya_Lifescience",
        description=(
            "Supriya Lifescience is an Indian pharmaceutical company that manufactures active "
            "pharmaceutical ingredients (APIs) and speciality chemicals for export to global "
            "markets. It focuses on research-driven manufacturing of antihistamines, analgesics, "
            "and vitamin compounds."
        ),
    ),
    # ── BFSI ─────────────────────────────────────────────────────────────
    IPORecord(
        symbol="LICI",
        company="Life Insurance Corporation of India (LIC)",
        sector="Insurance / BFSI",
        ipo_date="2022-05-17",
        issue_price=949.0,
        listing_price=875.0,
        website_url="https://licindia.in",
        wikipedia_url="https://en.wikipedia.org/wiki/Life_Insurance_Corporation_of_India",
        description=(
            "Life Insurance Corporation of India (LIC) is the largest state-owned insurance "
            "company and institutional investor in India. It provides life insurance, pension, "
            "and investment products to millions of policyholders across all states including "
            "rural India, Bharat, tier-2 and tier-3 cities through its vast agent network."
        ),
    ),
    IPORecord(
        symbol="SBICARDS",
        company="SBI Cards and Payment Services",
        sector="Fintech / BFSI",
        ipo_date="2020-03-16",
        issue_price=755.0,
        listing_price=658.0,
        website_url="https://www.sbicard.com",
        wikipedia_url="https://en.wikipedia.org/wiki/SBI_Card",
        description=(
            "SBI Cards is India's second-largest credit card issuer, offering a range of credit "
            "cards with rewards, cashback, and travel benefits. It is a joint venture between "
            "SBI and The Carlyle Group, providing digital payment solutions including UPI-linked "
            "credit cards, contactless payments, and EMI-based consumer financing."
        ),
    ),
    IPORecord(
        symbol="EASEMYTRIP",
        company="Easy Trip Planners (EaseMyTrip)",
        sector="Travel Tech",
        ipo_date="2021-03-08",
        issue_price=187.0,
        listing_price=206.0,
        website_url="https://www.easemytrip.com",
        wikipedia_url="https://en.wikipedia.org/wiki/EaseMyTrip",
        description=(
            "EaseMyTrip is India's second-largest online travel aggregator for booking flights, "
            "hotels, holiday packages, and bus tickets. It targets tier-2 and tier-3 cities and "
            "semi-urban travellers in India by offering no-convenience-fee bookings, Hindi-language "
            "support, and affordable travel options for the Bharat market."
        ),
    ),
    # ── Technology / SaaS ─────────────────────────────────────────────────
    IPORecord(
        symbol="MAPMYINDIA",
        company="C.E. Info Systems (MapmyIndia)",
        sector="Mapping / Technology",
        ipo_date="2021-12-21",
        issue_price=1033.0,
        listing_price=1581.0,
        website_url="https://www.mapmyindia.com",
        wikipedia_url="https://en.wikipedia.org/wiki/MapmyIndia",
        description=(
            "MapmyIndia is India's leading digital maps, geospatial data, and location-based "
            "technology company. It provides mapping APIs, navigation software, IoT fleet "
            "management, and location intelligence solutions to automotive OEMs, enterprises, "
            "and government agencies using artificial intelligence and machine learning."
        ),
    ),
    IPORecord(
        symbol="TARSONS",
        company="Tarsons Products",
        sector="Lab Supplies / Technology",
        ipo_date="2021-11-24",
        issue_price=662.0,
        listing_price=702.0,
        website_url="https://www.tarsons.in",
        wikipedia_url="https://en.wikipedia.org/wiki/Tarsons_Products",
        description=(
            "Tarsons Products is India's leading manufacturer of laboratory plastic ware used in "
            "life sciences research, diagnostics, and healthcare. It exports scientific instruments "
            "and consumables to research labs, hospitals, and pharmaceutical companies globally."
        ),
    ),
    IPORecord(
        symbol="KRSNAA",
        company="Krsnaa Diagnostics",
        sector="Healthcare Tech",
        ipo_date="2021-08-19",
        issue_price=954.0,
        listing_price=909.0,
        website_url="https://www.krsnaa.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Krsnaa_Diagnostics",
        description=(
            "Krsnaa Diagnostics is a technology-enabled diagnostics company that operates "
            "radiology and pathology centres in government hospitals across rural India, "
            "Bharat, tier-2 and tier-3 cities. It provides affordable diagnostic services "
            "to underserved communities through public-private partnership models."
        ),
    ),
    # ── Consumer / FMCG ──────────────────────────────────────────────────
    IPORecord(
        symbol="BIKAJI",
        company="Bikaji Foods International",
        sector="FMCG / Snacks",
        ipo_date="2022-11-03",
        issue_price=300.0,
        listing_price=322.0,
        website_url="https://www.bikaji.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Bikaji_Foods",
        description=(
            "Bikaji Foods is one of India's largest ethnic snack and sweets companies, serving "
            "customers across rural India, Bharat, and tier-2 and tier-3 cities. It manufactures "
            "bhujia, namkeen, rasgulla, soan papdi, and ready-to-eat traditional snacks distributed "
            "through a wide network of kirana stores, general trade retailers, and modern trade."
        ),
    ),
    IPORecord(
        symbol="DEVYANI",
        company="Devyani International",
        sector="QSR / Food",
        ipo_date="2021-08-04",
        issue_price=90.0,
        listing_price=141.0,
        website_url="https://www.devyaniinternational.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Devyani_International",
        description=(
            "Devyani International is the largest franchisee of Yum! Brands in India, operating "
            "KFC, Pizza Hut, and Costa Coffee restaurants. It is expanding into tier-2, tier-3 "
            "cities and semi-urban markets across India to serve the growing aspirational "
            "middle class in smaller Indian cities and Bharat."
        ),
    ),
    IPORecord(
        symbol="SAPPHIRE",
        company="Sapphire Foods India",
        sector="QSR / Food",
        ipo_date="2021-11-09",
        issue_price=1180.0,
        listing_price=1310.0,
        website_url="https://www.sapphirefoods.in",
        wikipedia_url="https://en.wikipedia.org/wiki/Sapphire_Foods_India",
        description=(
            "Sapphire Foods is the largest KFC franchisee in the Indian subcontinent, also "
            "operating Pizza Hut restaurants. It focuses on expanding quick-service restaurant "
            "presence in tier-2 and tier-3 cities across India, Sri Lanka, and the Maldives, "
            "targeting younger urban and semi-urban consumers."
        ),
    ),
    IPORecord(
        symbol="ADANIWILMAR",
        company="Adani Wilmar",
        sector="FMCG / Edible Oils",
        ipo_date="2022-02-08",
        issue_price=230.0,
        listing_price=221.0,
        website_url="https://www.fortunefoods.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Adani_Wilmar",
        description=(
            "Adani Wilmar is one of India's largest FMCG companies, best known for Fortune brand "
            "edible oils including soyabean, sunflower, and mustard oil. It serves rural Bharat, "
            "tier-2 and tier-3 cities through kirana stores and general trade. It also sells "
            "wheat flour, rice, pulses, sugar, and packaged food products."
        ),
    ),
    # ── Infrastructure / Manufacturing ────────────────────────────────────
    IPORecord(
        symbol="CLEAN",
        company="Clean Science and Technology",
        sector="Specialty Chemicals",
        ipo_date="2021-07-19",
        issue_price=900.0,
        listing_price=1784.0,
        website_url="https://www.cleanscience.co.in",
        wikipedia_url="https://en.wikipedia.org/wiki/Clean_Science_and_Technology",
        description=(
            "Clean Science and Technology is a specialty chemicals manufacturer producing "
            "performance chemicals, FMCG chemicals, and pharmaceutical intermediates. Its "
            "products include antioxidants, UV stabilizers, and preservatives used in "
            "personal care, food, and industrial applications globally."
        ),
    ),
    IPORecord(
        symbol="GLAND",
        company="Gland Pharma",
        sector="Pharmaceuticals",
        ipo_date="2020-11-20",
        issue_price=1500.0,
        listing_price=1710.0,
        website_url="https://www.glandpharma.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Gland_Pharma",
        description=(
            "Gland Pharma is a leading injectable-focused global pharmaceutical company. "
            "It develops and manufactures complex injectables, oncology, and ophthalmic "
            "products for regulated markets in USA, Europe, Canada, and Australia. "
            "It is majority-owned by Shanghai Fosun Pharmaceutical Group."
        ),
    ),
    IPORecord(
        symbol="CHEMCON",
        company="Chemcon Speciality Chemicals",
        sector="Specialty Chemicals",
        ipo_date="2020-09-24",
        issue_price=340.0,
        listing_price=731.0,
        website_url="https://www.chemconworld.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Chemcon_Speciality_Chemicals",
        description=(
            "Chemcon Speciality Chemicals is a manufacturer of specialty chemicals used in "
            "oil and gas well cementing, API-grade pharmaceutical intermediates, and "
            "specialty iodine-based contrast media. It exports to global markets including "
            "the US, Europe, and Japan."
        ),
    ),
    # ── Renewable Energy / EV ─────────────────────────────────────────────
    IPORecord(
        symbol="WARDWIZARD",
        company="Wardwizard Innovations & Mobility",
        sector="Electric Vehicles",
        ipo_date="2021-06-09",
        issue_price=35.0,
        listing_price=53.0,
        website_url="https://www.wardwizard.in",
        wikipedia_url="https://en.wikipedia.org/wiki/Wardwizard_Innovations_and_Mobility",
        description=(
            "Wardwizard Innovations is an Indian electric vehicle manufacturer producing "
            "Joy e-bike electric scooters, e-cycles, and electric two-wheelers. It targets "
            "eco-conscious urban commuters, tier-2 and tier-3 city consumers in Bharat, "
            "and last-mile delivery companies seeking green mobility solutions."
        ),
    ),
    IPORecord(
        symbol="GREENPANEL",
        company="Greenpanel Industries",
        sector="Wood Panels / Green Materials",
        ipo_date="2019-09-05",
        issue_price=181.0,
        listing_price=163.0,
        website_url="https://www.greenpanel.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Greenpanel_Industries",
        description=(
            "Greenpanel Industries is India's largest manufacturer of MDF (medium density "
            "fibreboard) wood panels for furniture, interior design, and construction. "
            "It produces eco-friendly, formaldehyde-free wood products sold to dealers, "
            "furniture makers, and retail customers across India."
        ),
    ),
    # ── Retail / Fashion ──────────────────────────────────────────────────
    IPORecord(
        symbol="METRO",
        company="Metro Brands",
        sector="Footwear Retail",
        ipo_date="2021-12-22",
        issue_price=500.0,
        listing_price=430.0,
        website_url="https://www.metrobrands.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Metro_Brands",
        description=(
            "Metro Brands is one of India's largest footwear specialty retailers operating "
            "Metro, Mochi, Walkway, and Da Vinchi branded stores. It sells premium and "
            "mid-market footwear to urban consumers. It is expanding into tier-2 cities "
            "and semi-urban markets to capture the growing aspirational retail segment."
        ),
    ),
    IPORecord(
        symbol="VEDANT",
        company="Vedant Fashions (Manyavar)",
        sector="Ethnic Fashion",
        ipo_date="2022-02-16",
        issue_price=866.0,
        listing_price=1009.0,
        website_url="https://www.manyavar.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Manyavar",
        description=(
            "Vedant Fashions is India's leading designer and retailer of celebration wear "
            "under the Manyavar and Mohey brands. It sells ethnic Indian wedding and festive "
            "clothing for men and women through stores across India including tier-2 and "
            "tier-3 cities, targeting the wedding occasion market in Bharat."
        ),
    ),
    # ── Real Estate / Infra ───────────────────────────────────────────────
    IPORecord(
        symbol="NUVOCO",
        company="Nuvoco Vistas Corporation",
        sector="Cement / Construction",
        ipo_date="2021-08-09",
        issue_price=570.0,
        listing_price=542.0,
        website_url="https://www.nuvoco.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Nuvoco_Vistas",
        description=(
            "Nuvoco Vistas is the fifth-largest cement company in India and the largest in "
            "eastern India by capacity. It produces Portland cement, ready-mix concrete, and "
            "modern building materials for construction projects in housing, infrastructure, "
            "and commercial segments across rural Bharat and urban India."
        ),
    ),
    IPORecord(
        symbol="MACROTECH",
        company="Macrotech Developers (Lodha)",
        sector="Real Estate",
        ipo_date="2021-04-19",
        issue_price=486.0,
        listing_price=422.0,
        website_url="https://www.lodhagroup.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Macrotech_Developers",
        description=(
            "Macrotech Developers, branded as Lodha, is one of India's largest real estate "
            "developers building premium and affordable residential housing, commercial spaces, "
            "and industrial parks in Mumbai, Pune, Hyderabad, and Bengaluru. Its affordable "
            "housing segment targets the growing middle class across urban India."
        ),
    ),
    # ── EdTech / Online Services ──────────────────────────────────────────
    IPORecord(
        symbol="JUSTDIAL",
        company="Just Dial",
        sector="Local Search / Internet",
        ipo_date="2020-07-01",
        issue_price=542.0,
        listing_price=625.0,
        website_url="https://www.justdial.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Just_Dial",
        description=(
            "Just Dial is India's leading local search engine and discovery platform connecting "
            "consumers with local businesses across cities, tier-2 and tier-3 towns, and semi-urban "
            "areas. It provides phone-based and digital search for restaurants, doctors, services, "
            "and shops across India including rural Bharat."
        ),
    ),
    IPORecord(
        symbol="GLOBAL",
        company="Global Health (Medanta)",
        sector="Healthcare / Hospital",
        ipo_date="2022-11-07",
        issue_price=336.0,
        listing_price=401.0,
        website_url="https://www.medanta.org",
        wikipedia_url="https://en.wikipedia.org/wiki/Medanta",
        description=(
            "Medanta is one of India's largest multi-specialty hospital chains offering "
            "advanced medical care including cardiac surgery, cancer treatment, organ transplants, "
            "neurosciences, and orthopaedics. It operates hospitals in Gurugram, Lucknow, Patna, "
            "Indore, and Ranchi, serving patients from tier-2 cities and semi-urban regions."
        ),
    ),
    # ── Auto Ancillary ────────────────────────────────────────────────────
    IPORecord(
        symbol="SANSERA",
        company="Sansera Engineering",
        sector="Auto Ancillary",
        ipo_date="2021-09-24",
        issue_price=744.0,
        listing_price=762.0,
        website_url="https://www.sansera.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Sansera_Engineering",
        description=(
            "Sansera Engineering is a precision engineering component manufacturer producing "
            "crankshafts, connecting rods, rocker arms, and gears for two-wheeler, commercial "
            "vehicle, and passenger car OEMs. It also develops components for electric vehicles "
            "and aerospace applications, exporting to Tier 1 suppliers worldwide."
        ),
    ),
    IPORecord(
        symbol="STARHEALTH",
        company="Star Health and Allied Insurance",
        sector="Health Insurance",
        ipo_date="2021-12-10",
        issue_price=900.0,
        listing_price=848.0,
        website_url="https://www.starhealth.in",
        wikipedia_url="https://en.wikipedia.org/wiki/Star_Health_and_Allied_Insurance",
        description=(
            "Star Health and Allied Insurance is India's largest standalone health insurance "
            "company providing retail health insurance policies. It serves urban, semi-urban, "
            "and tier-2 city consumers through individual agents, banks, and digital channels "
            "offering cashless hospitalisation and family health protection plans."
        ),
    ),
    # ── Additional IPOs ───────────────────────────────────────────────────
    IPORecord(
        symbol="NURECA",
        company="Nureca",
        sector="Healthcare Products",
        ipo_date="2021-02-15",
        issue_price=400.0,
        listing_price=616.0,
        website_url="https://www.nureca.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Nureca",
        description=(
            "Nureca is a digital-first healthcare products company selling home-health and "
            "wellness devices including blood pressure monitors, glucometers, nebulizers, "
            "weighing scales, and baby care products through e-commerce platforms in India. "
            "It targets health-conscious consumers in urban and tier-2 cities."
        ),
    ),
    IPORecord(
        symbol="RAILTEL",
        company="RailTel Corporation of India",
        sector="Telecom / Government IT",
        ipo_date="2021-02-26",
        issue_price=94.0,
        listing_price=109.0,
        website_url="https://www.railtelindia.com",
        wikipedia_url="https://en.wikipedia.org/wiki/RailTel_Corporation_of_India",
        description=(
            "RailTel Corporation is a government-owned telecom infrastructure provider "
            "operating India's largest neutral telecom network on railway land. It provides "
            "broadband, VPN, cloud services, and WiFi connectivity to railway stations including "
            "rural and semi-urban stations across India under the Digital India initiative."
        ),
    ),
    IPORecord(
        symbol="LPDC",
        company="Laxmi Organic Industries",
        sector="Specialty Chemicals",
        ipo_date="2021-03-15",
        issue_price=130.0,
        listing_price=156.0,
        website_url="https://www.laxmi.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Laxmi_Organic_Industries",
        description=(
            "Laxmi Organic Industries is India's largest manufacturer of acetyl intermediates "
            "and specialty intermediates. Its ethyl acetate and diketene products are used in "
            "pharmaceuticals, agrochemicals, coatings, and food additives industries globally."
        ),
    ),
    IPORecord(
        symbol="NAZARA",
        company="Nazara Technologies",
        sector="Gaming / Tech",
        ipo_date="2021-03-30",
        issue_price=1101.0,
        listing_price=1990.0,
        website_url="https://www.nazara.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Nazara_Technologies",
        description=(
            "Nazara Technologies is India's leading diversified gaming and sports media company. "
            "It operates mobile games, esports platforms, AdTech, and edtech products using "
            "artificial intelligence and machine learning. It targets the mobile gaming market "
            "across India, Africa, and emerging markets."
        ),
    ),
    IPORecord(
        symbol="CRAFTSMAN",
        company="Craftsman Automation",
        sector="Engineering / Auto",
        ipo_date="2021-03-25",
        issue_price=1490.0,
        listing_price=1515.0,
        website_url="https://www.craftsmanautomation.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Craftsman_Automation",
        description=(
            "Craftsman Automation is a diversified engineering company manufacturing powertrain "
            "components, aluminium die castings, industrial and engineering products. It serves "
            "automotive OEMs including two-wheeler, commercial vehicle, and tractor manufacturers "
            "and is transitioning to electric vehicle component manufacturing."
        ),
    ),
    IPORecord(
        symbol="POWERGRID",
        company="Power Grid Corporation InvIT",
        sector="Infrastructure / Power",
        ipo_date="2021-04-29",
        issue_price=100.0,
        listing_price=108.0,
        website_url="https://www.powergridinvit.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Power_Grid_Corporation_of_India",
        description=(
            "Power Grid InvIT is an infrastructure investment trust holding transmission line "
            "assets from Power Grid Corporation of India. It provides stable income from power "
            "transmission infrastructure serving electricity distribution across rural India, "
            "Bharat, and urban areas through the national grid."
        ),
    ),
    IPORecord(
        symbol="MTAR",
        company="MTAR Technologies",
        sector="Defence / Aerospace",
        ipo_date="2021-03-03",
        issue_price=575.0,
        listing_price=1050.0,
        website_url="https://www.mtartech.com",
        wikipedia_url="https://en.wikipedia.org/wiki/MTAR_Technologies",
        description=(
            "MTAR Technologies is a precision engineering company manufacturing critical and "
            "high-precision components for space, nuclear energy, defence, and clean energy "
            "sectors. Its products serve ISRO, DRDO, BARC, and international aerospace "
            "companies using advanced CNC machining and surface finishing."
        ),
    ),
    IPORecord(
        symbol="BROOKFIELD",
        company="Brookfield India Real Estate Trust",
        sector="Real Estate / REIT",
        ipo_date="2021-02-17",
        issue_price=275.0,
        listing_price=290.0,
        website_url="https://brookfieldindiareit.in",
        wikipedia_url="https://en.wikipedia.org/wiki/Brookfield_Asset_Management",
        description=(
            "Brookfield India Real Estate Trust is a SEBI-registered Real Estate Investment "
            "Trust owning commercial office parks in Mumbai, Gurugram, Noida, and Kolkata. "
            "It provides office space to multinational corporations and IT companies, generating "
            "stable rental income for unitholders."
        ),
    ),
    IPORecord(
        symbol="SHYAMMETALICS",
        company="Shyam Metalics and Energy",
        sector="Steel / Metals",
        ipo_date="2021-06-24",
        issue_price=306.0,
        listing_price=300.0,
        website_url="https://www.shyammetalics.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Shyam_Metalics_and_Energy",
        description=(
            "Shyam Metalics and Energy is an integrated steel producer manufacturing ferro "
            "alloys, sponge iron, steel billets, TMT bars, and pellets in Odisha and West "
            "Bengal. It supplies construction steel to real estate, infrastructure, and "
            "manufacturing sectors including rural housing in eastern India."
        ),
    ),
    IPORecord(
        symbol="TATAMOTORS",
        company="Tata Motors DVR",
        sector="Automotive",
        ipo_date="2020-10-28",
        issue_price=150.0,
        listing_price=162.0,
        website_url="https://www.tatamotors.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Tata_Motors",
        description=(
            "Tata Motors is India's largest commercial vehicle manufacturer and a major passenger "
            "vehicle maker under the Tata, Jaguar, and Land Rover brands. It is India's leader "
            "in electric vehicles with the Nexon EV and Tiago EV, targeting urban and "
            "semi-urban consumers seeking electric mobility solutions."
        ),
    ),
    IPORecord(
        symbol="ANANTRAJ",
        company="Anant Raj",
        sector="Real Estate / IT Parks",
        ipo_date="2020-03-02",
        issue_price=70.0,
        listing_price=68.0,
        website_url="https://www.anantraj.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Anant_Raj",
        description=(
            "Anant Raj is a real estate developer in the Delhi NCR region focusing on data "
            "centres, IT parks, commercial and residential properties. It is expanding into "
            "cloud and data centre infrastructure to serve the growing digital economy and "
            "enterprise technology sector in India."
        ),
    ),
    IPORecord(
        symbol="UGROCAPITAL",
        company="Ugro Capital",
        sector="NBFC / Fintech",
        ipo_date="2023-09-14",
        issue_price=200.0,
        listing_price=218.0,
        website_url="https://www.ugrocapital.com",
        wikipedia_url="https://en.wikipedia.org/wiki/UGRO_Capital",
        description=(
            "UGRO Capital is a data-tech NBFC focused on small and medium enterprise lending "
            "using technology and data analytics to underwrite credit for MSMEs in tier-2 and "
            "tier-3 cities across India. It uses machine learning and alternative data to "
            "provide business loans to underserved entrepreneurs in Bharat."
        ),
    ),
    IPORecord(
        symbol="IXIGO",
        company="Le Travenues Technology (ixigo)",
        sector="Travel Tech",
        ipo_date="2024-06-18",
        issue_price=93.0,
        listing_price=138.0,
        website_url="https://www.ixigo.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Ixigo",
        description=(
            "Ixigo is India's largest AI-powered travel app for train, bus, and flight bookings "
            "targeting users in tier-2 and tier-3 cities, semi-urban areas, and rural Bharat. "
            "Its Trains app is India's most-used train discovery and booking platform serving "
            "first-time internet users with Hindi-language support and offline functionality."
        ),
    ),
    IPORecord(
        symbol="FIRSTCRY",
        company="Brainbees Solutions (FirstCry)",
        sector="Baby Care E-Commerce",
        ipo_date="2024-08-13",
        issue_price=465.0,
        listing_price=651.0,
        website_url="https://www.firstcry.com",
        wikipedia_url="https://en.wikipedia.org/wiki/FirstCry",
        description=(
            "FirstCry is Asia's largest platform for mother and baby care products, selling "
            "toys, clothing, feeding gear, and maternity products online and through retail "
            "stores. It uses machine learning to personalise product recommendations and serves "
            "new parents across urban, tier-2, and semi-urban India."
        ),
    ),
    IPORecord(
        symbol="OLA",
        company="Ola Electric Mobility",
        sector="Electric Vehicles",
        ipo_date="2024-08-02",
        issue_price=76.0,
        listing_price=75.99,
        website_url="https://olaelectric.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Ola_Electric",
        description=(
            "Ola Electric is India's largest electric two-wheeler manufacturer, producing Ola "
            "S1 electric scooters at its Futurefactory in Tamil Nadu. It is building a vertically "
            "integrated EV ecosystem including cell manufacturing, charging networks, and software "
            "to accelerate India's transition to sustainable green electric mobility."
        ),
    ),
    IPORecord(
        symbol="BHARTIHEXA",
        company="Bharti Hexacom",
        sector="Telecom",
        ipo_date="2024-04-15",
        issue_price=570.0,
        listing_price=755.0,
        website_url="https://www.airtel.in",
        wikipedia_url="https://en.wikipedia.org/wiki/Bharti_Airtel",
        description=(
            "Bharti Hexacom is a subsidiary of Bharti Airtel providing mobile, fixed broadband, "
            "and enterprise telecom services in Rajasthan and the North East states of India. "
            "It operates 4G and 5G networks reaching urban, rural Bharat, semi-urban, and tier-3 "
            "areas through Airtel's unified brand and digital payment platform Airtel Money."
        ),
    ),
    IPORecord(
        symbol="SAGILITY",
        company="Sagility India",
        sector="Healthcare BPO / IT",
        ipo_date="2024-11-05",
        issue_price=30.0,
        listing_price=31.06,
        website_url="https://www.sagility.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Sagility",
        description=(
            "Sagility is a technology-enabled healthcare services company providing business "
            "process outsourcing to US health insurance payers and healthcare providers. "
            "It uses AI, automation, and machine learning to process claims, manage member "
            "services, and optimise revenue cycle management for healthcare clients."
        ),
    ),
    IPORecord(
        symbol="HYUNDAIMOTOR",
        company="Hyundai Motor India",
        sector="Automotive",
        ipo_date="2024-10-22",
        issue_price=1960.0,
        listing_price=1931.0,
        website_url="https://www.hyundai.com/in",
        wikipedia_url="https://en.wikipedia.org/wiki/Hyundai_Motor_India",
        description=(
            "Hyundai Motor India is the second-largest passenger vehicle manufacturer in India, "
            "producing petrol, diesel, CNG, and electric vehicles. Its Creta, Venue, and i20 "
            "models are popular across urban and tier-2 cities. It is expanding its electric "
            "vehicle lineup with the Ioniq 5 and Creta Electric for the Indian market."
        ),
    ),
    IPORecord(
        symbol="BAJAJHOUSE",
        company="Bajaj Housing Finance",
        sector="Housing Finance / NBFC",
        ipo_date="2024-09-16",
        issue_price=70.0,
        listing_price=150.0,
        website_url="https://www.bajajhousingfinance.in",
        wikipedia_url="https://en.wikipedia.org/wiki/Bajaj_Housing_Finance",
        description=(
            "Bajaj Housing Finance is one of India's fastest-growing non-bank mortgage lenders "
            "providing home loans, loan against property, and lease rental discounting. It serves "
            "customers in metropolitan cities and tier-2 cities, using digital platforms and "
            "technology-driven underwriting to disburse affordable home loans."
        ),
    ),
    IPORecord(
        symbol="SWIGGY",
        company="Bundl Technologies (Swiggy)",
        sector="Food Tech / Q-Commerce",
        ipo_date="2024-11-13",
        issue_price=390.0,
        listing_price=412.0,
        website_url="https://www.swiggy.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Swiggy",
        description=(
            "Swiggy is India's second-largest online food delivery platform and quick commerce "
            "company. Its Instamart service delivers groceries, household essentials, and "
            "medicines in under 10 minutes in major cities. Swiggy Genie provides courier and "
            "errand services, all powered by AI-driven logistics and delivery optimization."
        ),
    ),
    IPORecord(
        symbol="AWFIS",
        company="Awfis Space Solutions",
        sector="Co-working / PropTech",
        ipo_date="2024-05-22",
        issue_price=383.0,
        listing_price=432.0,
        website_url="https://www.awfis.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Awfis",
        description=(
            "Awfis is India's largest co-working and flexible office space provider operating "
            "in metro cities, tier-2 cities, and semi-urban business districts. It provides "
            "managed workspaces, hot desks, meeting rooms, and enterprise office solutions "
            "to startups, SMEs, and large corporations seeking flexible workspace."
        ),
    ),
    IPORecord(
        symbol="TBO",
        company="TBO Tek",
        sector="Travel Tech / B2B",
        ipo_date="2024-05-08",
        issue_price=875.0,
        listing_price=1426.0,
        website_url="https://www.tbo.com",
        wikipedia_url="https://en.wikipedia.org/wiki/TBO_Tek",
        description=(
            "TBO Tek is a global travel distribution platform connecting travel buyers (agents, "
            "OTAs, corporates) with travel suppliers (hotels, airlines, car rentals) through an "
            "integrated B2B marketplace. It uses technology and machine learning to optimise "
            "pricing, inventory allocation, and payment processing for travel businesses."
        ),
    ),
    IPORecord(
        symbol="KFINTECH",
        company="KFin Technologies",
        sector="Fintech / Capital Markets",
        ipo_date="2022-12-21",
        issue_price=366.0,
        listing_price=312.0,
        website_url="https://www.kfintech.com",
        wikipedia_url="https://en.wikipedia.org/wiki/KFin_Technologies",
        description=(
            "KFin Technologies is India's leading technology platform for capital market "
            "infrastructure services, providing mutual fund registrar and transfer agent "
            "services, issuer solutions for IPOs, and investor services. It uses digital "
            "payment processing, AI-driven KYC, and data analytics for financial market participants."
        ),
    ),
    IPORecord(
        symbol="DREAMFOLKS",
        company="Dreamfolks Services",
        sector="Fintech / Lifestyle",
        ipo_date="2022-09-06",
        issue_price=326.0,
        listing_price=429.0,
        website_url="https://www.dreamfolks.in",
        wikipedia_url="https://en.wikipedia.org/wiki/Dreamfolks_Services",
        description=(
            "Dreamfolks is India's largest airport service aggregator providing lounge access, "
            "spa, transit hotels, and ancillary travel services through a digital platform. "
            "It connects credit card issuers, airlines, and airports to deliver premium travel "
            "experience benefits to cardholders using a technology-first payment gateway model."
        ),
    ),
    IPORecord(
        symbol="DELHIVERY2",
        company="Tracxn Technologies",
        sector="Market Intelligence / SaaS",
        ipo_date="2022-10-20",
        issue_price=80.0,
        listing_price=73.0,
        website_url="https://tracxn.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Tracxn",
        description=(
            "Tracxn Technologies is a SaaS-based market intelligence platform providing data "
            "on startups, private companies, and investment trends to venture capital funds, "
            "investment banks, and corporate strategy teams. It uses machine learning and "
            "AI to track and analyse the global startup ecosystem."
        ),
    ),
    IPORecord(
        symbol="KAYNES",
        company="Kaynes Technology India",
        sector="Electronics Manufacturing",
        ipo_date="2022-11-22",
        issue_price=587.0,
        listing_price=915.0,
        website_url="https://kaynes.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Kaynes_Technology",
        description=(
            "Kaynes Technology is an end-to-end IoT-enabled integrated electronics manufacturing "
            "and solutions company. It designs and manufactures printed circuit board assemblies, "
            "box builds, and embedded systems for automotive, aerospace, defence, medical, "
            "and industrial electronics sectors using advanced automation."
        ),
    ),
    IPORecord(
        symbol="UNIPARTS",
        company="Uniparts India",
        sector="Engineering / Agri",
        ipo_date="2022-12-01",
        issue_price=577.0,
        listing_price=530.0,
        website_url="https://www.unipartsindia.com",
        wikipedia_url="https://en.wikipedia.org/wiki/Uniparts_India",
        description=(
            "Uniparts India is a global manufacturer of engineered systems and solutions for "
            "off-highway, agriculture, construction, and forestry equipment. It exports precision "
            "components to North America and Europe, supplying John Deere, CNH Industrial, "
            "and other OEMs with hydraulic and mechanical systems."
        ),
    ),
]


def filter_by_timeframe(start_year: int, end_year: int) -> list[IPORecord]:
    """Return IPOs whose ipo_date falls within [start_year, end_year] inclusive."""
    return [
        r for r in CORPUS
        if start_year <= int(r.ipo_date[:4]) <= end_year
    ]


def get_by_symbol(symbol: str) -> IPORecord | None:
    for r in CORPUS:
        if r.symbol.upper() == symbol.upper():
            return r
    return None
