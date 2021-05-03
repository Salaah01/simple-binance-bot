FROM ubuntu:20.04
ENV PYTHONUNBUFFERED=1

# Base installs
RUN apt update -y \
  && apt upgrade -y \
  && apt install -y python3.9 \
  && apt install -y python3.9-dev \
  && apt install -y libpq-dev \
  && rm -f /usr/bin/python3 \
  && ln -s python3.9 /usr/bin/python3 \
  && apt install -y python3-pip \
  && apt install -y wget

# Install TA-lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
  && tar -xzf ta-lib-0.4.0-src.tar.gz \
  && cd ta-lib/ \
  && ./configure --prefix=/usr \
  && make \
  && make install

RUN mkdir -p app

WORKDIR /app
COPY . .

RUN pip3 install -r requirements.txt
