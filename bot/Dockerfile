FROM ubuntu:20.04

# Base installs
RUN apt update -y \
  && apt upgrade -y \
  && apt install -y python3.9 \
  && apt install -y python3.9-dev \
  && apt install -y libpq-dev \
  && rm /usr/bin/python3 \
  && ln -s python3.9 /usr/bin/python3 \
  && apt install -y python3-pip

# Install TA-lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
  && tar -xzf ta-lib-0.4.0-src.tar.gz \
  && cd ta-lib/ \
  && ./configure --prefix=/usr \
  && make \
  && make install
