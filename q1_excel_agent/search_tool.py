"""Lightweight search and terminology lookup tool for inventory management concepts."""

import re
from typing import Dict, Any, Optional

# Curated reference glossary for inventory management terminology.
# Ensures deterministic, reliable definitions for standard business queries
# without requiring extra third-party search APIs or paid external keys.
INVENTORY_GLOSSARY: Dict[str, Dict[str, str]] = {
    "safety stock": {
        "term": "Safety Stock",
        "definition": (
            "A surplus buffer quantity of stock held by a business to mitigate the risk of stockouts "
            "caused by unexpected surges in customer demand or supplier lead-time delays. "
            "Formula: Safety Stock = (Max Daily Sales * Max Lead Time) - (Avg Daily Sales * Avg Lead Time)."
        ),
        "source": "APICS / Supply Chain Management Reference",
    },
    "inventory turnover": {
        "term": "Inventory Turnover (Turnover Ratio)",
        "definition": (
            "A financial efficiency metric indicating how many times a company sells and replaces its stock "
            "of goods over a specified period. A higher ratio generally signals robust sales or lean inventory. "
            "Formula: Inventory Turnover = Cost of Goods Sold (COGS) / Average Inventory Value."
        ),
        "source": "Corporate Finance Institute / Inventory Accounting Guidelines",
    },
    "eoq": {
        "term": "EOQ (Economic Order Quantity)",
        "definition": (
            "The optimal order quantity that minimizes total inventory management costs, balancing order setup costs "
            "against inventory holding/carrying costs. "
            "Formula: EOQ = sqrt((2 * Annual Demand * Order Cost) / Holding Cost per Unit)."
        ),
        "source": "Production and Operations Management Reference",
    },
    "economic order quantity": {
        "term": "Economic Order Quantity (EOQ)",
        "definition": (
            "The ideal order quantity a company should purchase to minimize inventory costs such as holding costs, "
            "shortage costs, and order costs. "
            "Formula: EOQ = sqrt((2 * D * S) / H) where D = Annual Demand, S = Setup/Order Cost, H = Holding Cost."
        ),
        "source": "Production and Operations Management Reference",
    },
    "reorder point": {
        "term": "Reorder Point (ROP)",
        "definition": (
            "The specific inventory level that triggers an order for additional inventory items to arrive before stockouts occur. "
            "Formula: Reorder Point = (Lead Time Demand) + Safety Stock."
        ),
        "source": "Supply Chain Operations Reference",
    },
    "carrying cost": {
        "term": "Carrying Cost (Holding Cost)",
        "definition": (
            "The total cost associated with storing and maintaining unsold goods, including warehousing space, insurance, "
            "taxes, employee labor, depreciation, and shrinkage. Typically represents 15% to 30% of inventory value."
        ),
        "source": "Managerial Accounting Standard Reference",
    },
    "holding cost": {
        "term": "Holding Cost (Carrying Cost)",
        "definition": (
            "The total cost of holding inventory in a warehouse over time, including capital cost, storage space costs, "
            "inventory service costs, and inventory risk costs."
        ),
        "source": "Managerial Accounting Standard Reference",
    },
    "stockout": {
        "term": "Stockout (Out of Stock)",
        "definition": (
            "An event where customer demand for an item cannot be fulfilled because inventory has been completely depleted, "
            "leading to lost revenue and potential customer dissatisfaction."
        ),
        "source": "Retail Operations Reference",
    },
    "reconciliation": {
        "term": "Inventory Reconciliation",
        "definition": (
            "The accounting procedure of comparing physical inventory counts against digital stock records to identify "
            "and explain discrepancies caused by shrinkage, unrecorded sales, damaged goods, or clerical errors."
        ),
        "source": "Inventory Accounting Standards",
    },
    "stock discrepancy": {
        "term": "Inventory Stock Discrepancy",
        "definition": (
            "A discrepancy or variance between the recorded stock quantity in the database and the physical count "
            "or theoretical calculation (e.g., Opening Stock + Purchases - Sales != Recorded Hand-in-Stock). "
            "Common causes include unrecorded wastage, theft/shrinkage, supplier short-shipment, or data entry errors."
        ),
        "source": "Inventory Audit & Quality Assurance Guidelines",
    },
}


def search_inventory_context(query: str) -> Dict[str, Any]:
    """
    Search definitions, formulas, and operational context for inventory management terminology.
    
    Parameters:
        query: Term or question to look up (e.g., 'What is safety stock?', 'EOQ', 'inventory turnover').
        
    Returns:
        Structured dictionary containing query, found status, definition, and source.
    """
    clean_q = query.lower().strip()
    
    # 1. Direct or substring matching against curated glossary
    for key, data in INVENTORY_GLOSSARY.items():
        if key in clean_q or re.search(rf"\b{re.escape(key)}\b", clean_q):
            return {
                "query": query,
                "found": True,
                "term": data["term"],
                "definition": data["definition"],
                "source": data["source"],
            }

    # 2. Token overlap fallback
    tokens = set(re.findall(r"\w+", clean_q))
    best_match = None
    max_overlap = 0
    for key, data in INVENTORY_GLOSSARY.items():
        key_tokens = set(key.split())
        overlap = len(tokens.intersection(key_tokens))
        if overlap > max_overlap:
            max_overlap = overlap
            best_match = data

    if best_match and max_overlap > 0:
        return {
            "query": query,
            "found": True,
            "term": best_match["term"],
            "definition": best_match["definition"],
            "source": best_match["source"],
        }

    # 3. Not found in local glossary
    return {
        "query": query,
        "found": False,
        "term": query,
        "definition": (
            f"No specific inventory glossary entry found for '{query}'. "
            "For general web search, ensure Gemini native Google Search Grounding is enabled."
        ),
        "source": "None",
    }
