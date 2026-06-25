# Delonghi Pinguino PAC N portable climate integration for HomeAssistant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Galaxy102&repository=homeassistant-delonghi-pinguino-pac-n&category=integration)

## Functions
The following functions are supported:
- General
  - Use Fahrenheit as device temperature unit
- Climate entity
  - Target Temperature
  - Fan Mode
  - Device Mode (Cool, Dry, Fan)

Not supported:
- Timer

## How I got here
I captured Pronto codes with ESPHome's Infrared Receiver entity.
These Pronto codes contain 32 bits of binary data, for which I created a table and then looked at what changed.
Protocol details can be found in the Docstrings of the source files.

## Supported devices
This integration targets the Delonghi PAC N series with the following infrared remote:

![Delonghi 5515110111](https://assets.mmsrg.com/isr/166325/c1/-/pixelboxx-mss-81953192?x=1800&y=1800&format=jpg&quality=80&sp=yes&strip=yes&trim&ex=1800&ey=1800&align=center&resizesource&unsharp=1.5x1+0.7+0.02&cox=0&coy=0&cdx=1800&cdy=1800)

Known models with the same or a compatible remote are: (source: https://www.remote-control-world.eu/climatisation-ventilateur-c-261/delonghi-pac-n82-eco-n75-n80-n85-n87-n90-n91-n110-n115-n120-n135-t%25C3%25A9l%25C3%25A9commande-de-remplacement-p-16204?language=de)
- Delonghi PAC N74 Eco R290
- Delonghi PAC N75
- Delonghi PAC N76
- Delonghi PAC N76 Silent
- Delonghi PAC N77 Eco R290
- Delonghi PAC N80
- Delonghi PAC N80.1
- Delonghi PAC N81
- Delonghi PAC N82 Eco R290
- Delonghi PAC N85
- Delonghi PAC N86
- Delonghi PAC N87 Silent
- Delonghi PAC N88 Silent
- Delonghi PAC N89 Silent
- Delonghi PAC N90
- Delonghi PAC N90 Eco Silent R290
- Delonghi PAC N90.B
- Delonghi PAC N90E
- Delonghi PAC N91 Eco Silent R290
- Delonghi PAC N92 Eco Silent R290
- Delonghi PAC N100E
- Delonghi PAC N110
- Delonghi PAC N110EC
- Delonghi PAC N110EC-3A
- Delonghi PAC N115EC
- Delonghi PAC N115EC.WH-3A
- Delonghi PAC N120
- Delonghi PAC N120E
- Delonghi PAC N120EC
- Delonghi PAC N120EX
- Delonghi PAC N120W
- Delonghi PAC N125E
- Delonghi PAC N135EC
- Delonghi PAC N140E
- Delonghi PAC N250 GN-3A WH
- Delonghi PAC N270 GN-3A WH
- Delonghi PAC N285 GN-3A DG
- Delonghi PAC C100 EC

- Delonghi PAC AN95
- Delonghi PAC AN96
- Delonghi PAC AN110
- Delonghi PAC AN111
- Delonghi PAC AN120
- Delonghi PAC AN120ES
- Delonghi PAC AN125 ES
- Delonghi PAC AN130ES.WH-3A
- Delonghi PAC AN135ES.WH-3A
- Delonghi PAC AN140ES.WH-3A
- Delonghi PAC AN140HPEC
- Delonghi PAC AN285 GN-3A WH

- Delonghi PAC CN86 Silent
- Delonghi PAC CN90 Silent
- Delonghi PAC CN90.B
- Delonghi PAC CN91
- Delonghi PAC CN92 Silent
- Delonghi PAC CN93 Eco
- Delonghi PAC CN94
- Delonghi PAC CN95 Eco
- Delonghi PAC CN96 Eco
- Delonghi PAC CN120E

## License

This project (except the branding) is licensed under the MIT license. See [LICENSE](LICENSE) for details.
