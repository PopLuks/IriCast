# 🌱 Irigare inteligentă cu Open-Meteo

Proiect IoT pentru estimarea necesarului de apă al unei grădini folosind date meteorologice de la [Open-Meteo](https://open-meteo.com/en/docs). Sistemul combină precipitațiile, evapotranspirația de referință (ET₀) și prognoza meteo pentru a recomanda dacă o zonă ar trebui irigată. Obiectivul este reducerea irigărilor inutile și compararea unei strategii bazate pe vreme cu un program fix de irigare.

> **Stadiu:** documentație și proiectare inițială. Comenzile de rulare, rezultatele și detaliile implementării trebuie actualizate după ce codul sursă este disponibil.

## Echipa

- **[Numele membrului 1]**
- **[Numele membrului 2]**
- **[Numele membrului 3]**

## Scenariul IoT

### 1. Ce sistem fizic este simulat?

Sistemul fizic simulat este o grădină împărțită în una sau mai multe zone de irigare. Fiecare zonă poate avea parametri proprii, precum tipul culturii, coeficientul culturii și pragul de irigare.

În prima etapă, funcționarea este simulată software. Aplicația preia date meteorologice, estimează bilanțul hidric și generează recomandări de irigare. Ulterior, recomandările pot fi afișate într-un tablou de bord, trimise ca notificări sau transmise unui controler de irigare.

### 2. Ce senzori sunt folosiți?

În această versiune a proiectului nu sunt utilizați senzori fizici. Datele despre condițiile meteorologice sunt preluate din API-ul Open-Meteo și folosite ca intrări pentru simulare. Principalele date sunt:

- `precipitation_sum`: suma zilnică a precipitațiilor, în milimetri;
- `et0_fao_evapotranspiration`: evapotranspirația de referință ET₀, în milimetri;
- precipitații prognozate, pentru estimarea posibilității de a amâna irigarea;
- date meteorologice istorice, pentru simularea și compararea strategiilor în perioade diferite.

Nu este necesară conectarea la senzori fizici. Dacă un Raspberry Pi este disponibil, acesta poate rula scriptul de redare a datelor; în timpul dezvoltării, aceeași componentă poate fi executată local.

Open-Meteo oferă un API REST care nu necesită cheie API pentru utilizarea standard. Disponibilitatea și intervalul istoric depind de setul de date și de endpoint-ul selectat.

### 3. Ce anomalii sunt așteptate?

- date meteorologice lipsă sau indisponibile;
- răspunsuri API invalide sau neașteptate;
- ploaie prognozată care nu se produce;
- precipitații abundente care nu sunt absorbite integral de sol;
- perioade calde și secetoase, cu ET₀ ridicată;
- coordonate geografice sau fus orar incorecte;
- recomandări repetate de irigare cauzate de un prag configurat necorespunzător;
- diferențe între bilanțul estimat și umiditatea reală a solului.

## Arhitectură

Fluxul de date propus:

```text
Open-Meteo API
      │
      ▼
Prelucrarea și validarea datelor
      │
      ▼
Estimatorul bilanțului hidric
      │
      ▼
Motorul de decizie pentru irigare
      │
      ├──► Tablou de bord
      ├──► Notificare
      └──► Controler / electrovalvă (opțional)
```

## Întrebarea de cercetare

**RQ:** În ce măsură o strategie de irigare bazată pe precipitații și evapotranspirația de referință poate reduce consumul simulat de apă față de irigarea după un program fix, fără a depăși o limită prestabilită a deficitului hidric estimat?

## Ipoteză

**H1:** În perioadele meteorologice evaluate, strategia bazată pe bilanțul hidric va utiliza mai puțină apă pentru irigare decât strategia cu program fix, păstrând deficitul hidric estimat sub o limită definită.

**H0:** Strategia bazată pe bilanțul hidric nu va reduce consumul simulat de apă în mod relevant fără a încălca limita deficitului hidric.

Ipotezele vor fi evaluate utilizând aceleași date meteorologice și aceiași parametri ai zonei pentru toate strategiile comparate.

## Soluția de referință (baseline)

Soluția de referință este o strategie de irigare după un program fix. Irigarea are loc la intervale prestabilite, indiferent de precipitații sau de ET₀.

Pentru o comparație corectă, toate strategiile trebuie evaluate pentru aceeași locație, perioadă, zonă de grădină, stare inițială și ipoteze privind eficiența irigării.

## Abordarea propusă

### 1. Estimarea bilanțului hidric

Un model simplificat al bilanțului pentru un interval de timp este:

```text
B(t) = B(t-1) + P_eff(t) - ET_c(t) + I_eff(t)
```

Unde:

- `B(t)`: bilanțul hidric estimat, în milimetri;
- `P_eff(t)`: precipitațiile efective disponibile plantelor;
- `ET_c(t)`: evapotranspirația estimată a culturii;
- `I_eff(t)`: apa de irigare care ajunge efectiv în zona rădăcinilor.

Evapotranspirația culturii poate fi aproximată prin:

```text
ET_c(t) = ET0(t) * Kc(t)
```

`ET0(t)` este evapotranspirația de referință furnizată de Open-Meteo, iar `Kc(t)` este coeficientul culturii, în funcție de tipul culturii și stadiul de dezvoltare.

Într-un prototip simplificat se poate folosi ET₀ direct, echivalent cu presupunerea `Kc = 1`. Această aproximație trebuie menționată în interpretarea rezultatelor.

### 2. Decizia de irigare

Motorul de decizie compară bilanțul estimat cu un prag configurabil. O regulă inițială ar putea fi:

- dacă bilanțul scade sub prag, se recomandă irigarea;
- dacă sunt prognozate precipitații suficiente, irigarea poate fi amânată;
- dacă datele sunt invalide sau indisponibile, decizia este marcată ca incertă și nu se pornește automat irigarea doar pe baza unor valori implicite.

Pragul, intervalul de evaluare și ponderea acordată precipitațiilor prognozate trebuie să fie configurabile.

### 3. Utilizarea prognozei

Pentru a ține cont de incertitudinea prognozei, precipitațiile prognozate pot fi ponderate. De exemplu, un factor de `0.5` ar însemna că modelul ia în calcul jumătate din cantitatea prognozată pentru estimarea viitoare. Valoarea este un parametru experimental, nu una optimă în toate condițiile.

### 4. Explicarea deciziei

Pentru fiecare recomandare, sistemul ar trebui să înregistreze:

- bilanțul hidric estimat;
- precipitațiile observate și prognozate;
- ET₀ și, dacă este disponibil, ET₍c₎ estimat;
- pragul configurat;
- decizia rezultată și motivul acesteia.

## Plan experimental

### Date și seturi de test

Experimentele vor utiliza date meteorologice istorice de la Open-Meteo. Datele și rezultatele intermediare ar trebui salvate pentru a permite repetarea experimentelor.

Variabilele principale sunt precipitațiile zilnice, ET₀ și marcajele temporale. Parametrii de simulare includ coeficientul culturii, pragul de irigare, eficiența irigării și setările programului fix.

### Scenarii

1. **Vreme obișnuită:** alternanță între ploaie și perioade uscate.
2. **Perioadă caldă și secetoasă:** ET₀ ridicată și precipitații reduse.
3. **Perioadă ploioasă:** precipitații frecvente.
4. **Erori de prognoză:** precipitațiile estimate diferă de cele observate ulterior.
5. **Date indisponibile:** API-ul nu furnizează valori pentru un interval.
6. **Sensibilitatea pragului:** se variază pragul pentru a măsura influența sa asupra consumului de apă și deficitului estimat.

### Strategii comparate

- **Strategia A: program fix:** irigare la intervale prestabilite.
- **Strategia B: reguli de precipitații:** decizie bazată pe cantitatea de ploaie și prognoză.
- **Strategia C: bilanț hidric:** decizie bazată pe precipitații, ET₀ și bilanțul cumulativ estimat.

### Variabile controlate

- coordonatele geografice și perioada evaluată;
- caracteristicile zonei de grădină;
- coeficientul culturii;
- eficiența și debitul de irigare;
- starea inițială a bilanțului hidric;
- limita acceptată pentru deficitul hidric.

### Indicatori de evaluare

1. **Cantitatea totală de apă pentru irigare**: volumul sau stratul total de apă utilizat.
2. **Deficitul hidric estimat**: deficitul maxim și/sau cumulativ modelat.
3. **Frecvența irigării**: numărul de evenimente de irigare.
4. **Calitatea deciziilor**: irigări inutile și ocazii de irigare ratate, conform criteriilor definite pentru simulare.
5. **Sensibilitatea la prognoză**: efectul erorilor de prognoză asupra deciziilor.
6. **Disponibilitatea datelor**: proporția intervalelor cu date de intrare valide.

Rezultatele vor fi prezentate prin tabele și grafice. Concluziile trebuie să precizeze setul de date, perioada, parametrii și limitările simulării. Nu se presupun îmbunătățiri înainte de efectuarea experimentelor.

## Tehnologii

Stiva tehnologică propusă poate fi ajustată în timpul implementării.

| Componentă | Tehnologie propusă |
|---|---|
| Date meteorologice | Open-Meteo REST API |
| Simulare | Date generate și model de bilanț hidric |
| Backend | Python |
| Comunicare | HTTP / REST, JSON |
| Stocare | CSV sau SQLite |
| Interfață | Tablou de bord web sau Home Assistant |
| ML / AI | Opțional; algoritmul inițial este bazat pe reguli |
| Actuare | Releu sau electrovalvă, opțional |

## Integrarea Open-Meteo

Exemplu de cerere pentru precipitații zilnice și ET₀:

```text
https://api.open-meteo.com/v1/forecast?latitude=47.66&longitude=23.58&daily=precipitation_sum,et0_fao_evapotranspiration&timezone=Europe%2FBucharest
```

Coordonatele `47.66, 23.58` sunt un exemplu și trebuie înlocuite cu coordonatele grădinii.

Pentru date istorice, se poate utiliza endpoint-ul:

```text
https://archive-api.open-meteo.com/v1/archive
```

Documentație:

- [Forecast API](https://open-meteo.com/en/docs)
- [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)

Aplicația trebuie să valideze răspunsurile JSON, să gestioneze erorile de rețea și să nu confunde datele lipsă cu precipitații egale cu zero.

## Rulare

**Notă:** pașii de mai jos sunt orientativi și trebuie adaptați după crearea fișierelor de cod. Repository-ul trebuie să conțină fișierele menționate înainte ca aceste comenzi să poată fi folosite efectiv.

### Cerințe

- Python 3.11 sau o versiune compatibilă;
- Git;
- conexiune la internet pentru accesarea API-ului;
- coordonatele geografice ale grădinii.

### Instalare

```bash
git clone <repository-url>
cd <project-directory>
python -m venv .venv
```

Activarea mediului virtual:

**Windows (PowerShell)**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

Dacă proiectul include un fișier `requirements.txt`, instalați dependențele cu:

```bash
pip install -r requirements.txt
```

Comanda exactă de pornire și parametrii de configurare vor fi adăugați după stabilirea structurii aplicației și implementarea codului.

## Rezultate

Această secțiune va fi completată după implementare și evaluare experimentală.

Rezultatele planificate includ:

- comparația cantității totale de apă pentru fiecare strategie;
- evoluția bilanțului hidric în timp;
- momentele de irigare în raport cu precipitațiile și ET₀;
- analiza sensibilității pragului de irigare;
- efectul erorilor de prognoză asupra deciziilor;
- evaluarea ipotezei pe baza indicatorilor măsurați.

Nu sunt prezentate rezultate numerice deoarece experimentele nu sunt documentate în acest moment.

## Limitări

- ET₀ este un indicator de referință și nu reprezintă direct consumul de apă al oricărei plante.
- Necesarul real depinde de cultură, stadiul de dezvoltare, sol și condițiile locale.
- Nu toată cantitatea de precipitații ajunge la rădăcinile plantelor.
- Prognozele meteorologice sunt incerte.
- Fără senzori de sol, sistemul estimează bilanțul hidric, dar nu confirmă umiditatea reală.
- Modelul inițial poate să nu includă scurgerea de suprafață, drenajul și variațiile dintre diferite puncte ale grădinii.
- Datele istorice și simulările nu înlocuiesc validarea în teren.
- Controlul automat al irigării necesită protecții suplimentare împotriva datelor eronate, defectării actuatorului și udării excesive.

Prin urmare, rezultatele descriu performanța modelului de estimare în scenariile testate, nu măsurarea directă a stării plantelor sau a umidității solului.

## Dezvoltări viitoare

- integrarea senzorilor de umiditate a solului pentru compararea estimărilor cu măsurătorile;
- comandarea unei electrovalve sau a unui releu de irigare;
- suport pentru mai multe zone și coeficienți specifici culturilor;
- folosirea măsurătorilor locale de ploaie;
- evaluarea incertitudinii prognozei și a pragurilor adaptive;
- integrarea cu Home Assistant;
- testarea într-o grădină reală și compararea consumului simulat cu cel măsurat.

## Referințe

1. [Open-Meteo: Forecast API](https://open-meteo.com/en/docs)
2. [Open-Meteo: Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
3. [LazyAdmin: Automating My Vegetable Garden Irrigation with Home Assistant](https://lazyadmin.nl/smart-home/home-assistant-garden-irrigation-automation/)
4. [agri-weather-mcp: repository GitHub menționat în propunerea inițială](https://github.com/etudelab/agri-weather-mcp)

## Concluzie

Proiectul evaluează dacă utilizarea precipitațiilor și a evapotranspirației de referință poate îmbunătăți deciziile de irigare față de un program fix. Combinarea datelor meteorologice istorice cu un model configurabil de bilanț hidric și un motor de decizie explicabil oferă un cadru pentru compararea strategiilor în condiții controlate.

Contribuția principală urmărită este evaluarea experimentală a strategiilor de irigare, cu prezentarea explicită a ipotezelor, parametrilor și limitărilor modelului.
