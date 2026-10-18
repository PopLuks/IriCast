# 🌱 IriCast (Irigare inteligentă cu Open-Meteo)

## Echipa
- Bancoș Gabriel
- Mirth Kevin
- Pop Lucas

## Scenariu IoT:

- **Ce sistem fizic este simulat?**
  Un sistem de monitorizare și sprijinire a deciziilor de irigare pentru o cultură de roșii în câmp deschis. În versiunea actuală, sistemul fizic nu este implementat și nu controlează echipamente reale. Analiza folosește date meteorologice reale de la Open-Meteo, procesate în Python, pentru a identifica perioade cu potențial risc de secetă.

- **Ce senzori sunt folosiți?**
  Nu sunt folosiți senzori fizici. Datele sunt preluate prin API-ul Open-Meteo și pot include temperatura aerului, umiditatea relativă și precipitațiile. Dacă Open-Meteo furnizează date despre umiditatea solului, proiectul le va prezenta ca estimări ale modelului, nu ca valori măsurate cu senzori.

- **Ce anomalii sunt de așteptat să apară?**
  - Perioade prelungite cu precipitații reduse sau absente.
  - Temperatură ridicată combinată cu umiditate relativă scăzută.
  - Modificări ale umidității solului estimate de model, dacă această variabilă este disponibilă.
  - Valori lipsă, întârziate sau neverosimile în datele preluate.

  Aceste condiții sunt indicatori pentru analiză și nu confirmă, de unele singure, că plantele suferă de stres hidric. Confirmarea ar necesita măsurători în teren sau validare agronomică.

## Arhitectură

`Open-Meteo API -> Python -> Rezultate`

Open-Meteo furnizează datele meteorologice. Python prelucrează datele și analizează condițiile asociate riscului de secetă. Proiectul nu include în prezent un gateway hardware sau un frontend separat.

## Întrebarea de cercetare

**ÎC:** Cât de eficient pot indicatorii derivați din date meteorologice reale Open-Meteo să identifice perioade cu risc crescut de secetă, relevante pentru o cultură de roșii în câmp deschis din Topolița, Neamț?

Dacă sunt incluse date despre umiditatea solului estimată de un model, întrebarea de cercetare și rezultatele trebuie să distingă explicit estimările modelului de măsurătorile directe ale solului.

## Ipoteză

**H1:** O regulă care combină mai mulți indicatori meteorologici, precum istoricul precipitațiilor și condițiile de temperatură ridicată, va identifica perioadele potențial secetoase mai util decât o regulă bazată pe o singură variabilă meteorologică.

Aceasta este o ipoteză care trebuie testată, nu un rezultat. Regulile și pragurile selectate trebuie documentate înainte de interpretarea rezultatelor.

## Metodă de referință

Metoda de referință va fi o regulă simplă și documentată, bazată pe o singură variabilă disponibilă, cum ar fi cantitatea cumulată de precipitații într-o perioadă definită. Metoda propusă va combina mai mulți indicatori meteorologici disponibili. Dacă sunt folosite estimări ale umidității solului, acestea pot fi evaluate ca semnal suplimentar și trebuie etichetate drept date estimate de un model.

Pragurile și ferestrele de timp trebuie precizate explicit. Fără observații independente din teren sau date de referință agronomice etichetate, proiectul poate compara comportamentul indicatorilor, dar nu poate susține că a validat acuratețea detectării stresului hidric real al culturii.

## Abordarea propusă

Analiza în Python va compara o regulă simplă de referință cu o regulă bazată pe mai mulți indicatori, folosind setul real de date Open-Meteo. În funcție de endpoint-ul selectat și de variabilele disponibile, analiza poate lua în considerare istoricul precipitațiilor, temperatura aerului, umiditatea relativă și umiditatea solului estimată de un model.

Rezultatul va fi un indicator interpretabil al riscului de secetă sau o recomandare de sprijin pentru irigare. Acesta are doar rol consultativ și nu va acționa automat echipamente reale de irigare. Recomandările nu trebuie prezentate ca fiind optime din punct de vedere agronomic fără măsurători în teren și validare de specialitate.

## Plan experimental

### Setul de date
- Se preiau date meteorologice reale de la Open-Meteo pentru locația și intervalul de timp selectate.
- Se înregistrează endpoint-ul API, coordonatele, perioada, variabilele, unitățile de măsură, data preluării și orice informații relevante despre atribuire sau licență.
- Se verifică marcajele temporale, valorile lipsă și consistența datelor înainte de analiză.
- Nu se generează în Python valori sintetice de la senzori pentru a fi folosite ca set principal de date al proiectului.
- Dacă o variabilă precum umiditatea solului este furnizată ca estimare de model, se documentează sursa și nu este descrisă ca măsurătoare directă din teren.

### Perioade și cazuri analizate
1. Perioade cu precipitații suficiente și temperaturi moderate.
2. Perioade prelungite cu precipitații reduse.
3. Perioade calde și secetoase.
4. Perioade de după precipitații, pentru a observa schimbările indicatorilor meteorologici.
5. Perioade cu date incomplete sau lipsă din sursă, pentru a testa tratarea calității datelor.

Cazurile vor fi selectate din setul real de date preluat. Ele nu vor fi descrise ca evenimente etichetate de stres al culturii decât dacă există observații independente din teren sau o metodă justificată de etichetare.

### Variabile controlate
- Coordonatele locației
- Perioada de analiză și rezoluția temporală
- Endpoint-ul Open-Meteo și variabilele selectate
- Precipitațiile accumulation window
- Pragurile și parametrii fiecărei reguli de detectare
- Modul de tratare a datelor lipsă

Pentru o comparație corectă, se folosește același set de date și aceeași perioadă pentru metoda de referință și metoda propusă, modificând doar regula evaluată.

### Evaluare
În funcție de datele de referință disponibile, evaluarea poate include:
- Numărul și durata perioadelor marcate ca secetoase sau cu risc ridicat
- Concordanța și diferențele dintre regula de referință și regula cu mai mulți indicatori
- Intervalul dintre modificările indicatorilor meteorologici și declanșarea unei alerte definite
- Numărul și momentul recomandărilor de sprijin pentru irigare
- Acoperirea datelor și proporția valorilor lipsă

Precizia, recall-ul, scorul F1 și întârzierea detectării în raport cu evenimente reale de stres hidric al culturii pot fi raportate doar dacă sunt disponibile evenimente de referință etichetate independent. Fără asemenea etichete, aceste metrici nu trebuie prezentate ca rezultate validate ale performanței.

## Tehnologii utilizate

- **Sursa datelor:** API Open-Meteo
- **Preluarea și analiza datelor:** Python
- **Procesare:** biblioteci Python pentru prelucrarea datelor, care vor fi enumerate în funcție de implementarea efectivă
- **Vizualizare:** grafice și tabele de sinteză, dacă sunt implementate
- **Hardware edge:** nu este necesar pentru versiunea actuală de analiză a datelor
- **Senzori fizici:** nu sunt declarați ca parte a implementării actuale
- **Controlul irigării:** neimplementat. rezultatele au doar rol consultativ

## Cum se rulează

*(de completat după implementare)*

## Rezultate

*(de completat după rularea simulărilor)*

## Limitări

- Datele Open-Meteo descriu condițiile meteorologice sau estimările unui model pentru o locație și o celulă de grilă. ele nu sunt măsurători provenite de la senzori instalați în cultura de roșii IriCast.
- Condițiile locale din teren pot diferi de datele pe grilă sau de cele estimate de modele.
- Indicatorii meteorologici, singuri, nu pot confirma starea reală a apei din plante sau sol.
- Umiditatea solului estimată de un model, dacă este folosită, trebuie diferențiată de măsurătorile directe ale senzorilor.
- Planificarea irigării în condiții de fiabilitate agronomică necesită informații locale despre sol, cultură și irigare, precum și validare prin măsurători în teren sau de către un specialist.
- Sistemul oferă doar rezultate de analiză și recomandări. Nu controlează automat echipamente reale de irigare.
- Detaliile specifice fermei, precum suprafața cultivată în prezent, tipul solului, instalarea senzorilor și volumele de irigare, nu au fost verificate pentru acest proiect.

## Bibliografie

1. Open-Meteo. *Weather API*. https://open-meteo.com/en/docs
2. Open-Meteo. *Documentation*. https://open-meteo.com/en/docs
3. Python Software Foundation. *Python 3 Documentation*. https://docs.python.org/3/

