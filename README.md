# m122-project

Smart Weather & Outfit Planner console app.

## Setup

```powershell
python -m pip install -r requirements.txt
```

Required environment variables:

```powershell
$env:OPENWEATHERMAP_API_KEY="your-openweathermap-key"
$env:GEMINI_API_KEY="your-gemini-key"
```

Optional environment variables:

```powershell
$env:GEMINI_MODEL="gemini-3.5-flash"
$env:WEATHER_UNITS="metric"
$env:REQUEST_TIMEOUT_SECONDS="10"
```

## Run

```powershell
python main.py
```

## Test

```powershell
python -m unittest discover -s tests
```
