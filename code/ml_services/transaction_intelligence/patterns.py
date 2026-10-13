import re
from typing import Dict, List, Tuple

from .types import TransactionCategory as C

MERCHANT_PATTERNS: Dict[C, List[str]] = {
    C.GROCERIES: [
        r"walmart|target|kroger|safeway|whole foods|trader joe|costco|aldi|carrefour|tesco|imtiaz|al-fatah",
        r"grocery|supermarket|food store|deli|butcher|produce|farmers market",
    ],
    C.RESTAURANTS: [
        r"mcdonald|burger king|kfc|subway|pizza|starbucks|dunkin|taco bell|domino|chipotle",
        r"restaurant|cafe|bistro|grill|diner|pub|brewery|doordash|uber eats|grubhub|foodpanda",
    ],
    C.GAS_STATIONS: [
        r"shell|exxon|\bbp\b|chevron|mobil|texaco|citgo|marathon|sunoco|total energies|pso",
        r"gas station|fuel|petrol|gasoline",
    ],
    C.RETAIL_SHOPPING: [
        r"best buy|home depot|lowes|macy|nordstrom|\bgap\b|ikea|h&m|zara|nike|adidas",
        r"department store|retail|mall|outlet|boutique",
    ],
    C.ONLINE_SHOPPING: [
        r"amazon|ebay|etsy|shopify|aliexpress|daraz|paypal \*|stripe \*|square \*",
        r"online store|e-commerce|web store",
    ],
    C.ENTERTAINMENT: [
        r"netflix|spotify|disney|hulu|youtube|apple music|prime video|steam|playstation|xbox",
        r"movie|theater|cinema|concert|ticketmaster|sports|game",
    ],
    C.TRAVEL: [
        r"airline|airways|airport|hotel|motel|airbnb|booking\.com|expedia|resort",
        r"vacation|flight|rental car|hertz|avis",
    ],
    C.TRANSPORTATION: [
        r"uber|lyft|careem|metro|transit|parking|toll|taxi|train|bus fare"
    ],
    C.HEALTHCARE: [
        r"hospital|clinic|doctor|dentist|pharmacy|cvs|walgreens|rite aid|lab",
        r"medical|health|dental|vision|prescription",
    ],
    C.UTILITIES: [
        r"electric|water|sewer|internet|cable|wireless|verizon|at&t|comcast|t-mobile|jazz|zong|ptcl|k-electric|sui gas",
        r"utility|telecom|broadband",
    ],
    C.INSURANCE: [r"insurance|geico|allstate|state farm|aetna|assurance|takaful"],
    C.EDUCATION: [r"university|college|school|tuition|coursera|udemy|textbook|academy"],
    C.PROFESSIONAL_SERVICES: [r"consulting|legal|attorney|accounting|notary|freelance"],
    C.HOME_IMPROVEMENT: [r"hardware|plumb|electrician|furniture|garden|lumber|paint"],
    C.PERSONAL_CARE: [r"salon|barber|spa|gym|fitness|beauty|cosmetic"],
    C.CHARITY: [r"donation|charity|foundation|red cross|unicef|edhi|zakat|ngo"],
    C.INVESTMENTS: [r"brokerage|fidelity|vanguard|robinhood|etrade|mutual fund|invest"],
    C.ATM_WITHDRAWALS: [r"\batm\b|cash withdrawal"],
    C.FEES: [
        r"fee|service charge|overdraft|penalty|interest charge|maintenance charge"
    ],
    C.INCOME: [r"salary|payroll|direct deposit|wages|dividend|bonus"],
    C.REFUNDS: [r"refund|reversal|chargeback|cashback"],
    C.TRANSFERS: [r"transfer|wire|zelle|venmo|p2p|remittance|sent to|received from"],
}

COMPILED_PATTERNS: Dict[C, List["re.Pattern[str]"]] = {
    category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for category, patterns in MERCHANT_PATTERNS.items()
}

MCC_RANGES: List[Tuple[int, int, C]] = [
    (5411, 5411, C.GROCERIES),
    (5499, 5499, C.GROCERIES),
    (5812, 5814, C.RESTAURANTS),
    (5541, 5542, C.GAS_STATIONS),
    (5311, 5399, C.RETAIL_SHOPPING),
    (5651, 5699, C.RETAIL_SHOPPING),
    (5964, 5969, C.ONLINE_SHOPPING),
    (5815, 5818, C.ENTERTAINMENT),
    (7832, 7841, C.ENTERTAINMENT),
    (7911, 7999, C.ENTERTAINMENT),
    (3000, 3299, C.TRAVEL),
    (4511, 4511, C.TRAVEL),
    (7011, 7011, C.TRAVEL),
    (3351, 3441, C.TRAVEL),
    (4111, 4131, C.TRANSPORTATION),
    (4784, 4789, C.TRANSPORTATION),
    (7523, 7523, C.TRANSPORTATION),
    (8011, 8099, C.HEALTHCARE),
    (5912, 5912, C.HEALTHCARE),
    (4812, 4829, C.UTILITIES),
    (4899, 4900, C.UTILITIES),
    (6300, 6399, C.INSURANCE),
    (8211, 8299, C.EDUCATION),
    (8999, 8999, C.PROFESSIONAL_SERVICES),
    (7399, 7399, C.PROFESSIONAL_SERVICES),
    (5200, 5261, C.HOME_IMPROVEMENT),
    (5712, 5719, C.HOME_IMPROVEMENT),
    (7230, 7299, C.PERSONAL_CARE),
    (7997, 7997, C.PERSONAL_CARE),
    (8398, 8398, C.CHARITY),
    (6211, 6211, C.INVESTMENTS),
    (6010, 6011, C.ATM_WITHDRAWALS),
    (6012, 6012, C.FEES),
    (4829, 4829, C.TRANSFERS),
    (6538, 6540, C.TRANSFERS),
]

SEED_CORPUS: List[Tuple[str, C]] = [
    ("weekly grocery shopping fresh vegetables", C.GROCERIES),
    ("supermarket purchase milk bread eggs", C.GROCERIES),
    ("lunch at the cafe downtown", C.RESTAURANTS),
    ("dinner reservation pizza and pasta", C.RESTAURANTS),
    ("fill up tank petrol pump", C.GAS_STATIONS),
    ("monthly electricity bill payment", C.UTILITIES),
    ("internet and phone service bill", C.UTILITIES),
    ("streaming subscription monthly", C.ENTERTAINMENT),
    ("cinema tickets weekend movie", C.ENTERTAINMENT),
    ("flight booking return ticket", C.TRAVEL),
    ("hotel stay two nights", C.TRAVEL),
    ("ride to airport taxi", C.TRANSPORTATION),
    ("pharmacy prescription medicine", C.HEALTHCARE),
    ("doctor consultation clinic visit", C.HEALTHCARE),
    ("health insurance premium", C.INSURANCE),
    ("university semester tuition", C.EDUCATION),
    ("online course enrollment", C.EDUCATION),
    ("salary credited by employer", C.INCOME),
    ("monthly payroll deposit", C.INCOME),
    ("refund for returned item", C.REFUNDS),
    ("atm cash withdrawal", C.ATM_WITHDRAWALS),
    ("account maintenance fee", C.FEES),
    ("overdraft penalty charge", C.FEES),
    ("sent money to a friend", C.TRANSFERS),
    ("wire transfer to savings", C.TRANSFERS),
    ("clothing store purchase jacket", C.RETAIL_SHOPPING),
    ("online order delivered package", C.ONLINE_SHOPPING),
    ("hardware store tools and paint", C.HOME_IMPROVEMENT),
    ("gym membership monthly", C.PERSONAL_CARE),
    ("haircut and salon visit", C.PERSONAL_CARE),
    ("charity donation monthly giving", C.CHARITY),
    ("mutual fund investment contribution", C.INVESTMENTS),
    ("legal consultation attorney fee", C.PROFESSIONAL_SERVICES),
    ("fresh fruit and vegetables market", C.GROCERIES),
    ("burger and fries takeaway", C.RESTAURANTS),
    ("coffee and sandwich", C.RESTAURANTS),
    ("car fuel refill", C.GAS_STATIONS),
    ("water and gas utility bill", C.UTILITIES),
    ("music and video subscription", C.ENTERTAINMENT),
    ("concert tickets", C.ENTERTAINMENT),
    ("train ticket and bus fare", C.TRANSPORTATION),
    ("airline baggage fee holiday trip", C.TRAVEL),
    ("dental checkup", C.HEALTHCARE),
    ("hospital bill", C.HEALTHCARE),
    ("car insurance premium", C.INSURANCE),
    ("school fees and textbooks", C.EDUCATION),
    ("wages from employer", C.INCOME),
    ("freelance payment received", C.INCOME),
    ("purchase refunded to account", C.REFUNDS),
    ("cash withdrawn at machine", C.ATM_WITHDRAWALS),
    ("monthly service charge", C.FEES),
    ("money sent to family", C.TRANSFERS),
    ("received from friend", C.TRANSFERS),
    ("shoes and clothes shopping", C.RETAIL_SHOPPING),
    ("marketplace order shipped", C.ONLINE_SHOPPING),
    ("furniture and garden supplies", C.HOME_IMPROVEMENT),
    ("fitness club membership", C.PERSONAL_CARE),
    ("charitable donation", C.CHARITY),
    ("stock purchase brokerage", C.INVESTMENTS),
    ("accounting and tax advice", C.PROFESSIONAL_SERVICES),
]

AMOUNT_RANGES = {
    C.ATM_WITHDRAWALS: (20.0, 1000.0),
    C.UTILITIES: (10.0, 600.0),
    C.INSURANCE: (30.0, 2000.0),
    C.GROCERIES: (3.0, 500.0),
    C.RESTAURANTS: (3.0, 300.0),
    C.GAS_STATIONS: (5.0, 150.0),
}

SUBCATEGORIES = {
    C.ENTERTAINMENT: {
        "streaming": r"netflix|spotify|hulu|disney|prime video|youtube",
        "gaming": r"steam|playstation|xbox|game",
        "events": r"concert|ticketmaster|theater|cinema",
    },
    C.TRAVEL: {
        "flights": r"airline|airways|flight",
        "lodging": r"hotel|motel|airbnb|resort",
        "car_rental": r"hertz|avis|rental car",
    },
    C.UTILITIES: {
        "telecom": r"internet|wireless|phone|cable|telecom|verizon|at&t|jazz|zong|ptcl",
        "energy": r"electric|gas|k-electric|sui gas",
        "water": r"water|sewer",
    },
    C.RESTAURANTS: {
        "delivery": r"doordash|uber eats|grubhub|foodpanda|delivery",
        "coffee": r"starbucks|dunkin|cafe|coffee",
        "fast_food": r"mcdonald|burger king|kfc|subway|taco bell",
    },
}
