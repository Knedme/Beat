FROM python:3.12.7-bookworm
RUN apt-get update -qy
RUN apt-get install -qy ffmpeg
COPY . /beat
WORKDIR /beat
RUN pip install -r requirements.txt
CMD ["python3.12", "run.py"]