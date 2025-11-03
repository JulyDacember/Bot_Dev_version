FROM python:3.12
LABEL authors="SPb BEST - RuVl"

# Update packages
RUN apt-get update && apt-get upgrade -y

# For aiogram-dialog's picture of dialogs
RUN apt-get install -y graphviz

# Set enviroment variables
ENV TZ="Europe/Moscow"
ENV PIP_ROOT_USER_ACTION=ignore

# Prepare project directory
CMD mkdir -p /usr/src/app/
WORKDIR /usr/src/app/

# Copy and install requirements
COPY ./requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy project to directory
COPY . ./

# Sanitize possible encoding/line-ending issues in run.py to avoid null bytes
RUN python3 - << 'PY'
import pathlib
p = pathlib.Path('run.py')
data = p.read_bytes()
if b'\x00' in data:
    try:
        text = data.decode('utf-16')
    except Exception:
        text = data.decode('utf-8', errors='ignore')
else:
    try:
        text = data.decode('utf-8')
    except Exception:
        text = data.decode('latin-1')
text = text.replace('\r\n', '\n')
p.write_text(text, encoding='utf-8')
PY

# Run project
ENTRYPOINT ["python3", "run.py"]
