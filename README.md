# Task Scheduler

Softapalikat:
- Backend = Python + FastAPI + OR-Tools optimoinnille
- Frontend = HTML + CSS + JavaScript + Bootstrap + Chart.js

## Yleiskuva

Tämä projekti koostuu backendistä ja frontendistä.

- Backend laskee optimoidun aikataulun käyttämällä Google OR-Tools CP-SAT -ratkaisijaa.
- Frontend näyttää tehtävät, koneet ja aikataulun selaimessa.

## Miten se toimii

1. Rakennetaan optimointimalli (decision variables).
2. Lisätään tuotannon rajoitteet (constraints).
3. Määritellään tavoitefunktio (minimize makespan).
4. Solver ratkaisee mallin.
5. Luetaan ratkaisu ja näytetään aikataulu käyttäjälle.

## Asennus ja ajaminen

1. Asenna riippuvuudet projektin juuressa:

```bash
python3 -m pip install -r requirements.txt
```

2. Käynnistä backend:

```bash
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

3. Avaa frontend staattisena palvelimena:

```bash
cd frontend
python3 -m http.server 8001
```

4. Avaa selainosoite:

```bash
http://127.0.0.1:8001/frontend/index.html
```

5. Frontendissä voit klikata `Generate Sample Data`, ladata oman JSON-tiedoston ja painaa `Optimize`.

## API

- `GET /tasks` palauttaa oletusesimerkit tehtävistä.
- `POST /optimize` laskee optimoidun aikataulun annetuille tehtäville.

## Huomioita

Priority-arvoja ei tässä aikataulutuksessa oteta vielä huomioon.
