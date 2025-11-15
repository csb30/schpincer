# 1. Használjunk egy karcsú, hivatalos Python alapképet
FROM python:3.10-slim-buster

ENV PYTHONUNBUFFERED=1

# 2. Beállítjuk a munkakönyvtárat a konténeren belül
WORKDIR /app

# 3. Másoljuk be a függőségek listáját
COPY requirements.txt .

# 4. Telepítsük a függőségeket
# A --no-cache-dir kisebb image-et eredményez
RUN pip install --no-cache-dir -r requirements.txt

# 5. Másoljuk be a projekt összes többi fájlját (amit a .dockerignore nem tilt)
COPY . .

# 6. Ez a parancs fog lefutni a konténer indításakor
CMD ["python", "monitor.py"]