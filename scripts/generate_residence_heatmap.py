#!/usr/bin/env python3
"""
Analyze geographic distribution of JETAASC subscribers
Parses Address field to extract zip codes and creates bubble map visualization
"""

import csv
import re
from collections import Counter
import json
import argparse
import os

# US state abbreviations
STATE_ABBREV = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
}

# Approximate coordinates for CA zip code prefixes (first 3 digits) and other areas
# Format: prefix -> (lat, lng, area_name)
ZIP_COORDS = {
    # Los Angeles area - detailed
    '900': (34.0522, -118.2437, 'Downtown LA'),
    '901': (33.9425, -118.2551, 'Inglewood/South LA'),
    '902': (33.8153, -118.3518, 'Torrance/South Bay'),
    '903': (33.8958, -118.2201, 'Compton/Lynwood'),
    '904': (33.9017, -118.0818, 'Cerritos/Norwalk'),
    '905': (33.7701, -118.1937, 'Long Beach'),
    '906': (33.7879, -118.1489, 'Long Beach East'),
    '907': (33.7975, -118.3223, 'San Pedro/Harbor'),
    '908': (33.7959, -118.1052, 'Lakewood/Hawaiian Gardens'),
    '910': (34.1808, -118.3090, 'Glendale/Burbank'),
    '911': (34.1425, -118.2551, 'Glendale/Eagle Rock'),
    '912': (34.1478, -118.1445, 'Pasadena'),
    '913': (34.1064, -118.0415, 'Arcadia/Monrovia'),
    '914': (34.0689, -117.9391, 'San Dimas/La Verne'),
    '915': (34.0966, -117.7198, 'Pomona/Claremont'),
    '916': (34.0195, -118.1517, 'Alhambra/Monterey Park'),
    '917': (34.0633, -118.2275, 'East LA/City Terrace'),
    '918': (34.0901, -117.8903, 'West Covina/Covina'),
    '919': (34.1478, -117.8648, 'Azusa/Glendora'),
    '920': (32.7157, -117.1611, 'San Diego Central'),
    '921': (32.8328, -117.1713, 'San Diego North'),
    '922': (33.1959, -117.3795, 'Oceanside/Carlsbad'),
    '923': (33.0114, -117.0917, 'Escondido/San Marcos'),
    '924': (32.6401, -117.0842, 'Chula Vista/National City'),
    '925': (32.7940, -116.9625, 'El Cajon/La Mesa'),
    '926': (33.6846, -117.8265, 'Irvine/Lake Forest'),
    '927': (33.7175, -117.8311, 'Santa Ana/Orange'),
    '928': (33.8366, -117.9143, 'Anaheim/Fullerton'),
    '930': (34.9530, -120.4357, 'Santa Maria'),
    '931': (34.4208, -119.6982, 'Santa Barbara'),
    '932': (35.3733, -119.0187, 'Bakersfield'),
    '933': (35.3733, -119.0187, 'Bakersfield'),
    '934': (36.7378, -119.7871, 'Fresno'),
    '935': (36.7378, -119.7871, 'Fresno'),
    '936': (36.7378, -119.7871, 'Fresno'),
    '937': (36.6002, -121.8947, 'Monterey/Salinas'),
    '939': (37.3382, -121.8863, 'San Jose'),
    '940': (37.7749, -122.4194, 'San Francisco'),
    '941': (37.7749, -122.4194, 'San Francisco'),
    '942': (37.8044, -122.2712, 'Oakland'),
    '943': (37.5485, -122.0590, 'Fremont/Hayward'),
    '944': (37.8716, -122.2727, 'Berkeley'),
    '945': (37.8044, -122.2712, 'Oakland'),
    '946': (37.9577, -122.3470, 'Richmond/El Cerrito'),
    '947': (37.9577, -122.3470, 'Contra Costa'),
    '948': (37.9577, -122.3470, 'Contra Costa'),
    '949': (37.9735, -122.5311, 'Marin County'),
    '950': (37.3382, -121.8863, 'San Jose'),
    '951': (33.9533, -117.3962, 'Riverside'),
    '952': (33.9533, -117.3962, 'Riverside'),
    '953': (34.0922, -117.4350, 'San Bernardino'),
    '954': (34.5362, -117.2928, 'Victorville/High Desert'),
    '955': (40.5865, -122.3917, 'Redding'),
    '956': (38.5816, -121.4944, 'Sacramento'),
    '957': (38.5816, -121.4944, 'Sacramento'),
    '958': (38.5816, -121.4944, 'Sacramento'),
    '959': (38.5816, -121.4944, 'Sacramento'),
    '960': (40.8021, -124.1637, 'Eureka'),
    # LA neighborhoods by specific zips
    '90004': (34.0764, -118.3090, 'Los Feliz'),
    '90005': (34.0594, -118.3011, 'Koreatown'),
    '90006': (34.0478, -118.2946, 'Pico-Union'),
    '90007': (34.0259, -118.2838, 'USC/South LA'),
    '90008': (34.0106, -118.3401, 'Baldwin Hills'),
    '90010': (34.0620, -118.3152, 'Mid-Wilshire'),
    '90012': (34.0622, -118.2406, 'Chinatown/Civic Center'),
    '90013': (34.0407, -118.2468, 'Downtown LA'),
    '90014': (34.0407, -118.2533, 'Fashion District'),
    '90015': (34.0370, -118.2654, 'South Park'),
    '90016': (34.0281, -118.3520, 'West Adams'),
    '90017': (34.0522, -118.2602, 'Downtown West'),
    '90018': (34.0281, -118.3178, 'Jefferson Park'),
    '90019': (34.0478, -118.3401, 'Mid-City'),
    '90020': (34.0667, -118.3090, 'Koreatown North'),
    '90024': (34.0633, -118.4298, 'Westwood'),
    '90025': (34.0411, -118.4476, 'West LA'),
    '90026': (34.0781, -118.2606, 'Echo Park'),
    '90027': (34.1017, -118.2937, 'Los Feliz/Griffith'),
    '90028': (34.1017, -118.3287, 'Hollywood'),
    '90029': (34.0900, -118.2937, 'Thai Town'),
    '90031': (34.0781, -118.2106, 'Lincoln Heights'),
    '90032': (34.0781, -118.1756, 'El Sereno'),
    '90033': (34.0481, -118.2106, 'Boyle Heights'),
    '90034': (34.0281, -118.3970, 'Palms/Cheviot Hills'),
    '90035': (34.0533, -118.3720, 'Miracle Mile'),
    '90036': (34.0700, -118.3520, 'Park La Brea'),
    '90038': (34.0900, -118.3287, 'Hollywood'),
    '90039': (34.1117, -118.2606, 'Silver Lake'),
    '90041': (34.1367, -118.2106, 'Eagle Rock'),
    '90042': (34.1117, -118.1906, 'Highland Park'),
    '90043': (33.9906, -118.3401, 'View Park'),
    '90044': (33.9531, -118.2901, 'Athens'),
    '90045': (33.9581, -118.3970, 'Westchester'),
    '90046': (34.1117, -118.3670, 'West Hollywood'),
    '90047': (33.9531, -118.3178, 'South LA'),
    '90048': (34.0750, -118.3720, 'Beverly Grove'),
    '90049': (34.0781, -118.4726, 'Brentwood'),
    '90056': (33.9906, -118.3720, 'Ladera Heights'),
    '90057': (34.0594, -118.2751, 'Westlake'),
    '90058': (33.9906, -118.2106, 'Vernon'),
    '90059': (33.9281, -118.2456, 'Watts'),
    '90061': (33.9206, -118.2751, 'South LA'),
    '90062': (34.0031, -118.3090, 'South LA'),
    '90063': (34.0481, -118.1856, 'East LA'),
    '90064': (34.0281, -118.4226, 'Rancho Park'),
    '90065': (34.1117, -118.2256, 'Cypress Park'),
    '90066': (34.0031, -118.4326, 'Mar Vista'),
    '90067': (34.0533, -118.4126, 'Century City'),
    '90068': (34.1267, -118.3287, 'Hollywood Hills'),
    '90069': (34.0900, -118.3820, 'West Hollywood'),
    '90071': (34.0522, -118.2537, 'DTLA Financial'),
    '90077': (34.1017, -118.4476, 'Bel Air'),
    '90094': (33.9781, -118.4476, 'Playa Vista'),
    '90210': (34.0901, -118.4065, 'Beverly Hills'),
    '90211': (34.0656, -118.3865, 'Beverly Hills'),
    '90212': (34.0578, -118.4015, 'Beverly Hills'),
    '90230': (34.0028, -118.3920, 'Culver City'),
    '90232': (34.0203, -118.3970, 'Culver City'),
    '90247': (33.8911, -118.2901, 'Gardena'),
    '90248': (33.8786, -118.3070, 'Gardena'),
    '90249': (33.9036, -118.3178, 'Gardena'),
    '90250': (33.9161, -118.3520, 'Hawthorne'),
    '90260': (33.8911, -118.3520, 'Lawndale'),
    '90266': (33.8836, -118.4076, 'Manhattan Beach'),
    '90274': (33.7578, -118.3870, 'Palos Verdes'),
    '90275': (33.7453, -118.3620, 'Rancho Palos Verdes'),
    '90277': (33.8286, -118.3870, 'Redondo Beach'),
    '90278': (33.8661, -118.3770, 'Redondo Beach'),
    '90291': (33.9956, -118.4726, 'Venice'),
    '90292': (33.9706, -118.4526, 'Marina del Rey'),
    '90293': (33.9581, -118.4576, 'Playa del Rey'),
    '90301': (33.9506, -118.3520, 'Inglewood'),
    '90302': (33.9631, -118.3401, 'Inglewood'),
    '90303': (33.9381, -118.3287, 'Inglewood'),
    '90304': (33.9256, -118.3620, 'Lennox'),
    '90401': (34.0195, -118.4916, 'Santa Monica'),
    '90402': (34.0370, -118.5016, 'Santa Monica'),
    '90403': (34.0295, -118.4866, 'Santa Monica'),
    '90404': (34.0295, -118.4716, 'Santa Monica'),
    '90405': (34.0045, -118.4766, 'Santa Monica'),
    '90501': (33.8286, -118.3070, 'Torrance'),
    '90502': (33.8411, -118.2951, 'Torrance'),
    '90503': (33.8411, -118.3401, 'Torrance'),
    '90504': (33.8661, -118.3287, 'Torrance'),
    '90505': (33.8161, -118.3520, 'Torrance'),
    '90601': (33.9756, -118.0567, 'Whittier'),
    '90602': (33.9631, -118.0317, 'Whittier'),
    '90603': (33.9381, -117.9967, 'Whittier'),
    '90604': (33.9256, -118.0067, 'Whittier'),
    '90605': (33.9381, -118.0317, 'Whittier'),
    '90606': (33.9756, -118.0967, 'Whittier'),
    '90620': (33.8536, -118.0117, 'Buena Park'),
    '90621': (33.8786, -117.9967, 'Buena Park'),
    '90630': (33.8036, -118.0617, 'Cypress'),
    '90631': (33.9131, -117.9517, 'La Habra'),
    '90638': (33.8911, -118.0517, 'La Mirada'),
    '90640': (34.0031, -118.1006, 'Montebello'),
    '90650': (33.9131, -118.0817, 'Norwalk'),
    '90660': (33.9881, -118.0667, 'Pico Rivera'),
    '90670': (33.8661, -118.0817, 'Santa Fe Springs'),
    '90680': (33.7786, -117.9817, 'Stanton'),
    '90701': (33.8661, -118.0567, 'Artesia'),
    '90703': (33.8661, -118.0317, 'Cerritos'),
    '90706': (33.8911, -118.1317, 'Bellflower'),
    '90710': (33.7911, -118.2651, 'Harbor City'),
    '90712': (33.8536, -118.1417, 'Lakewood'),
    '90713': (33.8411, -118.1167, 'Lakewood'),
    '90715': (33.8411, -118.0717, 'Lakewood'),
    '90716': (33.8286, -118.0567, 'Hawaiian Gardens'),
    '90717': (33.8036, -118.2901, 'Lomita'),
    '90720': (33.7911, -118.0767, 'Los Alamitos'),
    '90731': (33.7411, -118.2801, 'San Pedro'),
    '90732': (33.7536, -118.3120, 'San Pedro'),
    '90740': (33.7536, -118.0767, 'Seal Beach'),
    '90744': (33.7911, -118.2651, 'Wilmington'),
    '90745': (33.8161, -118.2651, 'Carson'),
    '90746': (33.8536, -118.2551, 'Carson'),
    '90802': (33.7661, -118.1867, 'Long Beach Downtown'),
    '90803': (33.7536, -118.1367, 'Long Beach Belmont'),
    '90804': (33.7786, -118.1517, 'Long Beach'),
    '90805': (33.8661, -118.1867, 'Long Beach North'),
    '90806': (33.7911, -118.1867, 'Long Beach'),
    '90807': (33.8286, -118.1867, 'Long Beach'),
    '90808': (33.8286, -118.1117, 'Long Beach East'),
    '90810': (33.8161, -118.2201, 'Long Beach West'),
    '90813': (33.7786, -118.1817, 'Long Beach'),
    '90814': (33.7661, -118.1517, 'Long Beach Belmont'),
    '90815': (33.7911, -118.1117, 'Long Beach'),
    '91001': (34.2017, -118.1306, 'Altadena'),
    '91006': (34.1367, -118.0256, 'Arcadia'),
    '91007': (34.1242, -118.0456, 'Arcadia'),
    '91010': (34.1367, -117.9556, 'Duarte'),
    '91011': (34.2142, -118.2006, 'La Cañada'),
    '91016': (34.1617, -117.9956, 'Monrovia'),
    '91020': (34.2267, -118.2406, 'Montrose'),
    '91024': (34.1742, -118.0556, 'Sierra Madre'),
    '91030': (34.1117, -118.1556, 'South Pasadena'),
    '91040': (34.2517, -118.2906, 'Sunland'),
    '91042': (34.2642, -118.2256, 'Tujunga'),
    '91101': (34.1478, -118.1445, 'Pasadena'),
    '91103': (34.1728, -118.1545, 'Pasadena'),
    '91104': (34.1603, -118.1245, 'Pasadena'),
    '91105': (34.1353, -118.1595, 'Pasadena'),
    '91106': (34.1353, -118.1245, 'Pasadena'),
    '91107': (34.1478, -118.0795, 'Pasadena'),
    '91108': (34.1228, -118.0995, 'San Marino'),
    '91201': (34.1617, -118.2906, 'Glendale'),
    '91202': (34.1617, -118.2656, 'Glendale'),
    '91203': (34.1492, -118.2556, 'Glendale'),
    '91204': (34.1367, -118.2556, 'Glendale'),
    '91205': (34.1367, -118.2306, 'Glendale'),
    '91206': (34.1617, -118.2206, 'Glendale'),
    '91207': (34.1867, -118.2606, 'Glendale'),
    '91208': (34.1992, -118.2306, 'Glendale'),
    '91214': (34.2267, -118.2556, 'La Crescenta'),
    '91301': (34.1367, -118.7556, 'Agoura Hills'),
    '91302': (34.1367, -118.6756, 'Calabasas'),
    '91303': (34.2017, -118.6006, 'Canoga Park'),
    '91304': (34.2267, -118.6006, 'Canoga Park'),
    '91306': (34.2017, -118.5556, 'Winnetka'),
    '91307': (34.1867, -118.6506, 'West Hills'),
    '91311': (34.2642, -118.5706, 'Chatsworth'),
    '91316': (34.1617, -118.5156, 'Encino'),
    '91321': (34.3892, -118.5506, 'Newhall'),
    '91324': (34.2392, -118.5406, 'Northridge'),
    '91325': (34.2517, -118.5056, 'Northridge'),
    '91326': (34.2767, -118.5556, 'Northridge'),
    '91330': (34.2392, -118.5256, 'Northridge'),
    '91331': (34.2767, -118.4256, 'Pacoima'),
    '91335': (34.2017, -118.4706, 'Reseda'),
    '91340': (34.2892, -118.4406, 'San Fernando'),
    '91342': (34.3142, -118.4256, 'Sylmar'),
    '91343': (34.2267, -118.4556, 'North Hills'),
    '91344': (34.2892, -118.5256, 'Granada Hills'),
    '91345': (34.2642, -118.4706, 'Mission Hills'),
    '91350': (34.4267, -118.5356, 'Santa Clarita'),
    '91351': (34.4017, -118.4756, 'Canyon Country'),
    '91352': (34.2267, -118.3256, 'Sun Valley'),
    '91354': (34.4517, -118.5606, 'Valencia'),
    '91355': (34.4142, -118.5606, 'Valencia'),
    '91356': (34.1742, -118.5456, 'Tarzana'),
    '91360': (34.1867, -118.8656, 'Thousand Oaks'),
    '91361': (34.1367, -118.8156, 'Westlake Village'),
    '91362': (34.1617, -118.8406, 'Thousand Oaks'),
    '91364': (34.1617, -118.5806, 'Woodland Hills'),
    '91367': (34.1742, -118.6006, 'Woodland Hills'),
    '91377': (34.1492, -118.7756, 'Oak Park'),
    '91381': (34.4017, -118.5756, 'Stevenson Ranch'),
    '91384': (34.4767, -118.6006, 'Castaic'),
    '91401': (34.1867, -118.4256, 'Van Nuys'),
    '91402': (34.2267, -118.4106, 'Panorama City'),
    '91403': (34.1492, -118.4506, 'Sherman Oaks'),
    '91405': (34.2017, -118.4256, 'Van Nuys'),
    '91406': (34.2017, -118.4906, 'Van Nuys'),
    '91411': (34.1867, -118.4506, 'Van Nuys'),
    '91423': (34.1492, -118.4256, 'Sherman Oaks'),
    '91436': (34.1617, -118.4706, 'Encino'),
    '91501': (34.1867, -118.3256, 'Burbank'),
    '91502': (34.1742, -118.3156, 'Burbank'),
    '91504': (34.2142, -118.3256, 'Burbank'),
    '91505': (34.1867, -118.3556, 'Burbank'),
    '91506': (34.1742, -118.3406, 'Burbank'),
    '91601': (34.1742, -118.3806, 'North Hollywood'),
    '91602': (34.1617, -118.3606, 'North Hollywood'),
    '91604': (34.1492, -118.3906, 'Studio City'),
    '91605': (34.2017, -118.3906, 'North Hollywood'),
    '91606': (34.1867, -118.3906, 'North Hollywood'),
    '91607': (34.1617, -118.4006, 'Valley Village'),
    '91608': (34.1367, -118.3656, 'Universal City'),
    '91702': (34.1117, -117.8856, 'Azusa'),
    '91706': (34.0831, -117.9517, 'Baldwin Park'),
    '91709': (34.0206, -117.7617, 'Chino Hills'),
    '91710': (34.0031, -117.6867, 'Chino'),
    '91711': (34.0956, -117.7117, 'Claremont'),
    '91722': (34.0956, -117.9317, 'Covina'),
    '91723': (34.0831, -117.8867, 'Covina'),
    '91724': (34.1081, -117.8567, 'Covina'),
    '91730': (34.1206, -117.5717, 'Rancho Cucamonga'),
    '91731': (34.0831, -118.0506, 'El Monte'),
    '91732': (34.0581, -118.0256, 'El Monte'),
    '91733': (34.0456, -118.0717, 'South El Monte'),
    '91740': (34.1206, -117.8067, 'Glendora'),
    '91741': (34.1456, -117.8267, 'Glendora'),
    '91744': (34.0331, -117.9417, 'La Puente'),
    '91745': (34.0081, -117.9767, 'Hacienda Heights'),
    '91746': (34.0456, -117.9717, 'La Puente'),
    '91748': (33.9906, -117.9117, 'Rowland Heights'),
    '91750': (34.1081, -117.7717, 'La Verne'),
    '91754': (34.0456, -118.1256, 'Monterey Park'),
    '91755': (34.0581, -118.1456, 'Monterey Park'),
    '91761': (34.0456, -117.5917, 'Ontario'),
    '91762': (34.0706, -117.6217, 'Ontario'),
    '91763': (34.0706, -117.6867, 'Montclair'),
    '91764': (34.0706, -117.5617, 'Ontario'),
    '91765': (34.0206, -117.8267, 'Diamond Bar'),
    '91766': (34.0581, -117.7517, 'Pomona'),
    '91767': (34.0831, -117.7317, 'Pomona'),
    '91768': (34.0581, -117.6867, 'Pomona'),
    '91770': (34.0706, -118.0756, 'Rosemead'),
    '91773': (34.1206, -117.8467, 'San Dimas'),
    '91775': (34.1081, -118.1056, 'San Gabriel'),
    '91776': (34.0956, -118.0806, 'San Gabriel'),
    '91780': (34.1206, -118.0256, 'Temple City'),
    '91784': (34.1456, -117.6917, 'Upland'),
    '91786': (34.1206, -117.6317, 'Upland'),
    '91789': (34.0206, -117.8667, 'Walnut'),
    '91790': (34.0456, -117.9117, 'West Covina'),
    '91791': (34.0706, -117.9067, 'West Covina'),
    '91792': (34.0206, -117.9067, 'West Covina'),
    '91801': (34.0956, -118.1256, 'Alhambra'),
    '91803': (34.0706, -118.1506, 'Alhambra'),
    # Arizona
    '850': (33.4484, -112.0740, 'Phoenix'),
    '851': (33.4484, -112.0740, 'Phoenix'),
    '852': (33.4152, -111.8315, 'Mesa/Tempe'),
    '853': (33.3062, -111.8413, 'Chandler/Gilbert'),
    '856': (32.2226, -110.9747, 'Tucson'),
    '857': (32.2226, -110.9747, 'Tucson'),
    '859': (34.8697, -111.7610, 'Flagstaff/Sedona'),
    '860': (33.4942, -111.9261, 'Scottsdale'),
    '863': (33.6189, -112.3679, 'Glendale/Peoria'),
    # San Diego specific
    '92101': (32.7197, -117.1628, 'Downtown SD'),
    '92102': (32.7097, -117.1228, 'Golden Hill'),
    '92103': (32.7497, -117.1628, 'Hillcrest'),
    '92104': (32.7497, -117.1228, 'North Park'),
    '92105': (32.7397, -117.0828, 'City Heights'),
    '92106': (32.7197, -117.2328, 'Point Loma'),
    '92107': (32.7397, -117.2528, 'Ocean Beach'),
    '92108': (32.7697, -117.1328, 'Mission Valley'),
    '92109': (32.7897, -117.2528, 'Pacific Beach'),
    '92110': (32.7597, -117.2028, 'Morena/Bay Park'),
    '92111': (32.8097, -117.1628, 'Clairemont'),
    '92113': (32.6897, -117.1228, 'Logan Heights'),
    '92114': (32.6997, -117.0528, 'Encanto'),
    '92115': (32.7597, -117.0628, 'College Area'),
    '92116': (32.7597, -117.1228, 'Normal Heights'),
    '92117': (32.8297, -117.2028, 'Clairemont Mesa'),
    '92118': (32.6797, -117.1828, 'Coronado'),
    '92119': (32.7997, -117.0228, 'San Carlos'),
    '92120': (32.7897, -117.0628, 'Grantville'),
    '92121': (32.9097, -117.2028, 'Sorrento Valley'),
    '92122': (32.8597, -117.2128, 'University City'),
    '92123': (32.8097, -117.1228, 'Kearny Mesa'),
    '92124': (32.8297, -117.0928, 'Tierrasanta'),
    '92126': (32.9097, -117.1428, 'Mira Mesa'),
    '92127': (33.0197, -117.0828, 'Rancho Bernardo'),
    '92128': (33.0197, -117.0528, 'Rancho Bernardo'),
    '92129': (32.9697, -117.1228, 'Rancho Peñasquitos'),
    '92130': (32.9597, -117.2228, 'Carmel Valley'),
    '92131': (32.9297, -117.0828, 'Scripps Ranch'),
    '92134': (32.7297, -117.1428, 'Naval Medical'),
    '92136': (32.6797, -117.1228, 'Naval Station'),
    '92139': (32.6697, -117.0528, 'Paradise Hills'),
    '92154': (32.5797, -117.0728, 'Otay Mesa'),
    # Orange County specific
    '92602': (33.7397, -117.7928, 'Irvine'),
    '92603': (33.6297, -117.7828, 'Irvine'),
    '92604': (33.6897, -117.8228, 'Irvine'),
    '92606': (33.6997, -117.8428, 'Irvine'),
    '92612': (33.6597, -117.8328, 'Irvine'),
    '92614': (33.6797, -117.8628, 'Irvine'),
    '92617': (33.6397, -117.8428, 'Irvine'),
    '92618': (33.6497, -117.7428, 'Irvine'),
    '92620': (33.7097, -117.7628, 'Irvine'),
    '92626': (33.6897, -117.9028, 'Costa Mesa'),
    '92627': (33.6497, -117.9228, 'Costa Mesa'),
    '92629': (33.4597, -117.6628, 'Dana Point'),
    '92630': (33.6397, -117.6728, 'Lake Forest'),
    '92637': (33.6097, -117.7028, 'Laguna Woods'),
    '92646': (33.6597, -117.9728, 'Huntington Beach'),
    '92647': (33.7197, -117.9928, 'Huntington Beach'),
    '92648': (33.6897, -117.9728, 'Huntington Beach'),
    '92649': (33.7297, -118.0428, 'Huntington Beach'),
    '92651': (33.5497, -117.7828, 'Laguna Beach'),
    '92653': (33.5997, -117.6928, 'Laguna Hills'),
    '92655': (33.6997, -117.9428, 'Midway City'),
    '92656': (33.5897, -117.7128, 'Aliso Viejo'),
    '92657': (33.5997, -117.8528, 'Newport Coast'),
    '92660': (33.6297, -117.8928, 'Newport Beach'),
    '92661': (33.6097, -117.8928, 'Newport Beach'),
    '92662': (33.6097, -117.9128, 'Newport Beach'),
    '92663': (33.6197, -117.9328, 'Newport Beach'),
    '92672': (33.4297, -117.6228, 'San Clemente'),
    '92673': (33.4497, -117.6128, 'San Clemente'),
    '92675': (33.5497, -117.6628, 'San Juan Capistrano'),
    '92677': (33.5197, -117.7128, 'Laguna Niguel'),
    '92679': (33.5997, -117.6328, 'Coto de Caza'),
    '92683': (33.7497, -117.9928, 'Westminster'),
    '92688': (33.6097, -117.6328, 'Rancho Santa Margarita'),
    '92691': (33.5897, -117.6528, 'Mission Viejo'),
    '92692': (33.6197, -117.6428, 'Mission Viejo'),
    '92694': (33.5597, -117.6028, 'Ladera Ranch'),
    '92701': (33.7497, -117.8628, 'Santa Ana'),
    '92702': (33.7097, -117.8628, 'Santa Ana'),
    '92703': (33.7497, -117.9028, 'Santa Ana'),
    '92704': (33.7097, -117.9028, 'Santa Ana'),
    '92705': (33.7497, -117.8128, 'Santa Ana'),
    '92706': (33.7697, -117.8828, 'Santa Ana'),
    '92707': (33.7097, -117.8428, 'Santa Ana'),
    '92708': (33.7097, -117.9528, 'Fountain Valley'),
    '92780': (33.7397, -117.8228, 'Tustin'),
    '92782': (33.7597, -117.7728, 'Tustin'),
    '92801': (33.8397, -117.9328, 'Anaheim'),
    '92802': (33.8097, -117.9228, 'Anaheim'),
    '92804': (33.8197, -117.9728, 'Anaheim'),
    '92805': (33.8397, -117.9028, 'Anaheim'),
    '92806': (33.8397, -117.8628, 'Anaheim'),
    '92807': (33.8497, -117.7928, 'Anaheim'),
    '92808': (33.8697, -117.7428, 'Anaheim Hills'),
    '92821': (33.9297, -117.8928, 'Brea'),
    '92823': (33.9197, -117.8228, 'Brea'),
    '92831': (33.8797, -117.9228, 'Fullerton'),
    '92832': (33.8697, -117.9428, 'Fullerton'),
    '92833': (33.8697, -117.9728, 'Fullerton'),
    '92835': (33.9097, -117.9228, 'Fullerton'),
    '92840': (33.7497, -117.9628, 'Garden Grove'),
    '92841': (33.7897, -117.9928, 'Garden Grove'),
    '92843': (33.7597, -117.9228, 'Garden Grove'),
    '92844': (33.7697, -117.9728, 'Garden Grove'),
    '92845': (33.7897, -117.9528, 'Garden Grove'),
    '92861': (33.7897, -117.8128, 'Villa Park'),
    '92865': (33.8297, -117.8428, 'Orange'),
    '92866': (33.7897, -117.8528, 'Orange'),
    '92867': (33.8197, -117.8128, 'Orange'),
    '92868': (33.7897, -117.8828, 'Orange'),
    '92869': (33.8097, -117.7728, 'Orange'),
    '92870': (33.8997, -117.8628, 'Placentia'),
    '92886': (33.9197, -117.7928, 'Yorba Linda'),
    '92887': (33.8897, -117.7428, 'Yorba Linda'),
}

def parse_address(address):
    """Extract city, state, and zip from address string"""
    if not address or address.strip() == '':
        return None, None, None

    address_upper = address.upper()

    # Try to find 5-digit zip code
    zip_match = re.search(r'\b(\d{5})\b', address)
    zip_code = zip_match.group(1) if zip_match else None

    # Look for 2-letter state code
    state = None
    state_match = re.search(r'\b([A-Z]{2})\s+\d{5}', address_upper)
    if state_match:
        potential_state = state_match.group(1)
        if potential_state in STATE_ABBREV:
            state = potential_state

    # Extract city
    city = None
    if state:
        city_match = re.search(r'([A-Za-z\s\.]+?)\s+' + state + r'\s+\d{5}', address, re.IGNORECASE)
        if city_match:
            city = city_match.group(1).strip().strip('.')

    return city, state, zip_code

def get_coords(zip_code, state):
    """Get coordinates for a zip code or state"""
    if zip_code:
        # Try exact zip match first
        if zip_code in ZIP_COORDS:
            return ZIP_COORDS[zip_code]
        # Try 3-digit prefix
        prefix = zip_code[:3]
        if prefix in ZIP_COORDS:
            return ZIP_COORDS[prefix]
    return None

def main():
    parser = argparse.ArgumentParser(description='Generate subscriber residence heatmap')
    parser.add_argument('csv_path', help='Path to subscribed audience CSV file')
    parser.add_argument('-o', '--output', default='subscriber_map.html', help='Output HTML file path')
    args = parser.parse_args()

    csv_path = args.csv_path
    output_path = args.output

    states = Counter()
    locations = {}  # (lat, lng) -> {'count': n, 'name': name}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = 0
        parsed = 0
        geocoded = 0

        for row in reader:
            total += 1
            address = row.get('Address', '')
            city, state, zip_code = parse_address(address)

            if state:
                parsed += 1
                states[state] += 1

                coords = get_coords(zip_code, state)
                if coords:
                    geocoded += 1
                    lat, lng, name = coords
                    key = (lat, lng)
                    if key not in locations:
                        locations[key] = {'count': 0, 'name': name, 'lat': lat, 'lng': lng}
                    locations[key]['count'] += 1

    # Print summary
    print(f"\n=== Geographic Analysis ===")
    print(f"Total subscribers: {total}")
    print(f"With parseable address: {parsed} ({parsed*100//total}%)")
    print(f"Geocoded to coordinates: {geocoded}")

    print(f"\n--- Top Locations ---")
    sorted_locs = sorted(locations.values(), key=lambda x: -x['count'])[:25]
    for loc in sorted_locs:
        print(f"  {loc['name']}: {loc['count']}")

    # Generate HTML
    generate_html(states, locations, total, parsed, geocoded, output_path)
    print(f"\n✓ Generated: {output_path}")

def generate_html(states, locations, total, parsed, geocoded, output_path):
    """Generate interactive HTML with Leaflet bubble map"""

    # Prepare location data for map
    loc_data = [
        {'lat': v['lat'], 'lng': v['lng'], 'count': v['count'], 'name': v['name']}
        for v in locations.values()
    ]

    # Prepare state data for bar chart
    state_data = [(STATE_ABBREV.get(s, s), c) for s, c in states.most_common(15)]

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JETAASC Subscriber Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
        }}
        .header {{
            padding: 1.5rem 2rem;
            text-align: center;
        }}
        h1 {{ color: #fff; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #888; }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            padding: 1rem 2rem;
            flex-wrap: wrap;
        }}
        .stat-box {{
            background: #16213e;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            text-align: center;
            min-width: 120px;
        }}
        .stat-number {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #4ecca3;
        }}
        .stat-label {{
            color: #888;
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }}
        #map {{
            height: 500px;
            width: 100%;
            border-top: 1px solid #333;
            border-bottom: 1px solid #333;
        }}
        .chart-section {{
            padding: 2rem;
            max-width: 800px;
            margin: 0 auto;
        }}
        .chart-container {{
            background: #16213e;
            padding: 1.5rem;
            border-radius: 12px;
        }}
        .chart-container h2 {{
            margin-bottom: 1rem;
            font-size: 1.1rem;
            color: #4ecca3;
        }}
        .legend {{
            padding: 1rem 2rem;
            text-align: center;
            color: #888;
            font-size: 0.9rem;
        }}
        .legend-item {{
            display: inline-flex;
            align-items: center;
            margin: 0 1rem;
        }}
        .legend-circle {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: rgba(78, 204, 163, 0.6);
            border: 2px solid #4ecca3;
            margin-right: 0.5rem;
        }}
        .legend-circle.small {{ width: 10px; height: 10px; }}
        .legend-circle.large {{ width: 30px; height: 30px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>JETAASC Subscriber Map</h1>
        <p class="subtitle">Geographic distribution of {geocoded} subscribers with mappable addresses</p>
    </div>

    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{total:,}</div>
            <div class="stat-label">Total Subscribers</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{states.get('CA', 0):,}</div>
            <div class="stat-label">California</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{states.get('AZ', 0):,}</div>
            <div class="stat-label">Arizona</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{len(locations):,}</div>
            <div class="stat-label">Unique Areas</div>
        </div>
    </div>

    <div class="legend">
        <span class="legend-item"><span class="legend-circle" style="background:#00b4d8;border-color:#00b4d8"></span> 1-2</span>
        <span class="legend-item"><span class="legend-circle" style="background:#8ac926;border-color:#8ac926"></span> 3-4</span>
        <span class="legend-item"><span class="legend-circle" style="background:#ffbe0b;border-color:#ffbe0b"></span> 5-9</span>
        <span class="legend-item"><span class="legend-circle" style="background:#ff6b35;border-color:#ff6b35"></span> 10-19</span>
        <span class="legend-item"><span class="legend-circle" style="background:#ff2d55;border-color:#ff2d55"></span> 20+</span>
    </div>

    <div id="map"></div>

    <div class="chart-section">
        <div class="chart-container">
            <h2>Subscribers by State</h2>
            <canvas id="stateChart"></canvas>
        </div>
    </div>

    <script>
        // Initialize map centered on LA area
        const map = L.map('map').setView([34.0, -118.0], 9);

        // Dark map tiles
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }}).addTo(map);

        // Location data
        const locations = {json.dumps(loc_data)};

        // Color scale based on count
        function getColor(count) {{
            if (count >= 20) return '#ff2d55';      // Hot pink - high
            if (count >= 10) return '#ff6b35';      // Orange - medium-high
            if (count >= 5) return '#ffbe0b';       // Yellow - medium
            if (count >= 3) return '#8ac926';       // Lime - low-medium
            return '#00b4d8';                        // Cyan - low
        }}

        // Add circles for each location
        locations.forEach(loc => {{
            const radius = Math.sqrt(loc.count) * 4000;
            const color = getColor(loc.count);
            L.circle([loc.lat, loc.lng], {{
                color: color,
                fillColor: color,
                fillOpacity: 0.5,
                weight: 2,
                radius: Math.max(radius, 1500)
            }}).addTo(map)
              .bindPopup(`<strong>${{loc.name}}</strong><br>${{loc.count}} subscriber${{loc.count > 1 ? 's' : ''}}`);
        }});

        // Bar chart
        const stateLabels = {json.dumps([s[0] for s in state_data])};
        const stateValues = {json.dumps([s[1] for s in state_data])};

        const colors = [
            '#4ecca3', '#45b7aa', '#3ca4b1', '#3391b8', '#2a7ebf',
            '#4169e1', '#5a5fcf', '#7355bd', '#8c4bab', '#a54199',
            '#be3787', '#d72d75', '#e63946', '#f15a24', '#f99d1c'
        ];

        new Chart(document.getElementById('stateChart'), {{
            type: 'bar',
            data: {{
                labels: stateLabels,
                datasets: [{{
                    data: stateValues,
                    backgroundColor: colors,
                    borderRadius: 6,
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{
                        grid: {{ color: '#333' }},
                        ticks: {{ color: '#888' }}
                    }},
                    y: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#eee' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''

    with open(output_path, 'w') as f:
        f.write(html)

if __name__ == '__main__':
    main()
