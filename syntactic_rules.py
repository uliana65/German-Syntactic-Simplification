ams_extend_rule = [[{"DEP":"ams"}]]
ams_missing_rule = [[{"DEP":"mo", "POS":"NUM"}, {"POS":"VERB"}],
                    [{"POS":"VERB"}, {"DEP":"mo", "POS":"NUM"}],
                    [{"DEP":"mo", "POS":"NUM"}, {"POS":"AUX"}],
                    [{"POS":"AUX"}, {"DEP":"mo", "POS":"NUM"}]]
app_split_rule = [[{"DEP":"app"}]]
passive_rule = [[{'POS':'AUX', "LEMMA":"werden","OP":"+"}, {"OP":"*"}, {"DEP":"oc", 'POS':'VERB', "MORPH": "VerbForm=Part", "OP":"+"}],
                 [{"DEP":"oc", 'POS':'VERB', "MORPH": "VerbForm=Part", "OP":"+"}, {"OP":"*"}, {'POS':'AUX', "LEMMA":"werden","OP":"+"}]]
partizip_2_rule = [[{'POS':'VERB', "MORPH": "VerbForm=Part", "OP":"+"}]]
coordination_rule = [[{"POS":"VERB", "DEP":"cj"}],
                     [{"POS":"AUX", "DEP":"cj"}]]
subordinated_rule = [[{"POS":"SCONJ"}]]
relative_rule = [[{"DEP":"rc"}]]

ams_regex_replace = {"nm":"Nanometer", "mm":"Millimeter", "cm":"Zentimeter", "dm":"Dezimeter", "m":"Meter", "km":"Kilometer",
             "mg":"Milligramm", "g":"Gramm", "kg":"Kilogramm", "t":"Tonne", "oz":"Unze", "lb":"Pfund", "lbs":"Pfund",
             "mi":"Meile", "ha":"Hektar", "°":"Grad", "ml":"Milliliter", "cl":"Zentiliter", "l":"Liter",
             "%":"Prozent", "nm^2":"Quadratnanometer", "mm^2":"Quadratmillimeter", "cm^2":"Quadratzentimeter",
             "dm^2":"Quadratdezimeter", "m^2":"Quadratmeter", "km^2":"Quadratkilometer", "nm2":"Quadratnanometer",
             "mm2":"Quadratmillimeter", "cm2":"Quadratzentimeter", "dm2":"Quadratdezimeter", "m2":"Quadratmeter",
             "km2":"Quadratkilometer", "nm²":"Quadratnanometer", "mm²":"Quadratmillimeter", "cm²":"Quadratzentimeter",
             "dm²":"Quadratdezimeter", "m²":"Quadratmeter", "km²":"Quadratkilometer", "nm³":"Kubiknanometer",
             "mm³":"Kubikmillimeter", "cm³":"Kubikzentimeter", "dm³":"Kubikdezimeter", "m³":"Kubikmeter", "km³":"Kubikkilometer",
             "nm^3":"Kubiknanometer", "mm^3":"Kubikmillimeter", "cm^3":"Kubikzentimeter", "dm^3":"Kubikdezimeter",
             "m^3":"Kubikmeter", "km^3":"Kubikkilometer", "nm3":"Kubiknanometer", "mm3":"Kubikmillimeter", "cm3":"Kubikzentimeter",
             "dm3":"Kubikdezimeter", "m3":"Kubikmeter", "km3":"Kubikkilometer", "GG": "Grundgesetz", "Art":"Artikel",
             "yd": "Yard", "€":"Euro", "$":"Dollar", "DM":"Deutsche Mark", "GBP": "Pfund", "£":"Pfund", "Mrd":"Milliarde",
             "Mio":"Million", "Stk":"Stück", "B":"Byte", "Lat":"Breitengrad", "Lon":"Längengrad", "gW":"Gigawatt",
             "kW":"Kilowatt", "W":"Watt", "Hz":"Hertz", "MHz":"Megahertz", "KHz":"Kilohertz", "GB":"Gigabyte", "MB":"Megabyte",
             "KB":"Kilobyte", "TB":"Terabyte", "BRT":"Bruttoregistertonne", "GWh":"Gigawattstunde", "Jz":"Jahrzehnt",
             "Wo":"Woche", "J":"Jahr", "h":"Stunde", "Std":"Stunde", "St":"Stunde", "Sek": "Sekunde", "s":"Sekunde", "sek":"Sekunde",
             "ms":"Millisekunde", "Min":"Minute", "min":"Minute", "d":"Tag", "M":"Monat", "Mo":"Monat", "Mon":"Monat", "Mt":"Monat",
             "Jhdt":"Jahrhundert", "Jh":"Jahrhundert", "Jahrh":"Jahrhundert", "Jhd":"Jahrhundert", "Jhrh":"Jahrhundert",
             "Lj":"Lichtjahr", "Flugstd":"Flugstunde", "Jt":"Jahrtausend", "Jtd":"Jahrtausend", "Jtsd":"Jahrtausend",
             "Jahrt":"Jahrtausend", "sm":"Seemeile", "Dek":"Dekade", "Ep":"Epoche", "PS":"Pferdestärke", "ft":"Fuß",
             "Pkt":"Punkt", "Pf":"Pfennig", "Pfg":"Pfennig", "Dpf":"Pfennig", "H":"Hundert", "Hd":"Hundert", "Hdt":"Hundert",
             "WS":"Wintersemester", "SS":"Sommersemester", "Nl":"Niederlage", "Ndl":"Niederlage", "Niederl":"Niederlage",
             "Okt":"Oktave", "Abschn":"Abschnitt", "PP":"Prozentpunkt", "Fl":"Fläche",
             "px":"Pixel"}

missing_ams_regex = r"(^|\s)\d\d\d\d($|\s)"
semicolon_regex = r"\(.*?\)|\".*?\"|((?!^);(?!$))"
ams_regex = r"(\d|pro)+\s*(nm\^2|mm\^2|cm\^2|dm\^2|m\^2|km\^2|nm2|mm2|cm2|dm2|m2|km2|nm²|mm²|cm²|dm²|m²|km²|nm³|mm³|cm³|dm³|m³|km³|nm\^3|mm\^3|cm\^3|dm\^3|m\^3|km\^3|nm3|mm3|cm3|dm3|m3|km3|nm|mm|cm|dm|km|mg|kg|oz|lbs|lb|mi|ha|°|ml|cl|%| |GG|Art|yd|€|\$|DM|GBP|£|Mrd|Mio|Stk|Lat|Lon|gW|kW|MHz|KHz|Hz|GB|MB|KB|TB|BRT|GWh|Jz|Wo|J|Std|St|Sek|sek|ms|Min|min|Mon|Mo|Mt|Jhdt|Jahrh|Jhd|Jhrh|Jh|Lj|Flugstd|Jtd|Jtsd|Jt|Jahrt|sm|Dek|Ep|PS|ft|Pkt|Pfg|Pf|Dpf|Hdt|Hd|H|WS|SS|Nl|Ndl|Niederl|Okt|Abschn|PP|Fl|px|m|l|B|g|W|h|s|d|M|t)(\W|$)+"
app_not_split_regex = r"(z.B.|zum Beispiel|z. B.)"
punt_regex = r"[,;.?!]+ *[,;.?!]+"
