FROM alpine:3.5

ENV LANG en_US.utf8

# Install postgres, bash (required by multicorn) and su-exec (required by docker-entrypoint)
RUN apk add --no-cache --update bash su-exec postgresql postgresql-dev

RUN mkdir /docker-entrypoint-initdb.d
RUN mkdir -p /var/run/postgresql && chown -R postgres /var/run/postgresql
ENV PGDATA /var/lib/postgresql/data
VOLUME /var/lib/postgresql/data

COPY docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]

# Install python for pgxnclient and multicorn
RUN apk add --no-cache --update python3 python3-dev git build-base \
  # Install and upgrade Pip
  # make some useful symlinks that are expected to exist
  && if [[ ! -e /usr/bin/python ]];        then ln -sf /usr/bin/python3.5 /usr/bin/python; fi \
  && if [[ ! -e /usr/bin/python-config ]]; then ln -sf /usr/bin/python3.5-config /usr/bin/python-config; fi \
  && if [[ ! -e /usr/bin/idle ]];          then ln -sf /usr/bin/idle3.5 /usr/bin/idle; fi \
  && if [[ ! -e /usr/bin/pydoc ]];         then ln -sf /usr/bin/pydoc3.5 /usr/bin/pydoc; fi \
  && if [[ ! -e /usr/bin/easy_install ]];  then ln -sf /usr/bin/easy_install-3.5 /usr/bin/easy_install; fi \
  && easy_install pip \
  && pip install --upgrade pip

RUN pip install pgxnclient

# Compile from source to allow python 3.5
RUN git clone git://github.com/Kozea/Multicorn.git /tmp/Multicorn && \
  cd /tmp/Multicorn && \
  git checkout v1.3.3 && \
  # Allow python 3.5, which is stated as support but fails the check
  sed -i 's/2.6/3.5/g' /tmp/Multicorn/preflight-check.sh && \
  make && \
  make install

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

WORKDIR /app

COPY . /app

RUN python setup.py install

EXPOSE 5432
CMD ["postgres"]
