"""Master list of Kenya's 47 counties (code, name, former province). ASAL flag is indicative; verify against NDMA."""
_P = {range(1, 7): "Coast", range(7, 10): "North Eastern", range(10, 18): "Eastern",
      range(18, 23): "Central", range(23, 37): "Rift Valley", range(37, 41): "Western",
      range(41, 47): "Nyanza", range(47, 48): "Nairobi"}
NAMES = ["Mombasa", "Kwale", "Kilifi", "Tana River", "Lamu", "Taita-Taveta", "Garissa", "Wajir", "Mandera",
         "Marsabit", "Isiolo", "Meru", "Tharaka-Nithi", "Embu", "Kitui", "Machakos", "Makueni", "Nyandarua",
         "Nyeri", "Kirinyaga", "Murang'a", "Kiambu", "Turkana", "West Pokot", "Samburu", "Trans Nzoia",
         "Uasin Gishu", "Elgeyo-Marakwet", "Nandi", "Baringo", "Laikipia", "Nakuru", "Narok", "Kajiado",
         "Kericho", "Bomet", "Kakamega", "Vihiga", "Bungoma", "Busia", "Siaya", "Kisumu", "Homa Bay",
         "Migori", "Kisii", "Nyamira", "Nairobi"]
ASAL = {"Kilifi", "Kwale", "Tana River", "Lamu", "Taita-Taveta", "Garissa", "Wajir", "Mandera", "Marsabit",
        "Isiolo", "Kitui", "Makueni", "Turkana", "West Pokot", "Samburu", "Baringo", "Laikipia", "Narok", "Kajiado"}

def _region(code):
    return next(v for r, v in _P.items() if code in r)

COUNTIES = [(i, n, _region(i), n in ASAL) for i, n in enumerate(NAMES, start=1)]
