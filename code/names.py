"""Names for big or populous GSHHG islands that Natural Earth's physical labels do not name.
Each was assigned by hand from the island's position, area and largest town (checked against the GSHHG polygon), keyed
by GSHHG polygon id. Islands I could not name with confidence are left unnamed. Also fixes a few Natural Earth labels."""
NAMES = {
    "37": "Severny Island (Novaya Zemlya)", "49": "Yuzhny Island (Novaya Zemlya)", "45": "New Britain",
    "46": "Brodeur Peninsula (Baffin Island)", "59": "Grande Terre (New Caledonia)", "74": "Ellef Ringnes Island",
    "80": "Viti Levu", "81": "Hawaii (Big Island)", "86": "Graham and Moresby Islands (Haida Gwaii)", "91": "Bougainville",
    "99": "Aru Islands", "102": "New Ireland", "104": "Prince of Wales Island (Alaska)", "105": "Grande Terre (Kerguelen)",
    "112": "Vanua Levu", "115": "Chichagof Island", "116": "Guadalcanal", "118": "Amund Ringnes Island",
    "119": "Bolshoy Lyakhovsky Island", "120": "Mackenzie King Island", "124": "Riesco Island", "127": "Isabela (Galápagos)",
    "131": "Stefansson Island", "132": "Buton", "134": "Cebu", "136": "Admiralty Island", "137": "Hoste Island",
    "139": "Baranof Island", "142": "Espiritu Santo", "143": "Gurupá Island", "146": "Milne Land", "148": "Santa Inés Island",
    "149": "Santa Isabel", "151": "Euboea", "156": "Traill Island", "160": "Makira", "161": "Yamdena", "162": "Masbate",
    "163": "Iturup", "165": "Waigeo", "169": "Funen", "171": "Revillagigedo Island", "172": "Muna", "174": "Kupreanof Island",
    "175": "Borden Island", "176": "Unalaska Island", "179": "Princess Royal Island", "182": "Obi", "184": "Navarino Island",
    "186": "Ymer Island", "187": "Peleng", "189": "Yapen", "190": "Cornwall Island", "193": "Isla de la Juventud",
    "194": "Nunivak Island", "195": "Lewis and Harris", "197": "Caviana Island", "199": "Laut Island", "201": "Magdalena Island",
    "202": "George Land", "203": "Misool", "237": "Salawati", "204": "New Georgia", "205": "Malakula", "207": "Paramushir",
    "209": "Kuiu Island", "214": "Maui", "216": "Afognak Island", "217": "Bolshoy Shantar Island", "219": "Bacan",
    "220": "Flaherty Island", "223": "Umnak Island", "224": "Geographical Society Island", "227": "Air Force Island",
    "228": "Savai'i", "229": "Bathurst Island (Australia)", "231": "Pioneer Island", "232": "Skye", "240": "Senja",
    "242": "Oahu", "244": "Eglinton Island", "245": "Great Inagua", "248": "Clavering Island", "252": "Pitt Island",
    "254": "Catanduanes", "256": "Qeshm", "257": "Kauai", "259": "Urup", "187163": "Copper Island (Keweenaw)",
    "187160": "Manitoulin Island", "187161": "René-Levasseur Island", "261": "Graham Island (Nunavut)", "262": "Öland",
    "263": "Nottingham Island", "264": "Desolación Island", "267": "Fergusson Island", "269": "Barentsøya",
    "274": "Clarence Island", "275": "Lembata", "276": "Lolland", "277": "Shannon Island", "278": "Basilan",
    "282": "Rote", "283": "New Hanover", "285": "Mangole", "286": "Tiburón Island", "287": "Bintan", "288": "Okinawa Island",
    "290": "Great Abaco", "291": "Wales Island", "292": "Byam Martin Island", "268": "Lougheed Island", "300": "Rowley Island",
    "304": "Alexandra Land", "309": "Tahiti", "310": "Chongming Island", "311": "Resolution Island", "312": "Hiiumaa",
    "314": "Mainland (Shetland)", "316": "Vansittart Island", "247": "Dawson Island", "249": "Rupat",
}
# tidy Natural Earth labels
RENAME = {"Mainland Tasmania": "Tasmania", "Hokkaidō": "Hokkaido", "Seram Island": "Seram", "Vancouver": "Vancouver Island"}
