import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="SET50 Valuation Dashboard", layout="wide")

# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_secret(key: str) -> str:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, AttributeError):
        return os.getenv(key, "")

# ── Static dataset (parsed from 2026-06-11 Valuation Sheet) ──────────────────
# Columns: ticker, company, sector, rec, price, target, upside,
#          mktcap(Bt m), pe_26f, ev_26f, yield_26f, roe_26f, pbv_26f

RAW_STOCKS = [
    # Bank
    ("BBL",    "Bangkok Bank Pcl",               "Bank",             "HOLD",  168.50, 162.00,  -3.9, 321640,   9.8, None, 6.7,  8.6,  0.5),
    ("KBANK",  "KASIKORNBANK Pcl",               "Bank",             "BUY",   197.50, 216.00,   9.4, 467942,  10.2, None, 6.6, 10.1,  0.8),
    ("KKP",    "Kiatnakin Phatra Bank Pcl",       "Bank",             "BUY",    87.00,  92.00,   5.7,  75665,  10.8, None, 7.0,  7.8,  1.1),
    ("KTB",    "Krung Thai Bank Pcl",             "Bank",             "BUY",    21.60,  24.00,  11.1, 462977,  10.2, None, 7.8, 15.4,  0.8),
    ("SCB",    "SCB X Group Pcl",                "Bank",             "HOLD",  131.50, 140.00,   6.5, 485668,  13.5, None, 6.8,  9.1,  0.8),
    ("TISCO",  "Tisco Financial Pcl",            "Bank",             "BUY",   137.50, 152.00,  10.5,  90873,  10.3, None, 6.3, 10.1,  0.8),
    # Finance
    ("ASK",    "Asia Sermkij Leasing Pcl",       "Finance",          "SELL",    9.10,   7.30, -19.8,   6405,  12.5, None, 4.6, 11.6,  1.2),
    ("BAM",    "Bangkok Asset Management Pcl",   "Finance",          "HOLD",   10.50,  12.50, -19.0,  21655,  12.3, None, 6.5, 17.9,  None),
    ("JMT",    "JMT Network Services Pcl",       "Finance",          "SELL",   30.00,   7.50,  16.7,  15327,  12.2, None, 4.9,  3.9,  None),
    ("KTC",    "Krungthai Card Pcl",             "Finance",          "BUY",    64.75,  75.00,  11.9,  77350,   9.8, None, 6.1,  4.6,  2.3),
    ("MTC",    "Muangthai Leasing Pcl",          "Finance",          "BUY",    27.00,  37.00,  37.0,  57240,   7.9, None, 1.9, 15.8,  2.0),
    ("SAK",    "Saksiam Capital Pcl",            "Finance",          "BUY",     3.00,   4.60,  53.3,   6288,   6.0, None, 7.4, 14.6,  1.0),
    ("SAWAD",  "Srisawad Corporation Pcl",       "Finance",          "BUY",    45.50,  55.00,  18.1,  47783,   8.5, None, 6.5, 14.8,  None),
    ("THANI",  "Ratchthani Leasing Pcl",         "Finance",          "HOLD",   19.90,  23.50,  18.1,  33064,   6.3, None, 3.6, 13.3,  None),
    ("TIDLOR", "Tidlor Holdings Pcl",            "Finance",          "BUY",    16.50,  17.00,  42.0,  10092,   8.5, None, 4.4,  8.4,  None),
    # Insurance
    ("TQM",    "TQM Alpha Pcl",                  "Insurance",        "BUY",    13.50,  18.00,  33.3,   8100,   8.5,  5.5, 8.2, 29.9,  None),
    # Automotive
    ("SAT",    "Somboon Advance Tech. Pcl",      "Automotive",       "BUY",    15.60,  17.00,   9.0,   6633,   9.5,  3.0, 9.6,  8.3,  None),
    # Construction
    ("CK",     "CH. Karnchang Pcl",              "Construction",     "BUY",    17.80,  23.00,  29.2,  24001,  16.5, 26.3, 3.0,  9.0,  None),
    ("STECON", "Stecon Group Pcl",               "Construction",     "BUY",    15.80,  19.00,  20.3,  30151,  13.3, 19.6, 2.9,  8.8,  None),
    # Electronics
    ("DELTA",  "Delta Electronics (Thailand) Pcl","Electronics",     "BUY",   358.00, 420.00,  17.3,4465626, 103.7, 71.1, 0.3, 30.0,  None),
    ("HANA",   "Hana Microelectronics Pcl",      "Electronics",      "SELL",   34.75,  24.00, -30.9,  30766,  39.8, 10.7, 1.3, 13.0,  None),
    ("KCE",    "KCE Electronics Pcl",            "Electronics",      "HOLD",   36.25,  16.00, -55.9,  42851,  24.0, 15.0, 3.6,  2.9,  None),
    # Energy
    ("BANPU",  "Banpu Pcl",                      "Energy",           "BUY",    33.50,  41.00,  32.1,  49333,  10.8,  5.4, 6.0, 14.1,  None),
    ("BCP",    "Bangchak Corporation Pcl",       "Energy",           "BUY",     5.45,   7.20,  22.4,  49333,   4.5,  3.0, 8.0,  4.5,  None),
    ("IRPC",   "IRPC Pcl",                       "Energy",           "SELL",   23.20,  21.00, -21.2, 130258,  10.5,  4.4, 1.6,  5.2,  None),
    ("IVL",    "Indorama Ventures Pcl",          "Energy",           "SELL",   11.90,  13.50,  13.4, 142800,  17.7,  6.9, 3.0,  6.7,  None),
    ("OR",     "PTT Oil And Retail Pcl",         "Energy",           "BUY",     1.84,   1.45,  -9.5,  37599,  16.7,  5.9, 3.3,  7.4,  None),
    ("PTG",    "PTG Energy Pcl",                 "Energy",           "BUY",   144.50, 159.00,  47.9,  11857,  16.0,  3.9, 5.6,  7.4,  None),
    ("PTT",    "PTT Pcl",                        "Energy",           "BUY",    36.50,  43.00,  17.8, 573663,  10.2,  3.9, 6.8,  8.8,  None),
    ("PTTEP",  "PTT Exploration & Production Pcl","Energy",          "HOLD",    7.10, 161.00,  10.0,1042549,  None,  3.0, 6.2,  None, None),
    ("PTTGC",  "PTT Global Chemical Pcl",        "Energy",           "SELL",   34.75,  31.00, -10.8, 156683,  17.2,  6.6,12.3, 10.8,  None),
    ("SPRC",   "Star Petroleum Refining Pcl",    "Energy",           "BUY",     7.30,   8.50,  16.4,  31652,   9.5,  3.0, 1.4, 15.7,  None),
    ("TOP",    "Thai Oil Pcl",                   "Energy",           "BUY",    45.50,  60.00,  31.9, 101640,  10.3,  5.2, 6.1, 10.2,  None),
    # Food
    ("CBG",    "Carabao Group Pcl",              "Food",             "BUY",    39.25,  50.00,  27.4, 157210,  14.4, 10.0, 4.2, 18.5,  None),
    ("CPF",    "Charoen Pokphand Foods Pcl",     "Food",             "BUY",    18.70,  23.00,  23.0, 162720,  14.3,  9.2, 5.6, 13.8,  None),
    ("ITC",    "i-Tail Corporation Pcl",         "Food",             "HOLD",   15.90,  17.00,   6.9,  47700,   8.1,  8.6, 5.9,  8.2,  None),
    ("KCG",    "KCG Corporation Pcl",            "Food",             "BUY",    20.50,  12.00, -23.9,  18878,  14.2,  6.4, 5.8, 16.8,  None),
    ("M",      "MK Restaurant Group Pcl",        "Food",             "SELL",   15.10,  15.60,  22.4,  45357,  13.2,  3.5, 6.8, 10.1,  None),
    ("OSP",    "Osotspa Pcl",                    "Food",             "BUY",     9.80,  19.60,  29.8,   5341,   9.5,  8.2, 7.6, 20.7,  None),
    ("RBF",    "R&B Food Supply Pcl",            "Food",             "SELL",   30.25,  28.00, -36.7,   8840,  20.1, 10.0, 3.4, 18.1,  None),
    ("SAPPE",  "SAPPE Pcl",                      "Food",             "SELL",    4.42,   2.80,  -7.4,   9326,  10.9,  6.5, 4.6,  8.8,  None),
    ("SNNP",   "Srinanaporn Marketing Pcl",      "Food",             "HOLD",    3.96,   4.00,   1.0,   5465,   8.9,  7.6, 6.7,  9.9,  None),
    ("TKN",    "Taokaenoi Food Group Pcl",       "Food",             "SELL",   11.10,  12.60,  13.5,  47232,  10.8,  7.8, 7.7, 18.9,  None),
    ("TU",     "Thai Union Group Pcl",           "Food",             "SELL",    6.60,   6.40,  -3.0,  18780,  13.8,  8.2, 6.1, 17.8,  None),
    # Healthcare
    ("BCH",    "Bangkok Chain Hospital Pcl",     "Healthcare",       "SELL",    9.15,   8.30,  -9.3,  22818,  17.9, 12.1, 4.2, 15.1,  None),
    ("BDMS",   "Bangkok Dusit Medical Svcs Pcl", "Healthcare",       "HOLD",  175.50, 156.00, -11.1, 284467,  17.4, 13.3, 4.3, 15.3,  None),
    ("BH",     "Bumrungrad Hospital Pcl",        "Healthcare",       "SELL",  243.00, 257.00,  14.5, 139517,  19.9, 13.9, 3.8, 24.5,  None),
    ("CHG",    "Chularat Hospital Pcl",          "Healthcare",       "BUY",     1.41,   1.80,  27.7,  15510,  15.4,  8.1, 5.2, 12.7,  None),
    ("MASTER", "Master Style Group Pcl",         "Healthcare",       "SELL",   16.20,  24.00,  48.1,  12738,  14.3,  4.9, 6.5, 14.5,  None),
    ("PR9",    "Praram 9 Hospital Pcl",          "Healthcare",       "BUY",     8.45,   9.00,  53.6,   2549,  11.8,  7.6, 3.5,  7.8,  None),
    ("SAFE",   "Safe Fertility Hospital Pcl",    "Healthcare",       "BUY",     5.60,   8.60,   6.5,   1702,   9.3,  0.2, 8.0,  8.3,  None),
    ("THG",    "Thonburi Healthcare Group Pcl",  "Healthcare",       "SELL",    7.45,   7.20,  -3.4,  13329,  44.2, 10.2, 1.1,  2.2,  None),
    # Hotel / Tourism
    ("AWC",    "Asset World Corp. Pcl",          "Hotel",            "HOLD",    3.60,   3.20, -11.8,  76223,  34.8, 24.3, 1.2,  2.3,  None),
    ("CENTEL", "The Central Plaza Hotel Pcl",    "Hotel",            "BUY",     3.34,   2.10,  24.2,  44550,  22.6, 13.4, 2.0,  8.6,  None),
    ("ERW",    "Erawan Hotel Pcl",               "Hotel",            "BUY",     2.74,   3.20,  16.8,  13390,  None,  8.7, 2.7,  None, None),
    ("MINT",   "Minor International Pcl",        "Hotel",            "BUY",    21.90,  35.00,  59.8, 124172,  14.6,  8.0, 3.8, 16.5,  None),
    ("SPA",    "Siam Wellness Group Pcl",        "Hotel",            "BUY",     2.94,   4.50,  53.1,   3771,  14.3,  6.4, 2.4, 11.2,  None),
    # Industrial
    ("AMATA",  "Amata Corporation Pcl",          "Industrial",       "BUY",    27.00,  31.00,  14.8,  31050,  11.3, 10.1, 4.2, 10.6,  None),
    ("ETL",    "Euroasia Total Logistics Pcl",   "Industrial",       "SELL",    0.36,   0.48,  33.3,    223,  13.2,  1.2, 2.3, 14.7,  None),
    ("PIN",    "Pinthong Industrial Park Pcl",   "Industrial",       "BUY",     4.28,   5.60,  30.8,   4965,   7.4,  9.7, 7.3,  2.8,  None),
    ("ROJNA",  "Rojana Industrial Park Pcl",     "Industrial",       "BUY",     5.45,   8.60,  57.8,    620,   9.1,  4.9, 2.7,  5.9,  None),
    ("SJWD",   "SCGJWD Logistics Pcl",           "Industrial",       "BUY",     7.25,  11.60,  60.0,  13130,  10.9, 19.5, 4.1, 12.8,  None),
    ("WHA",    "WHA Corporation Pcl",            "Industrial",       "BUY",     4.96,   5.80,  16.9,  74136,  15.3,  6.3, 3.9,  5.1,  None),
    ("WICE",   "WICE Logistics Pcl",             "Industrial",       "SELL",    2.50,   2.60,   4.0,   1630,  33.6,  2.8, 2.8,  3.6,  None),
    # Materials
    ("DCC",    "Dynasty Ceramic Pcl",            "Materials",        "BUY",     1.32,   1.65,  25.0,  12046,  19.3, 13.7, 3.0, 13.0,  None),
    ("SCC",    "The Siam Cement Pcl",            "Materials",        "SELL",  237.00, 192.00, -19.0, 284400,  22.2, 15.1, 2.5, 19.1,  None),
    ("TOA",    "TOA Paint (Thailand) Pcl",       "Materials",        "BUY",    11.90,  16.00,  34.5,  24145,   8.4,  3.5, 7.2,  3.7,  None),
    # Media
    ("BEC",    "The BEC World Enterprise Pcl",   "Media",            "BUY",     1.96,   2.50,  27.6,   3920,  55.9,  3.6, 3.3,  1.5,  None),
    ("ONEE",   "One Enterprise Pcl",             "Media",            "BUY",     2.62,   3.20,  22.1,   6239,  23.5,  0.4, 3.4,  2.7,  None),
    ("PLANB",  "Plan B Media Pcl",               "Media",            "HOLD",    3.96,   4.80, -28.6,  18217, 139.7,  5.4, 5.2,  9.4,  None),
    ("RS",     "RS Pcl",                         "Media",            "SELL",    0.14,   0.10,  21.2,  18780,  16.4,  None, None, 0.4,  None),
    ("VGI",    "VGI Pcl",                        "Media",            "SELL",    0.89,   1.70,  91.0,    306,  None,  None, None, None, None),
    # Paper & Packaging
    ("SCGP",   "SCG Packaging Pcl",              "Paper&Packaging",  "BUY",    25.25,  29.00,  14.9, 108396,  19.7,  7.8, 3.2,  7.3,  None),
    # Pharmaceuticals
    ("MEGA",   "Mega Lifesciences Pcl",          "Pharmaceuticals",  "SELL",   34.25,  26.00, -24.1,  29862,  15.5,  9.1, 4.5, 18.2,  None),
    # Professional
    ("MEB",    "MEB Corporation Pcl",            "Professional",     "BUY",    11.50,  23.00, 100.0,   8930,   9.5,  5.8, 6.1, 22.8,  None),
    ("SISB",   "SISB Pcl",                       "Professional",     "BUY",     9.50,  12.00,  26.3,   3450,   8.0,  3.4, 9.3, 27.7,  None),
    # Property
    ("AP",     "AP (Thailand) Pcl",              "Property",         "BUY",     7.05,  10.00,  41.8,  22179,  10.3, 18.3, 5.8, 20.9,  None),
    ("LH",     "Land And Houses Pcl",            "Property",         "SELL",    3.60,   3.20, -11.1,  43019,  14.4, 36.5, 4.9,  5.7,  None),
    ("QH",     "Quality Houses Pcl",             "Property",         "HOLD",    1.32,   1.60,  21.2,  14143,   6.1, 26.3, 9.0,  7.4,  None),
    ("SIRI",   "Sansiri Pcl",                    "Property",         "SELL",   15.40,  20.50, -37.1,  30077,  14.2, 24.0, 2.8, 11.0,  None),
    ("SPALI",  "Supalai Pcl",                    "Property",         "BUY",     1.40,   0.88,  33.1,  24511,  13.9, 11.1, 7.0,  4.0,  None),
    # Retail
    ("ADVICE", "Advice IT Infinite Pcl",         "Retail",           "BUY",    13.90,  12.50, -10.1,   3813,  12.3,  5.9, 5.3, 28.3,  None),
    ("BJC",    "Berli Jucker Pcl",               "Retail",           "SELL",    6.15,   6.40,   4.1,  55708,  13.6,  8.4, 5.1,  3.4,  None),
    ("COM7",   "COM7 Pcl",                       "Retail",           "BUY",    26.50,  34.00,  28.3, 401994,  13.7, 10.2, 4.6, 39.8,  None),
    ("CPALL",  "CP All Pcl",                     "Retail",           "BUY",    44.75,  60.00,  34.1, 150158,  12.8,  6.9, 3.9, 21.5,  None),
    ("CPAXT",  "CP Axtra Pcl",                   "Retail",           "HOLD",   14.40,  16.00,  11.1,  63274,  13.7,  6.7, 5.1,  3.6,  None),
    ("CPN",    "Central Pattana Corp. Pcl",      "Retail",           "BUY",    63.50,  75.00,  18.1, 284988,  14.7, 10.7, 4.0, 17.0,  None),
    ("CRC",    "Central Retail Corp. Pcl",       "Retail",           "BUY",    20.90,  24.00,  14.8, 126048,  16.0, 12.9, 3.1, 12.0,  None),
    ("DOHOME", "Dohome Pcl",                     "Retail",           "SELL",    3.34,   3.20,  -4.2,  11752,  20.4,  5.8, 1.2,  4.1,  None),
    ("GLOBAL", "Siam Global House Pcl",          "Retail",           "BUY",     6.15,   8.50,  38.2,  34452,  14.3, 11.8, 3.5, 24.1,  None),
    ("HMPRO",  "Home Product Center Pcl",        "Retail",           "BUY",     6.00,   9.50,  58.3,  78907,  12.4,  7.4, 6.4,  9.2,  None),
    ("MC",     "MC Group Pcl",                   "Retail",           "BUY",    36.75,  50.00,  13.6,  12127,  10.8, 10.1, 9.3, 21.7,  None),
    ("MOSHI",  "Moshi Moshi Retail Corp. Pcl",   "Retail",           "BUY",    11.00,  12.50,  36.1,  53251,  14.4,  5.0, 4.2, 28.8,  None),
    ("MRDIYT", "Mr. D.I.Y. Holding (Thailand)",  "Retail",           "BUY",     8.85,  11.00,  24.3,   8712,  17.5,  7.8, 2.3, 28.2,  None),
    ("SABINA", "Sabina Pcl",                     "Retail",           "SELL",   15.00,  14.40,  -4.0,   5213,  12.5,  8.9, 8.0, 22.6,  None),
    # Shipping
    ("PSL",    "Precious Shipping Pcl",          "Shipping",         "BUY",     6.95,   4.20,  17.0,  10837,  21.2,  8.8, 3.9, 63.4,  None),
    # Telecom
    ("ADVANC", "Advanced Info Service Pcl",      "Telecom",          "SELL",  359.00, 420.00, -39.6,1067741,  20.9, 11.0, 0.0, 43.4,  None),
    ("THCOM",  "Thaicom Pcl",                    "Telecom",          "BUY",    13.80,  12.50,  19.6, 476819,  19.8,  9.7, 2.5, 29.4,  None),
    ("TRUE",   "True Corporation Pcl",           "Telecom",          "BUY",    11.70,  16.50,   6.8,  12824,  None,  8.0, None, None, None),
    # Transport
    ("AAV",    "Asia Aviation Pcl",              "Transport",        "SELL",    1.05,   0.95,  -9.6, 796428,  30.0, 20.8, 1.4,  3.4,  None),
    ("AOT",    "Airports of Thailand Pcl",       "Transport",        "BUY",    55.75,  65.00,  16.6,1147301,  22.2, 12.8, 2.0, 15.2,  None),
    ("BA",     "Bangkok Airways Pcl",            "Transport",        "BUY",    16.20,  16.50,  53.8,  34020,  43.2, 21.0, 3.2, 13.7,  None),
    ("BEM",    "Bangkok Exp. & Metro Pcl",       "Transport",        "BUY",     5.20,   8.00,   1.9,  79482,  12.7, 11.9, 2.9, 19.4,  None),
    ("BTS",    "BTS Group Holdings Pcl",         "Transport",        "HOLD",    2.04,   2.50,  22.5, 191047,   6.4, 40.5, 4.7, 34.1,  None),
    ("THAI",   "Thai Airways International Pcl", "Transport",        "SELL",    6.75,   7.70,  14.1,  32831,  None,  3.5, None, None, None),
    # Utilities
    ("BCPG",   "BCPG Pcl",                       "Utilities",        "BUY",    14.00,  10.50,  62.8,  19323,  19.0, 21.9, 2.8,  8.3,  None),
    ("BGRIM",  "B.Grimm Power Pcl",              "Utilities",        "BUY",     6.45,  14.00,  None,  36497,  44.8, 19.0, 4.7,  6.9,  None),
    ("BPP",    "Banpu Power Pcl",                "Utilities",        "SELL",   11.50,  11.50, 119.3,  35049,   8.0, 12.0, 5.2,  8.5,  None),
    ("CKP",    "CK Power Pcl",                   "Utilities",        "BUY",     2.28,   5.00, -52.2,  18535,   8.1,  8.8, 3.9,  7.5,  None),
    ("EA",     "Energy Absolute Pcl",            "Utilities",        "SELL",    3.14,   1.50,  None,  23320,   6.0,  6.3, None, 5.7,  None),
    ("EGCO",   "Electricity Generating Pcl",     "Utilities",        "BUY",   115.00, 130.00,  13.0, 110674,  21.0, 25.8, 5.7,  8.7,  None),
    ("GPSC",   "Global Power Synergy Pcl",       "Utilities",        "BUY",    39.25,  43.00,   9.6,  60543,   6.5, 11.7, 3.8,  5.0,  None),
    ("GULF",   "Gulf Energy Dev. Pcl",           "Utilities",        "BUY",    62.75,  75.00, -31.8, 937475,  26.8, 43.8, 2.2, 10.1,  None),
    ("GUNKUL", "Gunkul Engineering Dev. Pcl",    "Utilities",        "BUY",    29.75,  35.00,  19.5,  35175,  18.5, 16.0, 3.0, 13.1,  None),
    ("RATCH",  "RATCH Group Pcl",                "Utilities",        "BUY",     3.96,   2.70,  17.6,  64706,   9.6, 14.6, 5.4,  7.1,  None),
    ("WHAUP",  "WHA Utilities & Power Pcl",      "Utilities",        "BUY",     5.95,   6.50,   9.3,  22759,  19.7, 23.2, 4.2,  8.5,  None),
    # Asset Funds
    ("3BBIF",  "3BB Internet Infrastructure Fund","Asset Funds",     "BUY",    12.70,  12.50,  11.6,  14123,  10.3, 15.8, 9.0, 21.6,  None),
    ("BTSGIF", "BTS Rail Mass Transit Growth Fund","Asset Funds",    "HOLD",    6.45,   7.20,  -1.6,  51600,   7.9,  7.9, 9.2, 10.5,  None),
    ("CPNREIT","CPN Retail Growth Leasehold REIT","Asset Funds",     "BUY",     2.44,   2.60,   6.6,  45988,   3.0,  3.0, None, 9.3,  None),
    ("DIF",    "Digital Telecom Infra Fund",     "Asset Funds",      "BUY",    10.10,  10.50,   4.0, 107380,   8.9,  9.1, 8.9,  7.2,  None),
]

COLS = ["ticker","company","sector","rec","price","target","upside",
        "mktcap","pe_26f","ev_26f","yield_26f","roe_26f","pbv_26f"]

REC_COLOR = {"BUY": "#00cc66", "HOLD": "#f0a500", "SELL": "#ff4444"}
REC_BG    = {"BUY": "#e6fff2", "HOLD": "#fff8e6", "SELL": "#ffe6e6"}

# ── Data loading ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=86400)   # refresh daily
def load_from_gsheets(url: str) -> pd.DataFrame | None:
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
        return df
    except Exception:
        return None

def load_data() -> tuple[pd.DataFrame, str]:
    gsheet_url = _get_secret("VALUATION_GSHEET_CSV_URL")
    if gsheet_url:
        df = load_from_gsheets(gsheet_url)
        if df is not None and not df.empty:
            return df, "Google Sheets"
    df = pd.DataFrame(RAW_STOCKS, columns=COLS)
    return df, "static (2026-06-11)"

# ── Sidebar ─────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Filters")

    gsheet_url = _get_secret("VALUATION_GSHEET_CSV_URL")
    if gsheet_url:
        st.success("📡 ดึงข้อมูลจาก Google Sheets (รีเฟรชทุก 24 ชม.)")
    else:
        st.info(
            "ตั้งค่า `VALUATION_GSHEET_CSV_URL` ใน secrets.toml\n"
            "เพื่ออัปเดตข้อมูลอัตโนมัติทุกวัน"
        )

    st.markdown("---")

    df_full, data_source = load_data()

    sectors = ["ทั้งหมด"] + sorted(df_full["sector"].unique().tolist())
    sel_sector = st.selectbox("Sector", sectors)

    rec_opts = st.multiselect("Rating", ["BUY", "HOLD", "SELL"], default=["BUY", "HOLD", "SELL"])

    upside_range = st.slider(
        "Upside/Downside (%)",
        min_value=-60.0, max_value=120.0, value=(-60.0, 120.0), step=1.0
    )

    st.markdown("---")
    if st.button("🔄 รีเฟรชข้อมูล", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"ข้อมูล: {data_source}")
    st.caption(f"อัปเดต: 11 มิ.ย. 2569")

# ── Filter ──────────────────────────────────────────────────────────────────────

df = df_full.copy()
if sel_sector != "ทั้งหมด":
    df = df[df["sector"] == sel_sector]
if rec_opts:
    df = df[df["rec"].isin(rec_opts)]
df = df[
    df["upside"].isna() |
    ((df["upside"] >= upside_range[0]) & (df["upside"] <= upside_range[1]))
]

# ── Header ──────────────────────────────────────────────────────────────────────

st.title("📊 SET50 Valuation Dashboard")
st.caption(f"Valuation Sheet · {datetime.now().strftime('%d %b %Y')} · ข้อมูล: {data_source}")
st.markdown("---")

# ── KPI cards ───────────────────────────────────────────────────────────────────

total     = len(df)
n_buy     = (df["rec"] == "BUY").sum()
n_hold    = (df["rec"] == "HOLD").sum()
n_sell    = (df["rec"] == "SELL").sum()
avg_up    = df["upside"].mean()
mktcap_t  = df_full["mktcap"].sum() / 1_000_000  # Bt trillion

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("หุ้นทั้งหมด",     f"{total} ตัว")
c2.metric("🟢 BUY",          f"{n_buy} ตัว",  delta=None)
c3.metric("🟡 HOLD",         f"{n_hold} ตัว")
c4.metric("🔴 SELL",         f"{n_sell} ตัว")
c5.metric("Avg Upside",       f"{avg_up:.1f}%" if not pd.isna(avg_up) else "N/A")
c6.metric("Mkt Cap (SET)",    f"{mktcap_t:.1f}T Bt")

st.markdown("---")

# ── Charts row ──────────────────────────────────────────────────────────────────

chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    st.subheader("📈 Upside/Downside ทุกตัว")
    df_chart = df.dropna(subset=["upside"]).sort_values("upside", ascending=False)
    if not df_chart.empty:
        fig_bar = px.bar(
            df_chart,
            x="ticker", y="upside",
            color="rec",
            color_discrete_map=REC_COLOR,
            hover_data=["company", "price", "target", "upside"],
            labels={"upside": "Upside (%)", "ticker": ""},
            height=380,
        )
        fig_bar.update_layout(
            showlegend=True,
            legend_title_text="Rating",
            yaxis=dict(zeroline=True, zerolinecolor="gray", zerolinewidth=1),
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-45,
        )
        fig_bar.add_hline(y=0, line_color="gray", line_dash="dash", line_width=1)
        st.plotly_chart(fig_bar, use_container_width=True)

with chart_col2:
    st.subheader("🥧 Rating Distribution")
    rec_counts = df["rec"].value_counts().reset_index()
    rec_counts.columns = ["rec", "count"]
    fig_pie = px.pie(
        rec_counts, names="rec", values="count",
        color="rec",
        color_discrete_map=REC_COLOR,
        hole=0.45,
        height=380,
    )
    fig_pie.update_traces(textinfo="label+percent+value")
    fig_pie.update_layout(showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Scatter: PE vs Upside ────────────────────────────────────────────────────────

st.subheader("🔍 PE 2026F vs Upside (Bubble = Market Cap)")
df_scatter = df.dropna(subset=["pe_26f", "upside"]).copy()
df_scatter = df_scatter[df_scatter["pe_26f"] < 80]  # exclude extreme outliers
if not df_scatter.empty:
    fig_sc = px.scatter(
        df_scatter,
        x="pe_26f", y="upside",
        size="mktcap",
        color="rec",
        color_discrete_map=REC_COLOR,
        hover_name="ticker",
        hover_data={"company": True, "sector": True, "price": True,
                    "target": True, "mktcap": ":,.0f"},
        labels={"pe_26f": "PE 2026F (x)", "upside": "Upside (%)", "mktcap": "Market Cap (Bt m)"},
        size_max=50,
        height=420,
        text="ticker",
    )
    fig_sc.update_traces(textposition="top center", textfont_size=9)
    fig_sc.add_hline(y=0, line_color="gray", line_dash="dash")
    fig_sc.update_layout(plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_sc, use_container_width=True)

# ── Sector heatmap ───────────────────────────────────────────────────────────────

st.subheader("🏭 Sector Breakdown")
sector_stats = df_full.groupby("sector").agg(
    total=("ticker", "count"),
    buy=("rec", lambda x: (x == "BUY").sum()),
    hold=("rec", lambda x: (x == "HOLD").sum()),
    sell=("rec", lambda x: (x == "SELL").sum()),
    avg_upside=("upside", "mean"),
    total_mktcap=("mktcap", "sum"),
).reset_index().sort_values("total_mktcap", ascending=False)

sec_col1, sec_col2 = st.columns([3, 2])

with sec_col1:
    # Stacked bar per sector
    sec_melt = sector_stats.melt(
        id_vars="sector", value_vars=["buy", "hold", "sell"],
        var_name="rating", value_name="count"
    )
    sec_melt["rating"] = sec_melt["rating"].str.upper()
    fig_sec = px.bar(
        sec_melt, x="sector", y="count", color="rating",
        color_discrete_map=REC_COLOR,
        barmode="stack",
        labels={"count": "# Stocks", "sector": "", "rating": "Rating"},
        height=360,
    )
    fig_sec.update_layout(xaxis_tickangle=-30, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_sec, use_container_width=True)

with sec_col2:
    sector_display = sector_stats[["sector","total","buy","hold","sell","avg_upside"]].copy()
    sector_display["avg_upside"] = sector_display["avg_upside"].map(
        lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
    )
    sector_display.columns = ["Sector","Total","BUY","HOLD","SELL","Avg Upside"]
    st.dataframe(sector_display, use_container_width=True, hide_index=True, height=360)

# ── Main table ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("📋 ตารางข้อมูลทั้งหมด")

sort_by  = st.selectbox("เรียงตาม", ["upside","pe_26f","yield_26f","roe_26f","mktcap"], index=0)
sort_asc = st.toggle("เรียงน้อย→มาก", value=False)

df_show = df.sort_values(sort_by, ascending=sort_asc, na_position="last")

def color_rec(val):
    c = REC_COLOR.get(val, "#ccc")
    bg = REC_BG.get(val, "#fff")
    return f"background-color:{bg};color:{c};font-weight:bold;border-radius:4px"

def color_upside(val):
    try:
        v = float(val.rstrip("%"))
        if v > 10:  return "color:#00aa44;font-weight:bold"
        if v < 0:   return "color:#cc2222;font-weight:bold"
        return "color:#cc8800"
    except:
        return ""

# Format display columns
df_display = df_show[[
    "ticker","company","sector","rec",
    "price","target","upside",
    "pe_26f","ev_26f","yield_26f","roe_26f","mktcap"
]].copy()
df_display.columns = [
    "Ticker","Company","Sector","Rating",
    "Price (Bt)","Target (Bt)","Upside %",
    "PE 26F (x)","EV/EBITDA 26F","Yield 26F %","ROE 26F %","Mkt Cap (Bt m)"
]
df_display["Upside %"]     = df_display["Upside %"].map(lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A")
df_display["Yield 26F %"]  = df_display["Yield 26F %"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
df_display["ROE 26F %"]    = df_display["ROE 26F %"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
df_display["PE 26F (x)"]   = df_display["PE 26F (x)"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
df_display["EV/EBITDA 26F"]= df_display["EV/EBITDA 26F"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
df_display["Mkt Cap (Bt m)"]= df_display["Mkt Cap (Bt m)"].map(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")

styled = (
    df_display.style
    .applymap(color_rec, subset=["Rating"])
    .applymap(color_upside, subset=["Upside %"])
    .set_properties(**{"font-size": "13px"})
)
st.dataframe(styled, use_container_width=True, hide_index=True, height=520)

# ── BUY highlights ──────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("🌟 Top BUY Picks — Highest Upside")
top_buys = (
    df_full[df_full["rec"] == "BUY"]
    .dropna(subset=["upside"])
    .nlargest(8, "upside")
)
cols = st.columns(min(4, len(top_buys)))
for i, (_, row) in enumerate(top_buys.iterrows()):
    with cols[i % 4]:
        st.markdown(
            f"""<div style='background:#f0fff7;border:1.5px solid #00cc66;
                border-radius:10px;padding:12px 14px;margin-bottom:12px'>
                <div style='font-size:18px;font-weight:700;color:#008844'>{row.ticker}</div>
                <div style='font-size:12px;color:#555;margin-bottom:4px'>{row.company[:28]}</div>
                <div style='font-size:13px'><b>฿{row.price:.2f}</b>
                    → <b>฿{row.target:.2f}</b></div>
                <div style='font-size:16px;font-weight:700;color:#00aa44'>
                    ▲ {row.upside:.1f}%</div>
                <div style='font-size:11px;color:#888'>{row.sector}</div>
            </div>""",
            unsafe_allow_html=True
        )

st.markdown("---")
st.caption("📌 ข้อมูลนี้เป็นเพียงการวิเคราะห์เพื่อการศึกษา ไม่ใช่คำแนะนำการลงทุน")
